"""
Tests for CourseSearchTool.execute() method
Tests cover: basic search, filters, error handling, formatting, and source tracking
"""

from search_tools import CourseSearchTool
from vector_store import SearchResults


def test_execute_basic_query(mock_vector_store, sample_search_results):
    """Test basic search execution with no filters"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results

    # Execute
    result = tool.execute(query="What is prompt engineering?")

    # Verify VectorStore.search called correctly
    mock_vector_store.search.assert_called_once_with(
        query="What is prompt engineering?", course_name=None, lesson_number=None
    )

    # Verify result format
    assert "[Introduction to Prompt Engineering - Lesson 1]" in result
    assert "Prompt engineering is the art" in result

    # Verify sources tracked
    assert len(tool.last_sources) == 2
    assert (
        tool.last_sources[0]["text"] == "Introduction to Prompt Engineering - Lesson 1"
    )


def test_execute_with_course_name_filter(mock_vector_store, sample_search_results):
    """Test query with course_name parameter"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results

    # Execute
    result = tool.execute(
        query="What is prompt engineering?",
        course_name="Introduction to Prompt Engineering",
    )

    # Verify course_name passed to search
    mock_vector_store.search.assert_called_once_with(
        query="What is prompt engineering?",
        course_name="Introduction to Prompt Engineering",
        lesson_number=None,
    )

    # Verify results returned
    assert "Prompt engineering" in result


def test_execute_with_lesson_number_filter(mock_vector_store, sample_search_results):
    """Test query with lesson_number parameter"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results

    # Execute
    result = tool.execute(query="What is prompt engineering?", lesson_number=1)

    # Verify lesson_number passed to search
    mock_vector_store.search.assert_called_once_with(
        query="What is prompt engineering?", course_name=None, lesson_number=1
    )

    # Verify results returned
    assert "Lesson 1" in result


def test_execute_with_combined_filters(mock_vector_store, sample_search_results):
    """Test query with both course_name and lesson_number"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results

    # Execute
    result = tool.execute(
        query="What is prompt engineering?",
        course_name="Introduction to Prompt Engineering",
        lesson_number=1,
    )

    # Verify both filters applied
    mock_vector_store.search.assert_called_once_with(
        query="What is prompt engineering?",
        course_name="Introduction to Prompt Engineering",
        lesson_number=1,
    )

    # Verify results returned
    assert "Introduction to Prompt Engineering" in result


def test_execute_empty_results(mock_vector_store, empty_search_results):
    """Test handling of no matches found"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = empty_search_results

    # Execute
    result = tool.execute(query="nonexistent topic")

    # Verify message
    assert "No relevant content found" in result

    # Verify last_sources updated (should be empty list based on _format_results)
    # Note: execute() doesn't explicitly clear sources on empty, but _format_results won't populate them
    assert len(tool.last_sources) == 0


def test_execute_empty_results_with_filters(mock_vector_store, empty_search_results):
    """Test empty results message includes filter context"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = empty_search_results

    # Execute with course filter
    result1 = tool.execute(query="nonexistent", course_name="Some Course")
    assert "No relevant content found in course 'Some Course'" in result1

    # Execute with lesson filter
    result2 = tool.execute(query="nonexistent", lesson_number=5)
    assert "No relevant content found in lesson 5" in result2

    # Execute with both filters
    result3 = tool.execute(
        query="nonexistent", course_name="Some Course", lesson_number=5
    )
    assert "No relevant content found in course 'Some Course' in lesson 5" in result3


def test_execute_error_from_vector_store(mock_vector_store, error_search_results):
    """Test error propagation from VectorStore"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = error_search_results

    # Execute
    result = tool.execute(query="any query")

    # Verify error message propagated
    assert "Database connection failed" in result


def test_format_results_with_lessons(mock_vector_store, sample_search_results):
    """Test formatting with lesson metadata"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results

    # Execute
    result = tool.execute(query="test")

    # Verify header format
    assert "[Introduction to Prompt Engineering - Lesson 1]" in result
    assert "[Introduction to Prompt Engineering - Lesson 2]" in result

    # Verify content follows header
    lines = result.split("\n")
    # Find the header line and verify content is on next line
    for i, line in enumerate(lines):
        if "[Introduction to Prompt Engineering - Lesson 1]" in line:
            assert "Prompt engineering is the art" in lines[i + 1]


def test_format_results_with_links(mock_vector_store, sample_search_results):
    """Test results with lesson links"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

    # Execute
    tool.execute(query="test")

    # Verify get_lesson_link called for lessons
    assert mock_vector_store.get_lesson_link.called

    # Verify sources contain links
    assert len(tool.last_sources) == 2
    assert tool.last_sources[0]["link"] == "https://example.com/lesson1"


def test_last_sources_tracking(mock_vector_store, sample_search_results):
    """Test source tracking mechanism"""
    # Setup
    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = sample_search_results

    # Execute
    tool.execute(query="test")

    # Verify last_sources updated
    assert len(tool.last_sources) == 2

    # Verify source structure
    assert "text" in tool.last_sources[0]
    assert "link" in tool.last_sources[0]

    # Verify source content
    assert (
        tool.last_sources[0]["text"] == "Introduction to Prompt Engineering - Lesson 1"
    )
    assert (
        tool.last_sources[1]["text"] == "Introduction to Prompt Engineering - Lesson 2"
    )


def test_multiple_documents_formatting(mock_vector_store):
    """Test multiple search results formatting"""
    # Setup - create multi-doc results
    multi_results = SearchResults(
        documents=[
            "First document content.",
            "Second document content.",
            "Third document content.",
        ],
        metadata=[
            {"course_title": "Course A", "lesson_number": 1},
            {"course_title": "Course B", "lesson_number": 2},
            {"course_title": "Course C", "lesson_number": 3},
        ],
        distances=[0.1, 0.2, 0.3],
        error=None,
    )

    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = multi_results

    # Execute
    result = tool.execute(query="test")

    # Verify documents separated by "\n\n"
    assert "\n\n" in result

    # Verify all documents have headers
    assert "[Course A - Lesson 1]" in result
    assert "[Course B - Lesson 2]" in result
    assert "[Course C - Lesson 3]" in result

    # Verify all content included
    assert "First document content" in result
    assert "Second document content" in result
    assert "Third document content" in result


def test_metadata_missing_fields(mock_vector_store):
    """Test handling of incomplete metadata"""
    # Setup - results with missing metadata
    incomplete_results = SearchResults(
        documents=["Some content"],
        metadata=[
            {}  # Missing course_title and lesson_number
        ],
        distances=[0.1],
        error=None,
    )

    tool = CourseSearchTool(mock_vector_store)
    mock_vector_store.search.return_value = incomplete_results

    # Execute
    result = tool.execute(query="test")

    # Verify defaults to 'unknown' for missing course_title
    assert "[unknown]" in result

    # Verify content still included
    assert "Some content" in result

    # Verify no crash
    assert result is not None
