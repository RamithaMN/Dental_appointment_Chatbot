"""Configuration settings for the chatbot microservice."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    SERVICE_PORT: int = 8001
    SERVICE_HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"
    
    # LLM Provider
    LLM_PROVIDER: Literal["openai", "anthropic", "local", "mock"] = "openai"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1000
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_MAX_TOKENS: int = 1000
    
    # Local Model Configuration
    LOCAL_MODEL_NAME: str = "mistralai/Mistral-7B-Instruct-v0.2"
    LOCAL_MODEL_DEVICE: str = "cpu"
    
    # Conversation Settings
    MAX_CONVERSATION_HISTORY: int = 10
    CONVERSATION_MEMORY_TYPE: Literal["buffer", "summary", "token"] = "buffer"
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # Vector Store
    ENABLE_RAG: bool = False
    VECTOR_STORE_TYPE: str = "chroma"
    VECTOR_STORE_PATH: str = "./data/vectorstore"
    
    # Chatbot Context
    CHATBOT_NAME: str = "DentalBot"
    CHATBOT_ROLE: str = "friendly dental assistant"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

