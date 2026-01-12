"""Performance metrics API endpoint for Phase 9"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.services.performance_monitor import PerformanceMonitor
from src.utils.cache import CacheManager
from src.graph_db.optimized_neo4j_client import OptimizedNeo4jClient
from src.config import settings


router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance"""
    return CacheManager(
        embedding_cache_size=settings.EMBEDDING_CACHE_SIZE,
        embedding_ttl_hours=settings.EMBEDDING_CACHE_TTL_HOURS,
        query_cache_size=settings.QUERY_CACHE_SIZE,
        query_ttl_hours=settings.QUERY_CACHE_TTL_HOURS
    )


def get_performance_monitor(
    cache_manager: CacheManager = Depends(get_cache_manager)
) -> PerformanceMonitor:
    """Get performance monitor instance"""
    # Note: Neo4j client would be injected if available
    return PerformanceMonitor(cache_manager=cache_manager)


@router.get("/metrics")
async def get_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
) -> Dict[str, Any]:
    """
    Get all performance metrics
    
    Returns:
        Complete performance metrics
    """
    return monitor.get_all_metrics()


@router.get("/metrics/summary")
async def get_metrics_summary(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
) -> Dict[str, Any]:
    """
    Get performance summary
    
    Returns:
        Concise performance summary
    """
    return monitor.get_performance_summary()


@router.get("/metrics/cache")
async def get_cache_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
) -> Dict[str, Any]:
    """
    Get cache performance metrics
    
    Returns:
        Cache metrics
    """
    return monitor.get_cache_metrics()


@router.get("/metrics/neo4j")
async def get_neo4j_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
) -> Dict[str, Any]:
    """
    Get Neo4j performance metrics
    
    Returns:
        Neo4j metrics
    """
    return monitor.get_neo4j_metrics()
