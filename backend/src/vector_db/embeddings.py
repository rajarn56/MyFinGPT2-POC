"""Embedding pipeline for Phase 4 Knowledge Layer with Phase 9 caching"""

import os
from typing import List, Optional
from loguru import logger
import litellm

from src.config import settings
from src.utils.cache import EmbeddingCache


class EmbeddingPipeline:
    """Handles embedding generation for vector database with caching"""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        embedding_cache: Optional[EmbeddingCache] = None
    ):
        """
        Initialize embedding pipeline
        
        Args:
            provider: Embedding provider (openai, lmstudio, etc.)
                     If None, uses EMBEDDING_PROVIDER env var or falls back to LLM provider
            model: Embedding model name (e.g., "text-embedding-ada-002" for OpenAI)
                   If None, uses EMBEDDING_MODEL env var or provider default
            embedding_cache: Optional embedding cache instance (created if not provided)
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
        
        # Initialize embedding cache (Phase 9)
        self.embedding_cache = embedding_cache or EmbeddingCache(
            max_size=10000,
            ttl_hours=24 * 7  # 7 days
        )
        
        logger.info(f"Initialized EmbeddingPipeline: provider={self.provider}, model={self.embedding_model}")
    
    def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for text (with caching)
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Embedding vector (list of floats)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        # Check cache first (Phase 9)
        if use_cache:
            cached_embedding = self.embedding_cache.get(text)
            if cached_embedding is not None:
                logger.debug(f"Cache hit for embedding: {text[:50]}...")
                return cached_embedding
        
        try:
            if self.provider == "lmstudio":
                embedding = self._generate_lmstudio_embedding(text)
            elif self.provider == "openai":
                embedding = self._generate_openai_embedding(text)
            else:
                # Default to OpenAI
                logger.warning(f"Unknown provider {self.provider}, falling back to OpenAI")
                embedding = self._generate_openai_embedding(text)
            
            # Cache the result (Phase 9)
            if use_cache and embedding:
                self.embedding_cache.set(text, embedding)
            
            return embedding
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
    
    def generate_batch_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True,
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing with caching)
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache (default: True)
            batch_size: Batch size for API calls (default: 100)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        # Process in batches for better performance (Phase 9)
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Check cache for batch
            batch_embeddings = []
            texts_to_embed = []
            indices_to_embed = []
            
            for idx, text in enumerate(batch):
                if use_cache:
                    cached = self.embedding_cache.get(text)
                    if cached is not None:
                        batch_embeddings.append((idx, cached))
                        continue
                
                texts_to_embed.append(text)
                indices_to_embed.append(idx)
            
            # Generate embeddings for uncached texts
            if texts_to_embed:
                try:
                    # Use litellm batch embedding if available
                    if self.provider == "openai":
                        response = litellm.embedding(
                            model=self.embedding_model,
                            input=texts_to_embed
                        )
                        
                        if response and response.data:
                            for idx, text in zip(indices_to_embed, texts_to_embed):
                                embedding = response.data[indices_to_embed.index(idx)]["embedding"]
                                batch_embeddings.append((idx, embedding))
                                
                                # Cache the result
                                if use_cache:
                                    self.embedding_cache.set(text, embedding)
                    else:
                        # Fall back to individual calls
                        for idx, text in zip(indices_to_embed, texts_to_embed):
                            embedding = self.generate_embedding(text, use_cache=use_cache)
                            batch_embeddings.append((idx, embedding))
                except Exception as e:
                    logger.error(f"Error generating batch embeddings: {e}")
                    # Fall back to individual calls
                    for idx, text in zip(indices_to_embed, texts_to_embed):
                        try:
                            embedding = self.generate_embedding(text, use_cache=use_cache)
                            batch_embeddings.append((idx, embedding))
                        except Exception as e2:
                            logger.error(f"Error generating embedding for text: {e2}")
                            batch_embeddings.append((idx, []))
            
            # Sort by original index and extract embeddings
            batch_embeddings.sort(key=lambda x: x[0])
            embeddings.extend([emb for _, emb in batch_embeddings])
        
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
