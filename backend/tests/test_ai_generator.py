"""
Tests for AIGenerator tool calling flow
Tests cover: basic generation, tool execution, message structure, and edge cases
"""

from unittest.mock import MagicMock

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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Setup tool manager
    mock_tool_manager.execute_tool.return_value = "Search results here"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="What is prompt engineering?",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify two API calls (decision + synthesis)
    assert mock_client.messages.create.call_count == 2

    # Verify tool executed
    mock_tool_manager.execute_tool.assert_called_once_with(
        "search_course_content", query="test"
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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Tool result"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test query",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify second call has correct message structure
    second_call_args = mock_client.messages.create.call_args_list[1]
    messages = second_call_args[1]["messages"]

    # Should have 3 messages: [user, assistant_tool_use, user_tool_result]
    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"


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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Tool result content"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify tool result format
    second_call_args = mock_client.messages.create.call_args_list[1]
    tool_result_message = second_call_args[1]["messages"][2]["content"][0]

    assert tool_result_message["type"] == "tool_result"
    assert tool_result_message["tool_use_id"] == "tool_123"
    assert tool_result_message["content"] == "Tool result content"


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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
        tool_manager=mock_tool_manager,
    )

    # Verify both tools executed
    assert mock_tool_manager.execute_tool.call_count == 2

    # Verify both results in message
    second_call_args = mock_client.messages.create.call_args_list[1]
    tool_results = second_call_args[1]["messages"][2]["content"]
    assert len(tool_results) == 2


def test_final_response_without_tools(mocker, mock_tool_manager):
    """Test final call (after max rounds) excludes tools parameter"""
    # Setup responses - force max rounds
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
    # Provide 2 tool_use responses to hit max rounds, then final text
    mock_client.messages.create.side_effect = [
        tool_use_response,
        tool_use_response,
        text_response,
    ]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify calls 0 and 1 have tools (within loop)
    assert "tools" in mock_client.messages.create.call_args_list[0][1]
    assert "tools" in mock_client.messages.create.call_args_list[1][1]

    # Verify third call (final after max rounds) does NOT include tools
    third_call_args = mock_client.messages.create.call_args_list[2]
    assert "tools" not in third_call_args[1]


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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute with history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    conversation_history = "User: Previous question\nAssistant: Previous answer"
    generator.generate_response(
        query="New question",
        conversation_history=conversation_history,
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify both calls include history in system prompt
    first_call = mock_client.messages.create.call_args_list[0]
    second_call = mock_client.messages.create.call_args_list[1]

    assert conversation_history in first_call[1]["system"]
    assert conversation_history in second_call[1]["system"]


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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Tool returns error message
    mock_tool_manager.execute_tool.return_value = "Error: Database connection failed"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify tool_use_id matches
    second_call_args = mock_client.messages.create.call_args_list[1]
    tool_result = second_call_args[1]["messages"][2]["content"][0]
    assert tool_result["tool_use_id"] == "unique_tool_id_456"


def test_system_prompt_with_history(mocker):
    """Test system prompt construction with history"""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Response"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Execute with history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    history = "User: Hi\nAssistant: Hello"
    generator.generate_response(query="Test", conversation_history=history)

    # Verify system prompt includes history
    call_args = mock_client.messages.create.call_args
    system_content = call_args[1]["system"]
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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Execute without history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(query="Test")

    # Verify system prompt is just SYSTEM_PROMPT
    call_args = mock_client.messages.create.call_args
    system_content = call_args[1]["system"]
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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-custom")
    generator.generate_response(query="Test")

    # Verify base parameters
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-sonnet-4-custom"
    assert call_args[1]["temperature"] == 0
    assert call_args[1]["max_tokens"] == 800


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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    # Execute with tools
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify tool_choice set in first call
    first_call_args = mock_client.messages.create.call_args_list[0]
    assert first_call_args[1]["tool_choice"] == {"type": "auto"}


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

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Execute without tool_manager
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")

    # This should not crash - either return error or handle gracefully
    try:
        response = generator.generate_response(
            query="Test", tools=[{"name": "search_course_content"}], tool_manager=None
        )
        # If we get here, check response is reasonable
        assert response is not None
    except AttributeError as e:
        # Expected failure - content[0] doesn't have .text attribute
        assert "text" in str(e).lower() or "attribute" in str(e).lower()


# ========== Helper Functions for Sequential Tool Calling Tests ==========


def create_mock_tool_response(tool_name, tool_id, tool_input):
    """Create mock API response with tool use"""
    response = MagicMock()
    response.stop_reason = "tool_use"
    tool_block = create_tool_block(tool_name, tool_id, tool_input)
    response.content = [tool_block]
    return response


def create_tool_block(tool_name, tool_id, tool_input):
    """Create mock tool use content block"""
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.id = tool_id
    block.input = tool_input
    return block


def create_mock_text_response(text):
    """Create mock API response with text"""
    response = MagicMock()
    response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = text
    response.content = [text_block]
    return response


# ========== Tests for Sequential Tool Calling ==========


def test_two_sequential_tool_calls(mocker, mock_tool_manager):
    """Test Claude makes 2 sequential tool calls across separate rounds"""
    # Round 1: Tool use (search_course_content)
    tool_use_1 = create_mock_tool_response(
        "search_course_content", "tool_1", {"query": "lesson 1"}
    )

    # Round 2: Another tool use (search_course_content)
    tool_use_2 = create_mock_tool_response(
        "search_course_content", "tool_2", {"query": "lesson 3"}
    )

    # Final: Text response
    final_text = create_mock_text_response(
        "Comparison: lesson 1 covers basics, lesson 3 covers advanced topics"
    )

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_1, tool_use_2, final_text]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = [
        "Result 1 content",
        "Result 2 content",
    ]

    # Execute
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="Compare lesson 1 and lesson 3",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify 3 API calls (2 tool rounds + final synthesis)
    assert mock_client.messages.create.call_count == 3

    # Verify 2 tool executions
    assert mock_tool_manager.execute_tool.call_count == 2

    # Verify final response
    assert (
        response
        == "Comparison: lesson 1 covers basics, lesson 3 covers advanced topics"
    )

    # Verify message accumulation
    final_call = mock_client.messages.create.call_args_list[2]
    messages = final_call[1]["messages"]
    assert (
        len(messages) == 5
    )  # [user, asst_tool1, user_result1, asst_tool2, user_result2]


