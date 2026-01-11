"""Embedding pipeline for Phase 4 Knowledge Layer"""

import os
from typing import List, Optional
from loguru import logger
import litellm

from src.config import settings


class EmbeddingPipeline:
    """Handles embedding generation for vector database"""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize embedding pipeline
        
        Args:
            provider: Embedding provider (openai, lmstudio, etc.)
                     If None, uses EMBEDDING_PROVIDER env var or falls back to LLM provider
            model: Embedding model name (e.g., "text-embedding-ada-002" for OpenAI)
                   If None, uses EMBEDDING_MODEL env var or provider default
        """
        # Determine provider
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "")
        if embedding_provider:
            self.provider = embedding_provider
        elif provider:
            self.provider = provider
        else:
            # Fall back to LLM provider
            self.provider = settings.LLM_PROVIDER
        
        # Determine model
        embedding_model_env = os.getenv("EMBEDDING_MODEL", "")
        if model:
            self.embedding_model = model
        elif embedding_model_env:
            self.embedding_model = embedding_model_env
        elif self.provider == "openai":
            self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        elif self.provider == "lmstudio":
            # LMStudio typically uses OpenAI-compatible embedding models
            self.embedding_model = embedding_model_env or "text-embedding-ada-002"
        else:
            # Default to OpenAI embedding model
            self.embedding_model = "text-embedding-ada-002"
        
        # Cache for detected embedding dimension
        self._cached_dimension: Optional[int] = None
        
        logger.info(f"Initialized EmbeddingPipeline: provider={self.provider}, model={self.embedding_model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (list of floats)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        try:
            if self.provider == "lmstudio":
                return self._generate_lmstudio_embedding(text)
            elif self.provider == "openai":
                return self._generate_openai_embedding(text)
            else:
                # Default to OpenAI
                logger.warning(f"Unknown provider {self.provider}, falling back to OpenAI")
                return self._generate_openai_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def _generate_lmstudio_embedding(self, text: str) -> List[float]:
        """Generate embedding using LMStudio"""
        # Set up LMStudio API base
        api_base = settings.LM_STUDIO_API_BASE
        os.environ["OPENAI_API_BASE"] = api_base
        
        # Set dummy key if not provided (LMStudio doesn't validate it)
        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "lm-studio"
        
        # Format model name for LiteLLM
        model_name = self.embedding_model
        if not model_name.startswith("openai/"):
            model_name = f"openai/{model_name}"
        
        try:
            response = litellm.embedding(
                model=model_name,
                input=[text],
                api_base=api_base
            )
            
            if response and response.data and len(response.data) > 0:
                embedding = response.data[0]["embedding"]
                # Cache dimension on first successful call
                if self._cached_dimension is None:
                    self._cached_dimension = len(embedding)
                return embedding
            else:
                raise ValueError("Empty response from LMStudio embedding API")
        except Exception as e:
            logger.error(f"LMStudio embedding failed: {e}")
            raise
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set for OpenAI embeddings")
        
        os.environ["OPENAI_API_KEY"] = api_key
        
        try:
            response = litellm.embedding(
                model=self.embedding_model,
                input=[text]
            )
            
            if response and response.data and len(response.data) > 0:
                embedding = response.data[0]["embedding"]
                # Cache dimension on first successful call
                if self._cached_dimension is None:
                    self._cached_dimension = len(embedding)
                return embedding
            else:
                raise ValueError("Empty response from OpenAI embedding API")
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error generating embedding for text: {e}")
                # Add empty embedding as fallback
                embeddings.append([])
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings generated by this pipeline
        
        Returns:
            Embedding dimension (e.g., 1536 for text-embedding-ada-002)
        """
        if self._cached_dimension is not None:
            return self._cached_dimension
        
        # Generate a test embedding to detect dimension
        try:
            test_embedding = self.generate_embedding("test")
            if test_embedding:
                self._cached_dimension = len(test_embedding)
                return self._cached_dimension
        except Exception as e:
            logger.error(f"Error detecting embedding dimension: {e}")
        
        # Default dimension for text-embedding-ada-002
        return 1536
