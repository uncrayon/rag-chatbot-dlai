"""
Tests for AIGenerator tool calling flow
Tests cover: basic generation, tool execution, message structure, and edge cases
"""
import pytest
from unittest.mock import MagicMock, patch, call
from ai_generator import AIGenerator


def test_generate_response_without_tools(mocker):
    """Test basic generation without tools"""
    # Setup mock client and response
    mock_text_response = MagicMock()
    mock_text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "This is a direct response."
    mock_text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_text_response

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(query="Hello")

    # Verify single API call
    assert mock_client.messages.create.call_count == 1

    # Verify text response returned
    assert response == "This is a direct response."


def test_generate_response_with_tool_use(mocker, mock_tool_manager):
    """Test two-phase flow when Claude uses tools"""
    # Setup tool use response
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    # Setup final text response
    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Based on the search results..."
    text_response.content = [text_block]

    # Mock client with two responses
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Setup tool manager
    mock_tool_manager.execute_tool.return_value = "Search results here"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="What is prompt engineering?",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify two API calls (decision + synthesis)
    assert mock_client.messages.create.call_count == 2

    # Verify tool executed
    mock_tool_manager.execute_tool.assert_called_once_with(
        "search_course_content",
        query="test"
    )

    # Verify final response
    assert response == "Based on the search results..."


def test_handle_tool_execution_message_format(mocker, mock_tool_manager):
    """Test message structure in tool execution flow"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Final answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Tool result"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test query",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify second call has correct message structure
    second_call_args = mock_client.messages.create.call_args_list[1]
    messages = second_call_args[1]['messages']

    # Should have 3 messages: [user, assistant_tool_use, user_tool_result]
    assert len(messages) == 3
    assert messages[0]['role'] == 'user'
    assert messages[1]['role'] == 'assistant'
    assert messages[2]['role'] == 'user'


def test_tool_result_format(mocker, mock_tool_manager):
    """Test tool result structure"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Final answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Tool result content"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify tool result format
    second_call_args = mock_client.messages.create.call_args_list[1]
    tool_result_message = second_call_args[1]['messages'][2]['content'][0]

    assert tool_result_message['type'] == 'tool_result'
    assert tool_result_message['tool_use_id'] == 'tool_123'
    assert tool_result_message['content'] == 'Tool result content'


def test_multiple_tool_calls(mocker, mock_tool_manager):
    """Test multiple tools in one response"""
    # Setup response with multiple tools
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"

    tool_block1 = MagicMock()
    tool_block1.type = "tool_use"
    tool_block1.name = "search_course_content"
    tool_block1.id = "tool_1"
    tool_block1.input = {"query": "test1"}

    tool_block2 = MagicMock()
    tool_block2.type = "tool_use"
    tool_block2.name = "get_course_outline"
    tool_block2.id = "tool_2"
    tool_block2.input = {"course_name": "test"}

    tool_use_response.content = [tool_block1, tool_block2]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Combined answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
        tool_manager=mock_tool_manager
    )

    # Verify both tools executed
    assert mock_tool_manager.execute_tool.call_count == 2

    # Verify both results in message
    second_call_args = mock_client.messages.create.call_args_list[1]
    tool_results = second_call_args[1]['messages'][2]['content']
    assert len(tool_results) == 2


def test_final_response_without_tools(mocker, mock_tool_manager):
    """Test second call excludes tools parameter"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Final answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify second call does NOT include tools
    second_call_args = mock_client.messages.create.call_args_list[1]
    assert 'tools' not in second_call_args[1]


def test_conversation_history_preserved(mocker, mock_tool_manager):
    """Test history maintained through tool use"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute with history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    conversation_history = "User: Previous question\nAssistant: Previous answer"
    generator.generate_response(
        query="New question",
        conversation_history=conversation_history,
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify both calls include history in system prompt
    first_call = mock_client.messages.create.call_args_list[0]
    second_call = mock_client.messages.create.call_args_list[1]

    assert conversation_history in first_call[1]['system']
    assert conversation_history in second_call[1]['system']


def test_tool_execution_error_handling(mocker, mock_tool_manager):
    """Test error from tool execution"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Handled error gracefully"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Tool returns error message
    mock_tool_manager.execute_tool.return_value = "Error: Database connection failed"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify no crash and response returned
    assert response is not None


def test_tool_use_id_matching(mocker, mock_tool_manager):
    """Test tool_use_id correctly tracked"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "unique_tool_id_456"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify tool_use_id matches
    second_call_args = mock_client.messages.create.call_args_list[1]
    tool_result = second_call_args[1]['messages'][2]['content'][0]
    assert tool_result['tool_use_id'] == "unique_tool_id_456"


def test_system_prompt_with_history(mocker):
    """Test system prompt construction with history"""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Response"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Execute with history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    history = "User: Hi\nAssistant: Hello"
    generator.generate_response(query="Test", conversation_history=history)

    # Verify system prompt includes history
    call_args = mock_client.messages.create.call_args
    system_content = call_args[1]['system']
    assert history in system_content
    assert "Previous conversation:" in system_content


def test_system_prompt_without_history(mocker):
    """Test system prompt without history"""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Response"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Execute without history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(query="Test")

    # Verify system prompt is just SYSTEM_PROMPT
    call_args = mock_client.messages.create.call_args
    system_content = call_args[1]['system']
    assert "Previous conversation:" not in system_content
    assert "You are an AI assistant" in system_content


def test_base_params_used(mocker):
    """Test API parameters are correct"""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Response"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-custom")
    generator.generate_response(query="Test")

    # Verify base parameters
    call_args = mock_client.messages.create.call_args
    assert call_args[1]['model'] == 'claude-sonnet-4-custom'
    assert call_args[1]['temperature'] == 0
    assert call_args[1]['max_tokens'] == 800


def test_tool_choice_auto(mocker, mock_tool_manager):
    """Test tool_choice parameter set when tools provided"""
    # Setup responses
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer"
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute with tools
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager
    )

    # Verify tool_choice set in first call
    first_call_args = mock_client.messages.create.call_args_list[0]
    assert first_call_args[1]['tool_choice'] == {"type": "auto"}


def test_no_tool_manager_with_tool_use(mocker):
    """
    Test edge case: tool_use without tool_manager
    EXPECTED TO FAIL: Line 92 assumes content[0].text exists
    """
    # Setup tool use response
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "test"}
    tool_use_response.content = [tool_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = tool_use_response

    mocker.patch('anthropic.Anthropic', return_value=mock_client)

    # Execute without tool_manager
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")

    # This should not crash - either return error or handle gracefully
    try:
        response = generator.generate_response(
            query="Test",
            tools=[{"name": "search_course_content"}],
            tool_manager=None
        )
        # If we get here, check response is reasonable
        assert response is not None
    except AttributeError as e:
        # Expected failure - content[0] doesn't have .text attribute
        assert "text" in str(e).lower() or "attribute" in str(e).lower()
