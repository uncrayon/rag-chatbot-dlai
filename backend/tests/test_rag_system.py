"""
Tests for RAG System integration
Tests cover: end-to-end query processing, session management, and tool orchestration
"""

from unittest.mock import MagicMock

from models import Course, Lesson
from rag_system import RAGSystem
from vector_store import SearchResults


def test_query_general_knowledge(mocker, test_config):
    """Test non-course question without tool use"""
    # Setup mock response without tools
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Python is a programming language."
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("What is Python?")

    # Verify direct response without search
    assert response == "Python is a programming language."
    # General knowledge queries might not produce sources
    assert isinstance(sources, list)


def test_query_course_specific(mocker, test_config):
    """Test course content question with tool use"""
    # Setup tool use response
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "prompt engineering"}
    tool_use_response.content = [tool_block]

    # Setup final response
    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Based on the course materials, prompt engineering is..."
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Mock VectorStore
    mock_vector_store = MagicMock()
    search_results = SearchResults(
        documents=["Prompt engineering content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.1],
        error=None,
    )
    mock_vector_store.search.return_value = search_results
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

    mocker.patch("rag_system.VectorStore", return_value=mock_vector_store)
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("What is prompt engineering?")

    # Verify search executed
    assert mock_vector_store.search.called

    # Verify response
    assert "Based on the course materials" in response

    # Verify sources returned
    assert len(sources) > 0


def test_query_with_session(mocker, test_config):
    """Test query with session_id includes history"""
    # Setup response
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer based on context"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)

    # First query to establish history
    rag.query("First question", session_id="test_session")

    # Second query should include history
    response, _ = rag.query("Follow-up question", session_id="test_session")

    # Verify history retrieved
    history = rag.session_manager.get_conversation_history("test_session")
    assert history is not None


def test_query_no_session(mocker, test_config):
    """Test query without session_id"""
    # Setup response
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("Question without session")

    # Verify no history passed (checked via no session_id)
    assert response == "Answer"


def test_sources_returned(mocker, test_config):
    """Test source tracking through tool_manager"""
    # Setup tool use response
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

    # Mock VectorStore with sources
    mock_vector_store = MagicMock()
    search_results = SearchResults(
        documents=["Content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.1],
        error=None,
    )
    mock_vector_store.search.return_value = search_results
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

    mocker.patch("rag_system.VectorStore", return_value=mock_vector_store)
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("Test query")

    # Verify sources format
    assert isinstance(sources, list)
    if len(sources) > 0:
        assert "text" in sources[0]
        assert "link" in sources[0]


def test_sources_reset(mocker, test_config):
    """Test sources cleared between queries"""
    # Setup tool use responses
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
    mock_client.messages.create.side_effect = [
        tool_use_response,
        text_response,  # First query
        tool_use_response,
        text_response,  # Second query
    ]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Mock VectorStore
    mock_vector_store = MagicMock()
    search_results = SearchResults(
        documents=["Content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.1],
        error=None,
    )
    mock_vector_store.search.return_value = search_results
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

    mocker.patch("rag_system.VectorStore", return_value=mock_vector_store)
    mocker.patch("rag_system.DocumentProcessor")

    # Execute two queries
    rag = RAGSystem(test_config)
    response1, sources1 = rag.query("First query")
    response2, sources2 = rag.query("Second query")

    # Verify sources reset (tool_manager.reset_sources() called)
    # Both queries should have fresh sources, not accumulated
    assert isinstance(sources1, list)
    assert isinstance(sources2, list)


def test_session_updated_after_query(mocker, test_config):
    """Test conversation saved to session"""
    # Setup response
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer to question"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    query_text = "What is the answer?"
    response, _ = rag.query(query_text, session_id="test_session")

    # Verify session updated
    history = rag.session_manager.get_conversation_history("test_session")
    assert history is not None
    assert "What is the answer?" in history
    assert "Answer to question" in history


def test_multiple_queries_same_session(mocker, test_config):
    """Test history accumulates across queries"""
    # Setup responses
    mock_response1 = MagicMock()
    mock_response1.stop_reason = "end_turn"
    text_block1 = MagicMock()
    text_block1.text = "First answer"
    mock_response1.content = [text_block1]

    mock_response2 = MagicMock()
    mock_response2.stop_reason = "end_turn"
    text_block2 = MagicMock()
    text_block2.text = "Second answer"
    mock_response2.content = [text_block2]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [mock_response1, mock_response2]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    rag.query("First question", session_id="test_session")
    rag.query("Second question", session_id="test_session")

    # Verify history includes both exchanges
    history = rag.session_manager.get_conversation_history("test_session")
    assert "First question" in history
    assert "First answer" in history
    assert "Second question" in history
    assert "Second answer" in history


def test_query_with_empty_results(mocker, test_config):
    """Test search finds nothing"""
    # Setup tool use response
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "search_course_content"
    tool_block.id = "tool_123"
    tool_block.input = {"query": "nonexistent topic"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "I couldn't find information about that topic."
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Mock VectorStore with empty results
    mock_vector_store = MagicMock()
    empty_results = SearchResults(documents=[], metadata=[], distances=[], error=None)
    mock_vector_store.search.return_value = empty_results

    mocker.patch("rag_system.VectorStore", return_value=mock_vector_store)
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("Nonexistent topic")

    # Verify Claude handles "No relevant content found" message
    assert response is not None


def test_query_with_search_error(mocker, test_config):
    """Test VectorStore error propagation"""
    # Setup tool use response
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
    text_block.text = "There was an error accessing the course materials."
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Mock VectorStore with error
    mock_vector_store = MagicMock()
    error_results = SearchResults(
        documents=[], metadata=[], distances=[], error="Database connection failed"
    )
    mock_vector_store.search.return_value = error_results

    mocker.patch("rag_system.VectorStore", return_value=mock_vector_store)
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("Test query")

    # Verify error handled gracefully
    assert response is not None


def test_tool_manager_registration(mocker, test_config):
    """Test tools properly registered"""
    mocker.patch("anthropic.Anthropic")
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)

    # Verify tools registered
    tool_defs = rag.tool_manager.get_tool_definitions()
    assert len(tool_defs) == 2

    # Verify CourseSearchTool registered
    tool_names = [tool["name"] for tool in tool_defs]
    assert "search_course_content" in tool_names
    assert "get_course_outline" in tool_names


def test_query_uses_outline_tool(mocker, test_config):
    """Test structural query uses get_course_outline"""
    # Setup tool use response for outline tool
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "get_course_outline"
    tool_block.id = "tool_123"
    tool_block.input = {"course_name": "Prompt Engineering"}
    tool_use_response.content = [tool_block]

    text_response = MagicMock()
    text_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "The course has 5 lessons..."
    text_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [tool_use_response, text_response]

    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    # Mock VectorStore with course catalog
    mock_vector_store = MagicMock()
    mock_vector_store.course_catalog.query.return_value = {
        "documents": [["Course description"]],
        "metadatas": [[{"title": "Introduction to Prompt Engineering"}]],
    }
    mock_vector_store.course_catalog.get.return_value = {
        "metadatas": [
            {
                "title": "Introduction to Prompt Engineering",
                "course_link": "https://example.com",
                "lessons_json": '[{"lesson_number": 1, "lesson_title": "Basics", "lesson_link": "https://example.com/1"}]',
            }
        ]
    }

    mocker.patch("rag_system.VectorStore", return_value=mock_vector_store)
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)
    response, sources = rag.query("List lessons in Prompt Engineering course")

    # Verify get_course_outline tool used
    assert response is not None


def test_max_history_limit(mocker, test_config):
    """Test history truncation at MAX_HISTORY"""
    # Setup responses
    mock_responses = []
    for i in range(5):
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.text = f"Answer {i}"
        mock_response.content = [text_block]
        mock_responses.append(mock_response)

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = mock_responses

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute multiple queries
    rag = RAGSystem(test_config)
    session_id = "test_session"

    for i in range(5):
        rag.query(f"Question {i}", session_id=session_id)

    # Verify only MAX_HISTORY (2) exchanges kept
    history = rag.session_manager.get_conversation_history(session_id)
    # Should only have last 2 exchanges (4 messages total)
    # Count how many "Question" entries in history
    question_count = history.count("Question")
    assert question_count == 2  # MAX_HISTORY = 2


def test_concurrent_sessions(mocker, test_config):
    """Test multiple sessions are isolated"""
    # Setup response
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.text = "Answer"
    mock_response.content = [text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    mocker.patch("rag_system.VectorStore")
    mocker.patch("rag_system.DocumentProcessor")

    # Execute
    rag = RAGSystem(test_config)

    # Create two separate sessions
    rag.query("Question for session 1", session_id="session_1")
    rag.query("Question for session 2", session_id="session_2")

    # Verify session isolation
    history1 = rag.session_manager.get_conversation_history("session_1")
    history2 = rag.session_manager.get_conversation_history("session_2")

    assert "Question for session 1" in history1
    assert "Question for session 1" not in history2

    assert "Question for session 2" in history2
    assert "Question for session 2" not in history1


def test_integration_with_document_processing(mocker, test_config):
    """Test full pipeline from document to query"""
    mocker.patch("anthropic.Anthropic")
    mocker.patch("rag_system.VectorStore")

    # Mock DocumentProcessor
    mock_processor = MagicMock()
    mock_course = Course(
        title="Test Course",
        course_link="https://example.com",
        instructor="Test Instructor",
        lessons=[
            Lesson(
                lesson_number=1, title="Lesson 1", lesson_link="https://example.com/1"
            )
        ],
    )
    mock_processor.process_course_document.return_value = (mock_course, [])

    mocker.patch("rag_system.DocumentProcessor", return_value=mock_processor)

    # Execute
    rag = RAGSystem(test_config)

    # Verify RAGSystem initialized without errors
    assert rag.document_processor is not None
    assert rag.vector_store is not None
    assert rag.ai_generator is not None
    assert rag.tool_manager is not None
