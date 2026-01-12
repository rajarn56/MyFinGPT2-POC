"""Performance monitoring service for Phase 9"""

from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

from src.utils.cache import CacheManager
from src.graph_db.optimized_neo4j_client import OptimizedNeo4jClient


class PerformanceMonitor:
    """
    Centralized performance monitoring service
    
    Tracks:
    - Cache hit rates (embedding cache, query cache)
    - Query performance (Neo4j, Chroma)
    - System metrics
    """
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        neo4j_client: Optional[OptimizedNeo4jClient] = None
    ):
        """
        Initialize performance monitor
        
        Args:
            cache_manager: CacheManager instance
            neo4j_client: OptimizedNeo4jClient instance
        """
        self.cache_manager = cache_manager
        self.neo4j_client = neo4j_client
        
        logger.info("PerformanceMonitor initialized")
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics
        
        Returns:
            Cache metrics dictionary
        """
        if not self.cache_manager:
            return {
                "embedding_cache": {},
                "query_cache": {}
            }
        
        stats = self.cache_manager.get_all_stats()
        
        return {
            "embedding_cache": {
                "size": stats["embedding_cache"]["size"],
                "max_size": stats["embedding_cache"]["max_size"],
                "hit_rate": stats["embedding_cache"]["hit_rate"],
                "hits": stats["embedding_cache"]["hits"],
                "misses": stats["embedding_cache"]["misses"],
                "efficiency": "high" if stats["embedding_cache"]["hit_rate"] > 70 else
                             "medium" if stats["embedding_cache"]["hit_rate"] > 40 else "low"
            },
            "query_cache": {
                "size": stats["query_cache"]["size"],
                "max_size": stats["query_cache"]["max_size"],
                "hit_rate": stats["query_cache"]["hit_rate"],
                "hits": stats["query_cache"]["hits"],
                "misses": stats["query_cache"]["misses"],
                "efficiency": "high" if stats["query_cache"]["hit_rate"] > 50 else
                             "medium" if stats["query_cache"]["hit_rate"] > 25 else "low"
            }
        }
    
    def get_neo4j_metrics(self) -> Dict[str, Any]:
        """
        Get Neo4j performance metrics
        
        Returns:
            Neo4j metrics dictionary
        """
        if not self.neo4j_client:
            return {}
        
        stats = self.neo4j_client.get_performance_stats()
        
        if not stats:
            return {}
        
        avg_duration = stats.get("avg_duration", 0.0)
        max_duration = stats.get("max_duration", 0.0)
        
        return {
            "total_queries": stats.get("total_queries", 0),
            "avg_duration_ms": round(avg_duration * 1000, 2),
            "min_duration_ms": round(stats.get("min_duration", 0.0) * 1000, 2),
            "max_duration_ms": round(max_duration * 1000, 2),
            "query_counts": stats.get("query_counts", {}),
            "error_counts": stats.get("error_counts", {}),
            "error_rate": round(
                sum(stats.get("error_counts", {}).values()) / 
                max(stats.get("total_queries", 1), 1) * 100,
                2
            ),
            "slow_query_count": stats.get("slow_query_count", 0),
            "performance_status": "good" if avg_duration < 0.5 else
                                 "acceptable" if avg_duration < 1.0 else "poor"
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all performance metrics
        
        Returns:
            Complete metrics dictionary
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_metrics": self.get_cache_metrics(),
            "neo4j_metrics": self.get_neo4j_metrics(),
            "system_status": self._get_system_status()
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        
        Returns:
            System status dictionary
        """
        cache_metrics = self.get_cache_metrics()
        neo4j_metrics = self.get_neo4j_metrics()
        
        # Determine overall status
        status = "healthy"
        issues = []
        
        # Check cache efficiency
        embedding_hit_rate = cache_metrics.get("embedding_cache", {}).get("hit_rate", 0)
        query_hit_rate = cache_metrics.get("query_cache", {}).get("hit_rate", 0)
        
        if embedding_hit_rate < 30:
            issues.append("Low embedding cache hit rate")
        
        if query_hit_rate < 20:
            issues.append("Low query cache hit rate")
        
        # Check Neo4j performance
        if neo4j_metrics:
            avg_duration = neo4j_metrics.get("avg_duration_ms", 0)
            error_rate = neo4j_metrics.get("error_rate", 0)
            
            if avg_duration > 1000:
                issues.append("Slow Neo4j queries")
                status = "degraded"
            
            if error_rate > 5:
                issues.append("High Neo4j error rate")
                status = "degraded"
        
        return {
            "status": status,
            "issues": issues,
            "recommendations": self._get_recommendations(cache_metrics, neo4j_metrics)
        }
    
    def _get_recommendations(
        self,
        cache_metrics: Dict[str, Any],
        neo4j_metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Get performance recommendations
        
        Args:
            cache_metrics: Cache metrics
            neo4j_metrics: Neo4j metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Cache recommendations
        embedding_hit_rate = cache_metrics.get("embedding_cache", {}).get("hit_rate", 0)
        if embedding_hit_rate < 40:
            recommendations.append(
                "Consider increasing embedding cache size or TTL to improve hit rate"
            )
        
        query_hit_rate = cache_metrics.get("query_cache", {}).get("hit_rate", 0)
        if query_hit_rate < 25:
            recommendations.append(
                "Consider increasing query cache TTL for frequently accessed queries"
            )
        
        # Neo4j recommendations
        if neo4j_metrics:
            avg_duration = neo4j_metrics.get("avg_duration_ms", 0)
            if avg_duration > 500:
                recommendations.append(
                    "Consider optimizing Neo4j queries or adding indexes for slow queries"
                )
            
            slow_query_count = neo4j_metrics.get("slow_query_count", 0)
            if slow_query_count > 10:
                recommendations.append(
                    "Review slow query log and optimize frequently slow queries"
                )
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get concise performance summary
        
        Returns:
            Performance summary
        """
        all_metrics = self.get_all_metrics()
        
        return {
            "timestamp": all_metrics["timestamp"],
            "system_status": all_metrics["system_status"]["status"],
            "cache_efficiency": {
                "embedding_hit_rate": all_metrics["cache_metrics"]["embedding_cache"].get("hit_rate", 0),
                "query_hit_rate": all_metrics["cache_metrics"]["query_cache"].get("hit_rate", 0)
            },
            "query_performance": {
                "avg_duration_ms": all_metrics["neo4j_metrics"].get("avg_duration_ms", 0),
                "error_rate": all_metrics["neo4j_metrics"].get("error_rate", 0)
            },
            "issues": all_metrics["system_status"]["issues"],
            "recommendations": all_metrics["system_status"]["recommendations"]
        }
