from unittest.mock import patch

from databricks_ai_bridge.genie import GenieResult
from langchain_core.messages import AIMessage

from databricks_langchain.genie import (
    GenieAgent,
    GenieTool,
    GenieToolInput,
    _concat_messages_array,
    _query_genie_as_agent,
)


def test_concat_messages_array():
    # Test a simple case with multiple messages
    messages = [
        {"role": "user", "content": "What is the weather?"},
        {"role": "assistant", "content": "It is sunny."},
    ]
    result = _concat_messages_array(messages)
    expected = "user: What is the weather?\nassistant: It is sunny."
    assert result == expected

    # Test case with missing content
    messages = [{"role": "user"}, {"role": "assistant", "content": "I don't know."}]
    result = _concat_messages_array(messages)
    expected = "user: \nassistant: I don't know."
    assert result == expected

    # Test case with non-dict message objects
    class Message:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    messages = [
        Message("user", "Tell me a joke."),
        Message("assistant", "Why did the chicken cross the road?"),
    ]
    result = _concat_messages_array(messages)
    expected = "user: Tell me a joke.\nassistant: Why did the chicken cross the road?"
    assert result == expected


@patch("databricks_langchain.genie.Genie")
def test_query_genie_as_agent(MockGenie):
    # Mock the Genie class and its response
    mock_genie = MockGenie.return_value
    mock_genie.ask_question.return_value = "It is sunny."

    input_data = {"messages": [{"role": "user", "content": "What is the weather?"}]}
    result = _query_genie_as_agent(input_data, "space-id", "Genie")

    expected_message = {"messages": [AIMessage(content="It is sunny.")]}
    assert result == expected_message

    # Test the case when genie_response is empty
    mock_genie.ask_question.return_value = None
    result = _query_genie_as_agent(input_data, "space-id", "Genie")

    expected_message = {"messages": [AIMessage(content="")]}
    assert result == expected_message


@patch("langchain_core.runnables.RunnableLambda")
def test_create_genie_agent(MockRunnableLambda):
    mock_runnable = MockRunnableLambda.return_value

    agent = GenieAgent("space-id", "Genie")
    assert agent == mock_runnable

    # Check that the partial function is created with the correct arguments
    MockRunnableLambda.assert_called()


@patch("databricks_langchain.genie.Genie")
def test_create_genie_tool(MockGenie):
    mock_genie = MockGenie.return_value
    mock_genie.ask_question_with_details.return_value = GenieResult(
        description=None, sql_query=None, response="It is sunny."
    )

    agent = GenieTool("space-id", "Genie", "Description")

    assert agent.name == "Genie"
    assert agent.args_schema == GenieToolInput
    assert agent.description == "Description"
    assert (
        agent.invoke({"question": "What is the weather?", "summarized_chat_history": "No history"})
        == "It is sunny."
    )

    assert mock_genie.ask_question_with_details.call_count == 1


@patch("databricks_langchain.genie.Genie")
def test_create_genie_tool_no_response(MockGenie):
    mock_genie = MockGenie.return_value
    mock_genie.ask_question_with_details.return_value = None

    agent = GenieTool("space-id", "Genie", "Description")

    assert agent.name == "Genie"
    assert agent.args_schema == GenieToolInput
    assert agent.description == "Description"
    assert (
        agent.invoke({"question": "What is the weather?", "summarized_chat_history": "No history"})
        == ""
    )

    assert mock_genie.ask_question_with_details.call_count == 1
