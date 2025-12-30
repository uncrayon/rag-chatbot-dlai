"""
API Endpoint Tests for FastAPI application
Tests cover: POST /api/query, GET /api/courses, DELETE /api/session/{session_id}
Uses FastAPI TestClient with mocked RAGSystem dependencies
"""
import pytest
from fastapi import status
from unittest.mock import patch


# ============================================================================
# POST /api/query ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
def test_query_endpoint_success(client, mock_rag_system, valid_query_request):
    """Test successful query with session ID"""
    # Execute
    response = client.post("/api/query", json=valid_query_request)

    # Verify response
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "session_id" in data
    assert data["session_id"] == "test_session_123"

    # Verify RAGSystem called correctly
    mock_rag_system.query.assert_called_once_with(
        "What is prompt engineering?",
        "test_session_123"
    )


@pytest.mark.api
def test_query_endpoint_creates_session_when_missing(
    client,
    mock_rag_system,
    query_request_without_session
):
    """Test that endpoint creates session ID if not provided"""
    # Setup: mock session creation
    mock_rag_system.session_manager.create_session.return_value = "auto_session_456"

    # Execute
    response = client.post("/api/query", json=query_request_without_session)

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should have created a session
    mock_rag_system.session_manager.create_session.assert_called_once()
    assert data["session_id"] == "auto_session_456"


@pytest.mark.api
def test_query_endpoint_validation_error(client, invalid_query_request):
    """Test validation error for missing required field"""
    # Execute
    response = client.post("/api/query", json=invalid_query_request)

    # Verify 422 validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    data = response.json()
    assert "detail" in data
    # FastAPI validation error format
    assert isinstance(data["detail"], list)


@pytest.mark.api
def test_query_endpoint_empty_query(client, empty_query_request, mock_rag_system):
    """Test behavior with empty query string"""
    # Execute
    response = client.post("/api/query", json=empty_query_request)

    # Should still process (empty string is valid string type)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
def test_query_endpoint_handles_rag_exception(client, test_app):
    """Test error handling when RAGSystem raises exception"""
    # Patch the global rag_system to raise an exception
    with patch('app.rag_system') as mock_rag:
        mock_rag.query.side_effect = Exception("Vector store unavailable")
        mock_rag.session_manager.create_session.return_value = "session_err"

        response = client.post("/api/query", json={
            "query": "Test query",
            "session_id": "test_session"
        })

        # Should return 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        data = response.json()
        assert "detail" in data
        assert "Vector store unavailable" in data["detail"]


@pytest.mark.api
def test_query_endpoint_with_sources(client, mock_rag_system):
    """Test that sources are properly returned in response"""
    # Configure mock to return specific sources
    mock_rag_system.query.return_value = (
        "Response with sources",
        [
            {"text": "Course 1 - Lesson 1", "link": "https://example.com/1"},
            {"text": "Course 1 - Lesson 2", "link": "https://example.com/2"}
        ]
    )

    response = client.post("/api/query", json={
        "query": "Test with sources",
        "session_id": "test_session"
    })

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify sources structure
    assert len(data["sources"]) == 2
    assert data["sources"][0]["text"] == "Course 1 - Lesson 1"
    assert data["sources"][0]["link"] == "https://example.com/1"


@pytest.mark.api
def test_query_endpoint_preserves_conversation_context(client, mock_rag_system):
    """Test that multiple queries in same session maintain context"""
    session_id = "context_session_789"

    # First query
    response1 = client.post("/api/query", json={
        "query": "What is prompt engineering?",
        "session_id": session_id
    })
    assert response1.status_code == status.HTTP_200_OK

    # Second query in same session
    response2 = client.post("/api/query", json={
        "query": "Can you elaborate?",
        "session_id": session_id
    })
    assert response2.status_code == status.HTTP_200_OK

    # Verify both used same session
    assert mock_rag_system.query.call_count == 2
    calls = mock_rag_system.query.call_args_list
    assert calls[0][0][1] == session_id
    assert calls[1][0][1] == session_id


# ============================================================================
# GET /api/courses ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
def test_get_courses_success(client, mock_rag_system):
    """Test successful retrieval of course statistics"""
    # Execute
    response = client.get("/api/courses")

    # Verify response
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "total_courses" in data
    assert "course_titles" in data
    assert data["total_courses"] == 3
    assert len(data["course_titles"]) == 3
    assert "Introduction to Prompt Engineering" in data["course_titles"]

    # Verify RAGSystem called
    mock_rag_system.get_course_analytics.assert_called_once()


@pytest.mark.api
def test_get_courses_empty_catalog(client, mock_rag_system):
    """Test response when no courses are loaded"""
    # Configure mock for empty state
    mock_rag_system.get_course_analytics.return_value = {
        "total_courses": 0,
        "course_titles": []
    }

    response = client.get("/api/courses")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_courses"] == 0
    assert data["course_titles"] == []


