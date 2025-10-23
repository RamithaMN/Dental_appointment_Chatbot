"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(..., description="User's message", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    user_id: str = Field(..., description="User identifier")
    context: Optional[Dict] = Field(None, description="Additional context for the conversation")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "message": "I'd like to schedule a teeth cleaning appointment",
                "user_id": "user123",
                "context": {
                    "user_name": "John Doe"
                }
            }]
        }
    }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    response: str = Field(..., description="Chatbot's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    message_count: int = Field(..., description="Number of messages in this session")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        },
        "json_schema_extra": {
            "examples": [{
                "response": "I'd be happy to help you schedule a teeth cleaning! ...",
                "session_id": "abc-123-def",
                "timestamp": "2025-10-22T12:00:00Z",
                "message_count": 5
            }]
        }
    }


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session."""
    
    user_id: str = Field(..., description="User identifier")


class SessionCreateResponse(BaseModel):
    """Response model for session creation."""
    
    session_id: str = Field(..., description="New session ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class SessionInfoResponse(BaseModel):
    """Response model for session information."""
    
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    message_count: int
    is_expired: bool


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    llm_provider: str = Field(..., description="Configured LLM provider")
    llm_available: bool = Field(..., description="Whether LLM is available")
    active_sessions: int = Field(..., description="Number of active sessions")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

