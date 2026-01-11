"""EDGAR and hybrid search API endpoints (Phase 5)"""

from fastapi import APIRouter, Header, Depends, HTTPException, Query
from typing import List, Optional
from loguru import logger

from src.services.session_service import SessionService
from src.services.hybrid_search_service import HybridSearchService
from src.graph_db.neo4j_client import Neo4jClient
from src.vector_db.embeddings import EmbeddingPipeline
from src.config import settings


router = APIRouter()


def get_session_service() -> SessionService:
    """Dependency for session service"""
    return SessionService()


def get_hybrid_search_service() -> HybridSearchService:
    """Dependency for hybrid search service"""
    try:
        neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        embedding_pipeline = EmbeddingPipeline()
        return HybridSearchService(neo4j_client, embedding_pipeline)
    except Exception as e:
        logger.error(f"Failed to initialize hybrid search service: {e}")
        raise HTTPException(status_code=500, detail="Hybrid search service unavailable")


@router.get("/search")
async def hybrid_search(
    query: str = Query(..., description="Search query text"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    company_ticker: Optional[str] = Query(None, description="Filter by company ticker"),
    form_type: Optional[str] = Query(None, description="Filter by form type (10-K, 10-Q, etc.)"),
    semantic_type: Optional[str] = Query(None, description="Filter by semantic type"),
    use_vector: bool = Query(True, description="Enable vector similarity search"),
    use_graph: bool = Query(True, description="Enable graph traversal search"),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    search_service: HybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Hybrid search: combine vector similarity and graph traversal
    
    Args:
        query: Search query text
        limit: Maximum number of results
        company_ticker: Filter by company ticker
        form_type: Filter by form type
        semantic_type: Filter by semantic type
        use_vector: Enable vector similarity search
        use_graph: Enable graph traversal search
        x_session_id: Session ID from header
        session_service: Session service dependency
        search_service: Hybrid search service dependency
        
    Returns:
        Search results with chunks and metadata
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Update session activity
    session_service.update_activity(x_session_id)
    
    try:
        results = search_service.search(
            query=query,
            limit=limit,
            company_ticker=company_ticker,
            form_type=form_type,
            semantic_type=semantic_type,
            use_vector=use_vector,
            use_graph=use_graph
        )
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/risk-factors")
async def search_risk_factors(
    company_ticker: Optional[str] = Query(None, description="Filter by company ticker"),
    limit: int = Query(10, ge=1, le=100),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    search_service: HybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Search for risk factor discussions
    
    Args:
        company_ticker: Filter by company ticker
        limit: Maximum number of results
        x_session_id: Session ID from header
        session_service: Session service dependency
        search_service: Hybrid search service dependency
        
    Returns:
        Risk factor chunks
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    session_service.update_activity(x_session_id)
    
    try:
        results = search_service.search_risk_factors(
            company_ticker=company_ticker,
            limit=limit
        )
        
        return {
            "query_type": "risk_factors",
            "results_count": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error searching risk factors: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/financial-analysis")
async def search_financial_analysis(
    company_ticker: Optional[str] = Query(None, description="Filter by company ticker"),
    limit: int = Query(10, ge=1, le=100),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    search_service: HybridSearchService = Depends(get_hybrid_search_service)
):
    """
    Search for financial analysis discussions
    
    Args:
        company_ticker: Filter by company ticker
        limit: Maximum number of results
        x_session_id: Session ID from header
        session_service: Session service dependency
        search_service: Hybrid search service dependency
        
    Returns:
        Financial analysis chunks
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    session_service.update_activity(x_session_id)
    
    try:
        results = search_service.search_financial_analysis(
            company_ticker=company_ticker,
            limit=limit
        )
        
        return {
            "query_type": "financial_analysis",
            "results_count": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error searching financial analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