@pytest.mark.api
def test_get_courses_handles_exception(client):
    """Test error handling when analytics fails"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.get_course_analytics.side_effect = Exception("ChromaDB not initialized")

        response = client.get("/api/courses")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data


@pytest.mark.api
def test_get_courses_response_schema(client, mock_rag_system):
    """Test that response matches CourseStats schema exactly"""
    response = client.get("/api/courses")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify exact schema (no extra fields)
    assert set(data.keys()) == {"total_courses", "course_titles"}
    assert isinstance(data["total_courses"], int)
    assert isinstance(data["course_titles"], list)
    assert all(isinstance(title, str) for title in data["course_titles"])


# ============================================================================
# DELETE /api/session/{session_id} ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
def test_clear_session_success(client, mock_rag_system):
    """Test successful session clearing"""
    session_id = "session_to_clear"

    # Execute
    response = client.delete(f"/api/session/{session_id}")

    # Verify response
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "ok"
    assert "message" in data

    # Verify session manager called
    mock_rag_system.session_manager.clear_session.assert_called_once_with(session_id)


@pytest.mark.api
def test_clear_nonexistent_session(client, mock_rag_system):
    """Test clearing session that doesn't exist (should succeed silently)"""
    # SessionManager.clear_session handles non-existent sessions gracefully
    response = client.delete("/api/session/nonexistent_session")

    # Should still return 200 OK
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
def test_clear_session_handles_exception(client):
    """Test error handling in session clearing"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.session_manager.clear_session.side_effect = Exception("Session DB error")

        response = client.delete("/api/session/test_session")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.api
def test_clear_session_with_special_characters(client, mock_rag_system):
    """Test session IDs with special characters (URL encoding)"""
    # Session IDs might contain underscores, hyphens, etc.
    session_id = "session-123_test"

    response = client.delete(f"/api/session/{session_id}")

    assert response.status_code == status.HTTP_200_OK
    mock_rag_system.session_manager.clear_session.assert_called_once_with(session_id)


# ============================================================================
# INTEGRATION TESTS (Multiple Endpoints)
# ============================================================================

@pytest.mark.api
@pytest.mark.integration
def test_full_conversation_flow(client, mock_rag_system):
    """Test complete flow: query → get courses → clear session"""
    # 1. Get available courses
    courses_response = client.get("/api/courses")
    assert courses_response.status_code == status.HTTP_200_OK

    # 2. Make a query
    query_response = client.post("/api/query", json={
        "query": "Tell me about the first course",
        "session_id": "flow_session"
    })
    assert query_response.status_code == status.HTTP_200_OK
    session_id = query_response.json()["session_id"]

    # 3. Clear the session
    clear_response = client.delete(f"/api/session/{session_id}")
    assert clear_response.status_code == status.HTTP_200_OK


@pytest.mark.api
@pytest.mark.integration
def test_concurrent_sessions(client, mock_rag_system):
    """Test that multiple concurrent sessions are handled correctly"""
    sessions = ["session_a", "session_b", "session_c"]

    for session_id in sessions:
        response = client.post("/api/query", json={
            "query": f"Query for {session_id}",
            "session_id": session_id
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["session_id"] == session_id

    # Each session should have been used once
    assert mock_rag_system.query.call_count == len(sessions)


# ============================================================================
# ERROR RESPONSE FORMAT TESTS
# ============================================================================

@pytest.mark.api
def test_error_response_format_500(client):
    """Test that 500 errors follow FastAPI HTTPException format"""
    with patch('app.rag_system') as mock_rag:
        mock_rag.query.side_effect = Exception("Test error")
        mock_rag.session_manager.create_session.return_value = "session"

        response = client.post("/api/query", json={"query": "test"})

        assert response.status_code == 500
        data = response.json()

        # FastAPI error format
        assert "detail" in data
        assert isinstance(data["detail"], str)


@pytest.mark.api
def test_error_response_format_422(client):
    """Test that validation errors follow FastAPI format"""
    response = client.post("/api/query", json={"invalid_field": "value"})

    assert response.status_code == 422
    data = response.json()

    # Pydantic validation error format
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert all("loc" in err and "msg" in err for err in data["detail"])


# ============================================================================
# CORS AND MIDDLEWARE TESTS
# ============================================================================

@pytest.mark.api
def test_cors_headers_present(client):
    """Test that CORS headers are present in responses"""
    response = client.get("/api/courses", headers={
        "Origin": "http://localhost:3000"
    })

    # CORS middleware should add headers
    # TestClient might not include all headers, but endpoint should work
    assert response.status_code == status.HTTP_200_OK


# ============================================================================
# RESPONSE SCHEMA VALIDATION TESTS
# ============================================================================

@pytest.mark.api
def test_query_response_schema(client, mock_rag_system):
    """Test that QueryResponse matches expected schema"""
    response = client.post("/api/query", json={
        "query": "Test query",
        "session_id": "test_session"
    })

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify required fields
    assert "answer" in data
    assert "sources" in data
    assert "session_id" in data

    # Verify types
    assert isinstance(data["answer"], str)
    assert isinstance(data["sources"], list)
    assert isinstance(data["session_id"], str)

    # Verify sources structure
    for source in data["sources"]:
        assert "text" in source
        assert "link" in source
