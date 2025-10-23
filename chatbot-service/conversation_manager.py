"""Conversation flow and memory management."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationTokenBufferMemory
)
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class ConversationSession:
    """Represents a single conversation session."""
    
    def __init__(self, session_id: str, user_id: str):
        """
        Initialize a conversation session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
        """
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.memory = self._create_memory()
    
    def _create_memory(self):
        """Create appropriate memory type based on configuration."""
        memory_type = settings.CONVERSATION_MEMORY_TYPE
        
        if memory_type == "buffer":
            return ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history",
                max_len=settings.MAX_CONVERSATION_HISTORY
            )
        elif memory_type == "summary":
            from llm_provider import llm_manager
            return ConversationSummaryMemory(
                llm=llm_manager.get_llm(),
                return_messages=True,
                memory_key="chat_history"
            )
        elif memory_type == "token":
            from llm_provider import llm_manager
            return ConversationTokenBufferMemory(
                llm=llm_manager.get_llm(),
                max_token_limit=2000,
                return_messages=True,
                memory_key="chat_history"
            )
        else:
            return ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
    
    def is_expired(self) -> bool:
        """
        Check if the session has expired.
        
        Returns:
            bool: True if session is expired
        """
        timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - self.last_activity > timeout
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.message_count += 1
    
    def add_message(self, human_message: str, ai_message: str):
        """
        Add a message exchange to memory.
        
        Args:
            human_message: User's message
            ai_message: AI's response
        """
        self.memory.save_context(
            {"input": human_message},
            {"output": ai_message}
        )
        self.update_activity()
    
    def get_history(self) -> List[BaseMessage]:
        """
        Get conversation history.
        
        Returns:
            List[BaseMessage]: List of messages in the conversation
        """
        return self.memory.load_memory_variables({}).get("chat_history", [])
    
    def clear(self):
        """Clear conversation memory."""
        self.memory.clear()
        logger.info(f"Cleared conversation history for session {self.session_id}")


class ConversationManager:
    """Manages multiple conversation sessions."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.sessions: Dict[str, ConversationSession] = {}
        logger.info("Conversation manager initialized")
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: User identifier
            
        Returns:
            str: New session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationSession(session_id, user_id)
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSession: The session if found, None otherwise
        """
        session = self.sessions.get(session_id)
        
        if session and session.is_expired():
            logger.info(f"Session {session_id} has expired, removing")
            self.end_session(session_id)
            return None
        
        return session
    
    def end_session(self, session_id: str):
        """
        End a conversation session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Ended session {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired:
            self.end_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            int: Number of active sessions
        """
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            dict: Session information if found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": session.message_count,
            "is_expired": session.is_expired()
        }


# Global conversation manager instance
conversation_manager = ConversationManager()