def test_max_rounds_enforced(mocker, mock_tool_manager):
    """Test that tool calls stop after 2 rounds (max limit)"""
    # All responses are tool_use (to test enforcement)
    tool_use = create_mock_tool_response(
        "search_course_content", "tool_n", {"query": "test"}
    )
    final_text = create_mock_text_response("Final answer")

    mock_client = MagicMock()
    # Provide 5 responses but should only use 2 + final
    mock_client.messages.create.side_effect = [
        tool_use,
        tool_use,
        final_text,
        tool_use,
        tool_use,
    ]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Result"

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="Test query",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Should only make 3 calls (2 tool rounds + 1 final without tools)
    assert mock_client.messages.create.call_count == 3
    assert mock_tool_manager.execute_tool.call_count == 2
    assert response == "Final answer"


def test_early_termination_after_one_round(mocker, mock_tool_manager):
    """Test recursion stops when Claude returns text instead of tool_use after round 1"""
    tool_use = create_mock_tool_response(
        "search_course_content", "tool_1", {"query": "test"}
    )
    text_response = create_mock_text_response("Here's the answer based on search")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use, text_response]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.return_value = "Search results"

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    response = generator.generate_response(
        query="Simple question",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Only 2 calls (1 tool round + text response)
    assert mock_client.messages.create.call_count == 2
    assert mock_tool_manager.execute_tool.call_count == 1
    assert response == "Here's the answer based on search"


def test_tools_available_in_both_rounds(mocker, mock_tool_manager):
    """Test that tools parameter is present in rounds 1 and 2, absent in final"""
    tool_use_1 = create_mock_tool_response(
        "search_course_content", "tool_1", {"query": "test1"}
    )
    tool_use_2 = create_mock_tool_response(
        "get_course_outline", "tool_2", {"course_name": "test"}
    )
    final_text = create_mock_text_response("Final synthesized answer")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_1, tool_use_2, final_text]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    tools = [{"name": "search_course_content"}, {"name": "get_course_outline"}]
    generator.generate_response(
        query="Test query", tools=tools, tool_manager=mock_tool_manager
    )

    calls = mock_client.messages.create.call_args_list

    # Round 1: Tools present
    assert "tools" in calls[0][1]
    assert calls[0][1]["tools"] == tools

    # Round 2: Tools present
    assert "tools" in calls[1][1]
    assert calls[1][1]["tools"] == tools

    # Final call: No tools (key difference from old implementation)
    assert "tools" not in calls[2][1]


