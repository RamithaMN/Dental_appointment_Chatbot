"""FastAPI application for dental chatbot microservice."""

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings
from models import (
    ChatRequest,
    ChatResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionInfoResponse,
    HealthCheckResponse,
    ErrorResponse
)
from chatbot_chain import dental_chatbot
from conversation_manager import conversation_manager
from llm_provider import llm_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Dental Chatbot Microservice...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Verify LLM is available
    if not llm_manager.is_available():
        logger.warning("LLM is not available at startup!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dental Chatbot Microservice...")
    conversation_manager.cleanup_expired_sessions()


# Initialize FastAPI app
app = FastAPI(
    title="Dental Chatbot Microservice",
    description="LangChain-powered dental assistant chatbot service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health & Status ====================

@app.get(
    "/",
    tags=["Health"]
)
async def root():
    """Root endpoint."""
    return {
        "service": "Dental Chatbot Microservice",
        "version": "1.0.0",
        "status": "online"
    }


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"]
)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        llm_provider=settings.LLM_PROVIDER,
        llm_available=llm_manager.is_available(),
        active_sessions=conversation_manager.get_active_sessions_count(),
        timestamp=datetime.now()
    )


# ==================== Session Management ====================

@app.post(
    "/api/sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"]
)
async def create_session(request: SessionCreateRequest):
    """
    Create a new conversation session.
    
    Args:
        request: Session creation request
        
    Returns:
        SessionCreateResponse: New session information
    """
    try:
        session_id = conversation_manager.create_session(request.user_id)
        return SessionCreateResponse(
            session_id=session_id,
            created_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@app.get(
    "/api/sessions/{session_id}",
    response_model=SessionInfoResponse,
    tags=["Sessions"]
)
async def get_session_info(session_id: str):
    """
    Get information about a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionInfoResponse: Session information
    """
    info = conversation_manager.get_session_info(session_id)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    return SessionInfoResponse(**info)


@app.delete(
    "/api/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Sessions"]
)
async def end_session(session_id: str):
    """
    End a conversation session.
    
    Args:
        session_id: Session identifier
    """
    conversation_manager.end_session(session_id)
    return None


# ==================== Chat ====================

@app.post(
    "/api/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    responses={
        200: {"description": "Successful response"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Internal error", "model": ErrorResponse}
    }
)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a chat message and generate a response.
    
    Args:
        request: Chat request containing message and session info
        background_tasks: Background tasks manager
        
    Returns:
        ChatResponse: Chatbot's response
    """
    try:
        # Get or create session
        if request.session_id:
            session = conversation_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or expired. Please create a new session."
                )
        else:
            session_id = conversation_manager.create_session(request.user_id)
            session = conversation_manager.get_session(session_id)
        
        # Generate response
        response_text = await dental_chatbot.chat(
            message=request.message,
            session=session,
            context=request.context
        )
        
        # Schedule cleanup in background
        background_tasks.add_task(conversation_manager.cleanup_expired_sessions)
        
        return ChatResponse(
            response=response_text,
            session_id=session.session_id,
            timestamp=datetime.now(),
            message_count=session.message_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message. Please try again."
        )


# ==================== Utilities ====================

@app.post(
    "/api/sessions/{session_id}/clear",
    status_code=status.HTTP_200_OK,
    tags=["Sessions"]
)
async def clear_session_history(session_id: str):
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session identifier
    """
    session = conversation_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    session.clear()
    return {"message": "Session history cleared"}


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=str(exc.status_code),
            timestamp=datetime.now()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="An unexpected error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            timestamp=datetime.now()
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.ENVIRONMENT == "development"
    )

