"""LLM client utility for Phase 3 using LiteLLM"""

import os
from typing import List, Dict, Any, Optional
from loguru import logger
import litellm

from src.config import settings


class LLMClient:
    """LLM client wrapper using LiteLLM for multi-provider support"""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            provider: LLM provider (defaults to settings.LLM_PROVIDER)
            model: Model name (defaults to provider-specific default)
        """
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or self._get_default_model()
        self._configure_litellm()
        logger.info(f"Initialized LLMClient with provider={self.provider}, model={self.model}")
    
    def _get_default_model(self) -> str:
        """Get default model for provider"""
        if self.provider == "openai":
            return settings.OPENAI_MODEL
        elif self.provider == "lmstudio":
            return settings.LM_STUDIO_MODEL
        else:
            # Default fallback
            return "gpt-4"
    
    def _configure_litellm(self):
        """Configure LiteLLM based on provider"""
        if self.provider == "lmstudio":
            # LM Studio uses OpenAI-compatible API
            os.environ["OPENAI_API_BASE"] = settings.LM_STUDIO_API_BASE
            # Set dummy key if not provided (some APIs require it)
            if not settings.OPENAI_API_KEY:
                os.environ["OPENAI_API_KEY"] = "lm-studio"
            # Format model as openai/<model> for LiteLLM
            if not self.model.startswith("openai/"):
                self.model = f"openai/{self.model}"
        elif self.provider == "openai":
            if settings.OPENAI_API_KEY:
                os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            else:
                logger.warning("OPENAI_API_KEY not set, LLM calls may fail")
        # Other providers (anthropic, gemini, ollama) can be added similarly
    
    def completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Call LLM completion
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments for litellm.completion
            
        Returns:
            LiteLLM response object
        """
        try:
            call_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                call_kwargs["max_tokens"] = max_tokens
            
            logger.debug(f"Calling LLM: model={self.model}, messages={len(messages)}")
            response = litellm.completion(**call_kwargs)
            logger.debug(f"LLM response received: {len(response.choices)} choices")
            return response
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise
    
    def get_content(self, response: Any) -> str:
        """
        Extract content from LLM response
        
        Args:
            response: LiteLLM response object
            
        Returns:
            Content string
        """
        if response and response.choices:
            return response.choices[0].message.content
        return ""
    
    def get_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """
        Extract token usage from LLM response
        
        Args:
            response: LiteLLM response object
            
        Returns:
            Dictionary with prompt_tokens, completion_tokens, total_tokens
        """
        if hasattr(response, "usage") and response.usage:
            return {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        return None