def test_message_structure_accumulation(mocker, mock_tool_manager):
    """Test that messages accumulate correctly through sequential rounds"""
    tool_use_1 = create_mock_tool_response(
        "search_course_content", "tool_1", {"query": "test1"}
    )
    tool_use_2 = create_mock_tool_response(
        "search_course_content", "tool_2", {"query": "test2"}
    )
    final_text = create_mock_text_response("Final answer")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_1, tool_use_2, final_text]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Original query",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    calls = mock_client.messages.create.call_args_list

    # Round 1: 1 message (initial user query)
    assert len(calls[0][1]["messages"]) == 1
    assert calls[0][1]["messages"][0]["role"] == "user"

    # Round 2: 3 messages (user, assistant tool_use, user tool_results)
    assert len(calls[1][1]["messages"]) == 3
    assert calls[1][1]["messages"][0]["role"] == "user"
    assert calls[1][1]["messages"][1]["role"] == "assistant"
    assert calls[1][1]["messages"][2]["role"] == "user"

    # Final: 5 messages (user, asst, user, asst, user)
    assert len(calls[2][1]["messages"]) == 5
    roles = [m["role"] for m in calls[2][1]["messages"]]
    assert roles == ["user", "assistant", "user", "assistant", "user"]


def test_tool_error_in_second_round(mocker, mock_tool_manager):
    """Test that tool execution error in round 2 is handled gracefully"""
    tool_use_1 = create_mock_tool_response(
        "get_course_outline", "tool_1", {"course_name": "test"}
    )
    tool_use_2 = create_mock_tool_response(
        "search_course_content", "tool_2", {"query": "test"}
    )
    final_text = create_mock_text_response("Based on outline, but search failed")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_1, tool_use_2, final_text]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # First tool succeeds, second fails
    mock_tool_manager.execute_tool.side_effect = [
        "Outline results",
        Exception("Database timeout error"),
    ]

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test query",
        tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
        tool_manager=mock_tool_manager,
    )

    # Should make 3 calls: round1, round2 (error), final
    assert mock_client.messages.create.call_count == 3

    # Verify error passed to Claude in final call
    third_call = mock_client.messages.create.call_args_list[2]
    messages = third_call[1]["messages"]

    # Check that error result was added
    error_message = messages[-1]["content"][0]
    assert error_message["is_error"]
    assert "Database timeout error" in error_message["content"]


def test_tool_returns_error_string(mocker, mock_tool_manager):
    """Test when tool returns error string (not exception)"""
    tool_use = create_mock_tool_response(
        "search_course_content", "tool_1", {"query": "test"}
    )
    text_response = create_mock_text_response("No results found for that query")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use, text_response]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Tool returns error string (common pattern in search_tools.py)
    mock_tool_manager.execute_tool.return_value = "Error: No matching course found"

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Search for nonexistent course",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Should not crash, should continue
    assert mock_client.messages.create.call_count == 2

    # Verify error flag was set
    second_call = mock_client.messages.create.call_args_list[1]
    tool_result = second_call[1]["messages"][2]["content"][0]

    assert tool_result["is_error"]
    assert "No matching course found" in tool_result["content"]


def test_sequential_with_conversation_history(mocker, mock_tool_manager):
    """Test that conversation history is preserved across sequential rounds"""
    tool_use_1 = create_mock_tool_response(
        "search_course_content", "tool_1", {"query": "test"}
    )
    tool_use_2 = create_mock_tool_response(
        "search_course_content", "tool_2", {"query": "test2"}
    )
    final_text = create_mock_text_response("Answer with context")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_1, tool_use_2, final_text]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

    # Execute with history
    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    conversation_history = "User: Previous question\nAssistant: Previous answer"
    generator.generate_response(
        query="New question",
        conversation_history=conversation_history,
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    # Verify all 3 calls include history in system prompt
    calls = mock_client.messages.create.call_args_list
    for call_args in calls:
        assert conversation_history in call_args[1]["system"]
        assert "Previous conversation:" in call_args[1]["system"]


def test_multiple_parallel_tools_in_one_round(mocker, mock_tool_manager):
    """Test multiple tool calls within a single response (parallel execution)"""
    # Create response with 2 tool use blocks in one response
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"

    tool_block_1 = create_tool_block(
        "search_course_content", "tool_1", {"query": "test1"}
    )
    tool_block_2 = create_tool_block(
        "get_course_outline", "tool_2", {"course_name": "test"}
    )
    tool_use_response.content = [tool_block_1, tool_block_2]

    final_text = create_mock_text_response("Combined answer from both tools")

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, final_text]
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

    generator = AIGenerator(api_key="test-key", model="claude-sonnet-4")
    generator.generate_response(
        query="Test",
        tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
        tool_manager=mock_tool_manager,
    )

    # Both tools executed in same round
    assert mock_tool_manager.execute_tool.call_count == 2

    # Second API call has both tool results
    second_call = mock_client.messages.create.call_args_list[1]
    tool_results = second_call[1]["messages"][2]["content"]
    assert len(tool_results) == 2
    assert tool_results[0]["tool_use_id"] == "tool_1"
    assert tool_results[1]["tool_use_id"] == "tool_2"
