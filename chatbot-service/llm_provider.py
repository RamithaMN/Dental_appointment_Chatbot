"""LLM provider factory and management."""

from typing import Optional, Any
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import AnthropicLLM as ChatAnthropic
except ImportError:
    from langchain_community.llms import Anthropic as ChatAnthropic
from langchain.llms.base import BaseLLM
from langchain.schema import BaseMessage, AIMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from config import settings
import logging
import re

logger = logging.getLogger(__name__)


class MockLLM(BaseLLM):
    """Mock LLM for testing and demo purposes without requiring API keys."""
    
    @property
    def _llm_type(self) -> str:
        return "mock"
    
    def _generate(
        self,
        prompts: list[str],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """Generate responses for a list of prompts."""
        from langchain.schema import Generation, LLMResult
        
        generations = []
        for prompt in prompts:
            text = self._get_mock_response(prompt)
            generations.append([Generation(text=text)])
        
        return LLMResult(generations=generations)
    
    def _call(
        self,
        prompt: str,
        stop: Optional[list] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a mock response based on the prompt."""
        return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """Generate a mock response based on the prompt."""
        prompt_lower = prompt.lower()
        
        # Appointment scheduling
        if any(word in prompt_lower for word in ["appointment", "schedule", "book", "reservation"]):
            return (
                "I'd be happy to help you schedule an appointment! 😊\n\n"
                "Could you please provide me with the following information:\n"
                "- Your preferred date and time\n"
                "- The reason for your visit (checkup, cleaning, specific concern)\n"
                "- Your contact phone number\n\n"
                "We're open Monday-Friday 8:00 AM - 6:00 PM, and Saturdays 9:00 AM - 2:00 PM."
            )
        
        # Services inquiry
        if any(word in prompt_lower for word in ["service", "offer", "do you", "what can"]):
            return (
                "We offer a comprehensive range of dental services including:\n\n"
                "🦷 General Dentistry (checkups, cleanings, fillings)\n"
                "✨ Cosmetic Dentistry (whitening, veneers, bonding)\n"
                "🦷 Orthodontics (braces, Invisalign)\n"
                "⚕️ Oral Surgery (extractions, wisdom teeth)\n"
                "🏥 Periodontics (gum disease treatment)\n"
                "🦷 Endodontics (root canals)\n"
                "🚑 Emergency Dental Care\n\n"
                "Which service are you interested in learning more about?"
            )
        
        # Hours inquiry
        if any(word in prompt_lower for word in ["hours", "open", "closed", "time"]):
            return (
                "Our office hours are:\n\n"
                "📅 Monday - Friday: 8:00 AM - 6:00 PM\n"
                "📅 Saturday: 9:00 AM - 2:00 PM\n"
                "📅 Sunday: Closed\n\n"
                "We also have a 24/7 emergency line for urgent dental needs. "
                "Would you like to schedule an appointment?"
            )
        
        # Pain/emergency
        if any(word in prompt_lower for word in ["pain", "hurt", "emergency", "urgent", "tooth ache", "toothache"]):
            return (
                "I'm sorry to hear you're experiencing discomfort! 😟\n\n"
                "For dental pain or emergencies, I recommend:\n"
                "1. Call our emergency line immediately: (555) 123-4567\n"
                "2. We have same-day emergency appointments available\n"
                "3. In the meantime, you can rinse with warm salt water and take over-the-counter pain medication\n\n"
                "Would you like me to schedule an emergency appointment for you?"
            )
        
        # Greeting
        if any(word in prompt_lower for word in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
            return (
                "Hello! Welcome to our dental practice! 👋\n\n"
                "I'm DentalBot, your friendly dental assistant. I'm here to help you with:\n"
                "- Scheduling appointments\n"
                "- Information about our services\n"
                "- Answering general dental questions\n"
                "- Office hours and location\n\n"
                "How can I assist you today?"
            )
        
        # Cost/price/insurance
        if any(word in prompt_lower for word in ["cost", "price", "insurance", "payment", "afford", "expensive"]):
            return (
                "Great question about costs! 💰\n\n"
                "We accept most major insurance plans and offer flexible payment options. "
                "Specific costs vary based on the treatment needed.\n\n"
                "For an accurate quote, I recommend scheduling a consultation where we can:\n"
                "- Assess your specific needs\n"
                "- Verify your insurance coverage\n"
                "- Provide a detailed treatment plan with costs\n\n"
                "Would you like to schedule a consultation?"
            )
        
        # Cleaning
        if "clean" in prompt_lower:
            return (
                "Professional teeth cleanings are essential for oral health! 🦷✨\n\n"
                "Our dental cleanings include:\n"
                "- Plaque and tartar removal\n"
                "- Polishing\n"
                "- Fluoride treatment\n"
                "- Oral health assessment\n\n"
                "We recommend cleanings every 6 months. "
                "Would you like to schedule a cleaning appointment?"
            )
        
        # Default response
        return (
            "Thank you for your question! I'm here to help with information about "
            "our dental services, scheduling appointments, and general dental care questions.\n\n"
            "Could you please provide a bit more detail about what you'd like to know? "
            "For example:\n"
            "- Need to schedule an appointment?\n"
            "- Questions about specific dental procedures?\n"
            "- Want to know our office hours?\n\n"
            "I'm here to help! 😊"
        )


class LLMProviderFactory:
    """Factory for creating LLM instances based on configuration."""
    
    @staticmethod
    def create_llm() -> BaseLLM:
        """
        Create and return an LLM instance based on the configured provider.
        
        Returns:
            BaseLLM: Configured LLM instance
            
        Raises:
            ValueError: If the provider is not supported or configuration is invalid
        """
        provider = settings.LLM_PROVIDER.lower()
        
        try:
            if provider == "openai":
                return LLMProviderFactory._create_openai_llm()
            elif provider == "anthropic":
                return LLMProviderFactory._create_anthropic_llm()
            elif provider == "local":
                return LLMProviderFactory._create_local_llm()
            elif provider == "mock":
                return LLMProviderFactory._create_mock_llm()
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to create LLM provider {provider}: {str(e)}")
            raise
    
    @staticmethod
    def _create_openai_llm() -> ChatOpenAI:
        """Create OpenAI LLM instance."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        
        logger.info(f"Initializing OpenAI LLM with model: {settings.OPENAI_MODEL}")
        
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            model_kwargs={
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }
        )
    
    @staticmethod
    def _create_anthropic_llm() -> ChatAnthropic:
        """Create Anthropic LLM instance."""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        
        logger.info(f"Initializing Anthropic LLM with model: {settings.ANTHROPIC_MODEL}")
        
        return ChatAnthropic(
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            temperature=settings.ANTHROPIC_TEMPERATURE,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
        )
    
    @staticmethod
    def _create_local_llm():
        """Create local/open-source LLM instance."""
        try:
            from langchain_community.llms import HuggingFacePipeline
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            logger.info(f"Initializing local LLM: {settings.LOCAL_MODEL_NAME}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(settings.LOCAL_MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(
                settings.LOCAL_MODEL_NAME,
                device_map=settings.LOCAL_MODEL_DEVICE,
                torch_dtype="auto"
            )
            
            # Create pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )
            
            return HuggingFacePipeline(pipeline=pipe)
            
        except ImportError as e:
            raise ValueError(
                "Local LLM requires additional dependencies. "
                "Install with: pip install transformers torch"
            ) from e
    
    @staticmethod
    def _create_mock_llm() -> MockLLM:
        """Create mock LLM instance for testing and demo purposes."""
        logger.info("Initializing Mock LLM (no API key required)")
        return MockLLM()


class LLMManager:
    """Manages LLM instance and provides utility methods."""
    
    def __init__(self):
        """Initialize the LLM manager."""
        self.llm: Optional[BaseLLM] = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM instance."""
        try:
            self.llm = LLMProviderFactory.create_llm()
            logger.info(f"Successfully initialized {settings.LLM_PROVIDER} LLM")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise
    
    def get_llm(self) -> BaseLLM:
        """
        Get the LLM instance.
        
        Returns:
            BaseLLM: The initialized LLM instance
        """
        if self.llm is None:
            self._initialize_llm()
        return self.llm
    
    def is_available(self) -> bool:
        """
        Check if LLM is available and ready.
        
        Returns:
            bool: True if LLM is initialized and ready
        """
        return self.llm is not None


# Global LLM manager instance
llm_manager = LLMManager()

