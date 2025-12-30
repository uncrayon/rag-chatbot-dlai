import os
import sys
from unittest.mock import MagicMock

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from models import Course, CourseChunk, Lesson
from vector_store import SearchResults


@pytest.fixture
def test_config():
    """Provide test configuration"""
    config = Config()
    config.ANTHROPIC_API_KEY = "test-api-key"
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    return config


@pytest.fixture
def sample_course():
    """Sample course with lessons"""
    return Course(
        title="Introduction to Prompt Engineering",
        course_link="https://example.com/prompt-engineering",
        instructor="Claude AI",
        lessons=[
            Lesson(
                lesson_number=1,
                title="Basics",
                lesson_link="https://example.com/lesson1",
            ),
            Lesson(
                lesson_number=2,
                title="Advanced Techniques",
                lesson_link="https://example.com/lesson2",
            ),
        ],
    )


@pytest.fixture
def sample_course_chunks(sample_course):
    """Sample course chunks for testing"""
    return [
        CourseChunk(
            content="Lesson 1 content: Prompt engineering is the art of crafting effective prompts.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=0,
        ),
        CourseChunk(
            content="Advanced techniques include chain of thought reasoning.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=1,
        ),
    ]


@pytest.fixture
def sample_search_results():
    """Sample search results from vector store"""
    return SearchResults(
        documents=[
            "Lesson 1 content: Prompt engineering is the art of crafting effective prompts.",
            "Advanced techniques include chain of thought reasoning.",
        ],
        metadata=[
            {
                "course_title": "Introduction to Prompt Engineering",
                "lesson_number": 1,
                "chunk_index": 0,
            },
            {
                "course_title": "Introduction to Prompt Engineering",
                "lesson_number": 2,
                "chunk_index": 1,
            },
        ],
        distances=[0.1, 0.2],
        error=None,
    )


@pytest.fixture
def empty_search_results():
    """Empty search results"""
    return SearchResults(documents=[], metadata=[], distances=[], error=None)


@pytest.fixture
def error_search_results():
    """Search results with error"""
    return SearchResults(
        documents=[], metadata=[], distances=[], error="Database connection failed"
    )


@pytest.fixture
def mock_vector_store(sample_search_results):
    """Mock VectorStore with configurable behavior"""
    mock = MagicMock()
    mock.search.return_value = sample_search_results
    mock.get_lesson_link.return_value = "https://example.com/lesson1"
    mock.get_course_count.return_value = 5
    mock.get_existing_course_titles.return_value = [
        "Introduction to Prompt Engineering"
    ]
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for API calls"""
    return MagicMock()


@pytest.fixture
def mock_tool_use_response():
    """Mock response from Anthropic with tool use"""
    mock = MagicMock()
    mock.stop_reason = "tool_use"

    # Create mock tool use content block
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = "search_course_content"
    tool_use_block.id = "toolu_123456"
    tool_use_block.input = {
        "query": "What is prompt engineering?",
        "course_name": None,
        "lesson_number": None,
    }

    mock.content = [tool_use_block]
    return mock


@pytest.fixture
def mock_text_response():
    """Mock text-only response from Anthropic"""
    mock = MagicMock()
    mock.stop_reason = "end_turn"

    # Create mock text content block
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = (
        "Prompt engineering is the art of crafting effective prompts for AI systems."
    )

    mock.content = [text_block]
    return mock


@pytest.fixture
def mock_session_manager():
    """Mock SessionManager"""
    mock = MagicMock()
    mock.get_conversation_history.return_value = None
    mock.add_exchange.return_value = None
    mock.create_session.return_value = "test_session_123"
    return mock


@pytest.fixture
def mock_tool_manager():
    """Mock ToolManager"""
    mock = MagicMock()
    mock.execute_tool.return_value = "Search results here"
    mock.get_last_sources.return_value = []
    mock.get_tool_definitions.return_value = [
        {"name": "search_course_content", "description": "Search course content"},
        {"name": "get_course_outline", "description": "Get course outline"},
    ]
    return mock
