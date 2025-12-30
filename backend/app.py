import warnings

warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

import os
from typing import Any

from config import config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag_system import RAGSystem

# Global RAG system instance
rag_system = None


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for course queries"""

    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    """Response model for course queries"""

    answer: str
    sources: list[dict[str, Any]]  # {text: str, link: str | null}
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""

    total_courses: int
    course_titles: list[str]


def create_app(mount_static: bool = True, skip_startup: bool = False) -> FastAPI:
    """
    Factory function to create FastAPI app with configurable options.

    Args:
        mount_static: If True, mount static files from ../frontend directory
        skip_startup: If True, skip startup event (useful for testing)

    Returns:
        Configured FastAPI application instance
    """
    # Initialize FastAPI app
    app = FastAPI(title="Course Materials RAG System", root_path="")

    # Add trusted host middleware for proxy
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    # Enable CORS with proper settings for proxy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Initialize RAG system
    global rag_system  # noqa: PLW0603
    rag_system = RAGSystem(config)

    # API Endpoints

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest) -> QueryResponse:
        """Process a query and return response with sources"""
        try:
            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()

            # Process query using RAG system
            answer, sources = rag_system.query(request.query, session_id)

            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats() -> CourseStats:
        """Get course analytics and statistics"""
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.delete("/api/session/{session_id}")
    async def clear_session(session_id: str) -> dict[str, str]:
        """Clear a session's conversation history"""
        try:
            rag_system.session_manager.clear_session(session_id)
            return {"status": "ok", "message": "Session cleared"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    # Conditional startup event
    if not skip_startup:

        @app.on_event("startup")
        async def startup_event() -> None:
            """Load initial documents on startup"""
            docs_path = "../docs"
            if os.path.exists(docs_path):
                print("Loading initial documents...")
                try:
                    courses, chunks = rag_system.add_course_folder(
                        docs_path, clear_existing=False
                    )
                    print(f"Loaded {courses} courses with {chunks} chunks")
                except Exception as e:
                    print(f"Error loading documents: {e}")

    # Conditional static file mounting
    if mount_static:
        # Check if frontend directory exists before mounting
        frontend_dir = "../frontend"
        if os.path.exists(frontend_dir):
            app.mount(
                "/", StaticFiles(directory=frontend_dir, html=True), name="static"
            )
        else:
            # In development/testing without frontend
            print(
                f"Warning: Frontend directory '{frontend_dir}' not found. Skipping static file mounting."
            )

    return app


# Create module-level app instance for production (uvicorn app:app)
app = create_app()
