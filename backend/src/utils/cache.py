"""Caching layer for Phase 9: Advanced Knowledge Layer

Implements:
- Embedding cache (caches computed embeddings)
- Query result cache (caches search results)
- Cache invalidation strategies
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from collections import OrderedDict


class LRUCache:
    """LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items in cache
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        if key in self.cache:
            # Update existing and move to end
            self.cache.move_to_end(key)
        else:
            # Check if we need to evict
            if len(self.cache) >= self.max_size:
                # Remove least recently used (first item)
                self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class TimedCacheEntry:
    """Cache entry with expiration time"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        """
        Initialize cache entry
        
        Args:
            value: Cached value
            ttl_seconds: Time to live in seconds
        """
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return datetime.utcnow() > self.expires_at


class EmbeddingCache:
    """Cache for embeddings to avoid recomputing"""
    
    def __init__(self, max_size: int = 10000, ttl_hours: int = 24 * 7):  # 7 days default
        """
        Initialize embedding cache
        
        Args:
            max_size: Maximum number of cached embeddings
            ttl_hours: Time to live in hours
        """
        self.cache: Dict[str, TimedCacheEntry] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.hits = 0
        self.misses = 0
    
    def _hash_text(self, text: str) -> str:
        """Generate hash key for text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding
        
        Args:
            text: Text to look up
            
        Returns:
            Cached embedding or None
        """
        key = self._hash_text(text)
        
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                # Remove expired entry
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            return entry.value
        
        self.misses += 1
        return None
    
    def set(self, text: str, embedding: List[float]):
        """
        Cache embedding
        
        Args:
            text: Text that was embedded
            embedding: Embedding vector
        """
        key = self._hash_text(text)
        
        # Check if we need to evict (simple FIFO if over limit)
        if len(self.cache) >= self.max_size:
            # Remove oldest expired entries first
            expired_keys = [
                k for k, v in self.cache.items()
                if v.is_expired()
            ]
            
            for k in expired_keys:
                del self.cache[k]
            
            # If still over limit, remove oldest
            if len(self.cache) >= self.max_size:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].created_at
                )
                del self.cache[oldest_key]
        
        self.cache[key] = TimedCacheEntry(embedding, self.ttl_seconds)
    
    def clear(self):
        """Clear all cached embeddings"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        # Count expired entries
        expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "expired_entries": expired_count
        }


class QueryResultCache:
    """Cache for query results"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 1):  # 1 hour default
        """
        Initialize query result cache
        
        Args:
            max_size: Maximum number of cached queries
            ttl_hours: Time to live in hours
        """
        self.cache: Dict[str, TimedCacheEntry] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.hits = 0
        self.misses = 0
    
    def _hash_query(
        self,
        query: str,
        collection_name: str,
        n_results: int,
        where: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate hash key for query"""
        query_dict = {
            "query": query,
            "collection": collection_name,
            "n_results": n_results,
            "where": where or {}
        }
        query_str = json.dumps(query_dict, sort_keys=True)
        return hashlib.sha256(query_str.encode('utf-8')).hexdigest()
    
    def get(
        self,
        query: str,
        collection_name: str,
        n_results: int,
        where: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached query results
        
        Args:
            query: Query text or embedding hash
            collection_name: Collection name
            n_results: Number of results
            where: Metadata filter
            
        Returns:
            Cached results or None
        """
        key = self._hash_query(query, collection_name, n_results, where)
        
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            return entry.value
        
        self.misses += 1
        return None
    
    def set(
        self,
        query: str,
        collection_name: str,
        results: List[Dict[str, Any]],
        n_results: int,
        where: Optional[Dict[str, Any]] = None
    ):
        """
        Cache query results
        
        Args:
            query: Query text or embedding hash
            collection_name: Collection name
            results: Query results
            n_results: Number of results
            where: Metadata filter
        """
        key = self._hash_query(query, collection_name, n_results, where)
        
        # Check if we need to evict
        if len(self.cache) >= self.max_size:
            # Remove expired entries first
            expired_keys = [
                k for k, v in self.cache.items()
                if v.is_expired()
            ]
            
            for k in expired_keys:
                del self.cache[k]
            
            # If still over limit, remove oldest
            if len(self.cache) >= self.max_size:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].created_at
                )
                del self.cache[oldest_key]
        
        self.cache[key] = TimedCacheEntry(results, self.ttl_seconds)
    
    def invalidate_collection(self, collection_name: str):
        """
        Invalidate all cached results for a collection
        
        Args:
            collection_name: Collection name to invalidate
        """
        keys_to_delete = [
            k for k in self.cache.keys()
            if collection_name in k  # Simple check - could be improved
        ]
        
        for k in keys_to_delete:
            del self.cache[k]
        
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for collection {collection_name}")
    
    def clear(self):
        """Clear all cached queries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "expired_entries": expired_count
        }


class CacheManager:
    """Central cache manager for all caching needs"""
    
    def __init__(
        self,
        embedding_cache_size: int = 10000,
        embedding_ttl_hours: int = 24 * 7,
        query_cache_size: int = 1000,
        query_ttl_hours: int = 1
    ):
        """
        Initialize cache manager
        
        Args:
            embedding_cache_size: Max size for embedding cache
            embedding_ttl_hours: TTL for embeddings (hours)
            query_cache_size: Max size for query cache
            query_ttl_hours: TTL for query results (hours)
        """
        self.embedding_cache = EmbeddingCache(
            max_size=embedding_cache_size,
            ttl_hours=embedding_ttl_hours
        )
        self.query_cache = QueryResultCache(
            max_size=query_cache_size,
            ttl_hours=query_ttl_hours
        )
        
        logger.info("CacheManager initialized")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        return {
            "embedding_cache": self.embedding_cache.get_stats(),
            "query_cache": self.query_cache.get_stats()
        }
    
    def clear_all(self):
        """Clear all caches"""
        self.embedding_cache.clear()
        self.query_cache.clear()
        logger.info("All caches cleared")
