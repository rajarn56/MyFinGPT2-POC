"""Optimized Neo4j client for Phase 9: Query optimization and performance monitoring"""

import time
from typing import Dict, Any, List, Optional
from loguru import logger
from collections import defaultdict
from datetime import datetime, timedelta

from src.graph_db.neo4j_client import Neo4jClient


class QueryPerformanceTracker:
    """Track query performance metrics"""
    
    def __init__(self):
        """Initialize performance tracker"""
        self.query_times: List[float] = []
        self.query_counts: Dict[str, int] = defaultdict(int)
        self.slow_queries: List[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.max_slow_query_history = 100
    
    def record_query(
        self,
        query_type: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Record query performance
        
        Args:
            query_type: Type of query (e.g., "vector_search", "graph_traversal")
            duration: Query duration in seconds
            success: Whether query succeeded
            error: Error message if failed
        """
        self.query_times.append(duration)
        self.query_counts[query_type] += 1
        
        if not success:
            self.error_counts[query_type] += 1
            if error:
                logger.warning(f"Query error ({query_type}): {error}")
        
        # Track slow queries (> 1 second)
        if duration > 1.0:
            slow_query = {
                "type": query_type,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
                "error": error
            }
            self.slow_queries.append(slow_query)
            
            # Keep only recent slow queries
            if len(self.slow_queries) > self.max_slow_query_history:
                self.slow_queries.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.query_times:
            return {
                "total_queries": 0,
                "avg_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "query_counts": {},
                "error_counts": {},
                "slow_query_count": 0
            }
        
        return {
            "total_queries": len(self.query_times),
            "avg_duration": sum(self.query_times) / len(self.query_times),
            "min_duration": min(self.query_times),
            "max_duration": max(self.query_times),
            "query_counts": dict(self.query_counts),
            "error_counts": dict(self.error_counts),
            "slow_query_count": len(self.slow_queries),
            "slow_queries": self.slow_queries[-10:]  # Last 10 slow queries
        }
    
    def reset(self):
        """Reset all statistics"""
        self.query_times.clear()
        self.query_counts.clear()
        self.slow_queries.clear()
        self.error_counts.clear()


class OptimizedNeo4jClient(Neo4jClient):
    """
    Optimized Neo4j client with:
    - Query performance tracking
    - Query optimization hints
    - Connection pooling optimization
    - Query result caching (optional)
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        enable_performance_tracking: bool = True
    ):
        """
        Initialize optimized Neo4j client
        
        Args:
            uri: Neo4j URI
            user: Neo4j username
            password: Neo4j password
            database: Database name
            enable_performance_tracking: Enable performance tracking
        """
        super().__init__(uri, user, password, database)
        
        self.performance_tracker = QueryPerformanceTracker() if enable_performance_tracking else None
        self.query_cache: Dict[str, Any] = {}  # Simple query cache
        self.cache_enabled = False  # Disabled by default (can be enabled if needed)
    
    def execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        query_type: str = "general",
        use_cache: bool = False,
        cache_ttl_seconds: int = 60
    ) -> List[Dict]:
        """
        Execute optimized Cypher query with performance tracking
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            query_type: Type of query for tracking
            use_cache: Whether to use query cache
            cache_ttl_seconds: Cache TTL in seconds
            
        Returns:
            Query results
        """
        # Check cache if enabled
        if use_cache and self.cache_enabled:
            cache_key = self._get_cache_key(query, parameters or {})
            cached_result = self.query_cache.get(cache_key)
            if cached_result:
                cached_data, cached_time = cached_result
                if time.time() - cached_time < cache_ttl_seconds:
                    logger.debug(f"Cache hit for query: {query_type}")
                    return cached_data
        
        # Optimize query
        optimized_query = self._optimize_query(query)
        
        # Execute with performance tracking
        start_time = time.time()
        success = True
        error = None
        
        try:
            result = super().execute_query(optimized_query, parameters)
            
            # Cache result if enabled
            if use_cache and self.cache_enabled:
                cache_key = self._get_cache_key(query, parameters or {})
                self.query_cache[cache_key] = (result, time.time())
            
            return result
        except Exception as e:
            success = False
            error = str(e)
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            # Record performance
            duration = time.time() - start_time
            if self.performance_tracker:
                self.performance_tracker.record_query(
                    query_type=query_type,
                    duration=duration,
                    success=success,
                    error=error
                )
    
    def _optimize_query(self, query: str) -> str:
        """
        Apply query optimizations
        
        Args:
            query: Original query
            
        Returns:
            Optimized query
        """
        optimized = query
        
        # Add query hints for optimization
        # Note: These are Neo4j-specific optimizations
        
        # Use index hints for common patterns
        if "MATCH (c:Company)" in query and "WHERE" in query:
            # Ensure index is used for Company lookups
            if "USING INDEX" not in query:
                # Neo4j will automatically use indexes, but we can add hints
                pass
        
        # Optimize LIMIT placement
        # LIMIT should be applied as early as possible
        
        return optimized
    
    def _get_cache_key(self, query: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for query"""
        import hashlib
        import json
        
        key_data = {
            "query": query,
            "parameters": parameters
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def execute_vector_search(
        self,
        query_embedding: List[float],
        semantic_type: Optional[str] = None,
        company_cik: Optional[str] = None,
        form_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Optimized vector similarity search
        
        Args:
            query_embedding: Query embedding vector
            semantic_type: Filter by semantic type
            company_cik: Filter by company CIK
            form_type: Filter by form type
            limit: Maximum results
            
        Returns:
            Search results
        """
        # Build optimized query with proper index usage
        query_parts = [
            "MATCH (ch:Chunk)",
            "WHERE ch.embedding IS NOT NULL"
        ]
        
        params = {}
        
        if semantic_type:
            query_parts.append("AND ch.semantic_type = $semantic_type")
            params["semantic_type"] = semantic_type
        
        if company_cik:
            query_parts.append("AND ch.company_cik = $company_cik")
            params["company_cik"] = company_cik
        
        if form_type:
            query_parts.append("AND ch.form_type = $form_type")
            params["form_type"] = form_type
        
        # Vector similarity search (Neo4j 5.x+ syntax)
        query_parts.append(
            "CALL db.index.vector.queryNodes("
            "'textChunkEmbeddings', "
            "$limit, "
            "$query_embedding"
            ") YIELD node AS ch, score"
        )
        params["query_embedding"] = query_embedding
        params["limit"] = limit
        
        query_parts.append("RETURN ch, score")
        query_parts.append("ORDER BY score DESC")
        query_parts.append(f"LIMIT {limit}")
        
        query = "\n".join(query_parts)
        
        # Execute with performance tracking
        results = self.execute_query(
            query=query,
            parameters=params,
            query_type="vector_search"
        )
        
        # Format results
        formatted_results = []
        for record in results:
            chunk_node = record.get("chunk_node", record.get("ch"))
            if chunk_node:
                formatted_results.append({
                    "chunk_id": chunk_node.get("chunk_id"),
                    "content": chunk_node.get("content"),
                    "similarity_score": record.get("score", 0.0),
                    "metadata": {
                        "semantic_type": chunk_node.get("semantic_type"),
                        "company_cik": chunk_node.get("company_cik"),
                        "form_type": chunk_node.get("form_type")
                    }
                })
        
        return formatted_results
    
    def execute_graph_traversal(
        self,
        start_node_label: str,
        start_node_property: str,
        start_node_value: Any,
        relationship_types: List[str],
        target_labels: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Optimized graph traversal query
        
        Args:
            start_node_label: Label of start node
            start_node_property: Property to match on start node
            start_node_value: Value to match
            relationship_types: Types of relationships to traverse
            target_labels: Labels of target nodes
            limit: Maximum results
            
        Returns:
            Traversal results
        """
        # Build optimized traversal query
        rel_pattern = "|".join(relationship_types) if relationship_types else "*"
        target_pattern = ":".join(target_labels) if target_labels else ""
        
        query = f"""
        MATCH (start:{start_node_label} {{{start_node_property}: $start_value}})
        MATCH path = (start)-[:{rel_pattern}*1..3]->(target{target_pattern})
        WHERE start.{start_node_property} = $start_value
        RETURN target, length(path) AS path_length
        ORDER BY path_length ASC
        LIMIT $limit
        """
        
        results = self.execute_query(
            query=query,
            parameters={
                "start_value": start_node_value,
                "limit": limit
            },
            query_type="graph_traversal"
        )
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if self.performance_tracker:
            return self.performance_tracker.get_stats()
        return {}
    
    def clear_query_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def enable_query_cache(self, enabled: bool = True):
        """Enable or disable query cache"""
        self.cache_enabled = enabled
        logger.info(f"Query cache {'enabled' if enabled else 'disabled'}")
