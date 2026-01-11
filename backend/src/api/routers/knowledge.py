"""Knowledge Layer API endpoints for Phase 4"""

from fastapi import APIRouter, Header, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger

from src.services.session_service import SessionService
from src.services.vector_search_service import VectorSearchService
from src.services.ingestion_service import IngestionService
from src.graph_db import Neo4jClient, Neo4jSchema
from src.config import settings


router = APIRouter()


class NewsArticleRequest(BaseModel):
    """Request model for news article ingestion"""
    title: str
    content: str
    symbol: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


def get_session_service() -> SessionService:
    """Dependency for session service"""
    return SessionService()


def get_vector_search_service() -> VectorSearchService:
    """Dependency for vector search service"""
    return VectorSearchService()


def get_ingestion_service() -> IngestionService:
    """Dependency for ingestion service"""
    return IngestionService()


def get_neo4j_client() -> Neo4jClient:
    """Dependency for Neo4j client"""
    return Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )


@router.get("/search/news")
async def search_news(
    query: str = Query(..., description="Search query"),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    n_results: int = Query(5, description="Number of results"),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Search financial news articles
    
    Args:
        query: Search query text
        symbol: Filter by stock symbol (optional)
        n_results: Number of results to return
        x_session_id: Session ID
        session_service: Session service
        search_service: Vector search service
        
    Returns:
        List of matching news articles
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    try:
        results = search_service.search_news(
            query=query,
            symbol=symbol,
            n_results=n_results
        )
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/reports")
async def search_reports(
    query: str = Query(..., description="Search query"),
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    n_results: int = Query(5, description="Number of results"),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    search_service: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Search analysis reports
    
    Args:
        query: Search query text
        symbols: Comma-separated list of symbols to filter by (optional)
        n_results: Number of results to return
        x_session_id: Session ID
        session_service: Session service
        search_service: Vector search service
        
    Returns:
        List of matching analysis reports
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    try:
        symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None
        results = search_service.search_analysis_reports(
            query=query,
            symbols=symbol_list,
            n_results=n_results
        )
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching reports: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/ingest/news")
async def ingest_news(
    request: NewsArticleRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    ingestion_service: IngestionService = Depends(get_ingestion_service)
):
    """
    Ingest a news article into the knowledge layer
    
    Args:
        request: News article data
        x_session_id: Session ID
        session_service: Session service
        ingestion_service: Ingestion service
        
    Returns:
        Document ID
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    try:
        doc_id = ingestion_service.ingest_news_article(
            title=request.title,
            content=request.content,
            symbol=request.symbol,
            source=request.source,
            url=request.url
        )
        return {
            "document_id": doc_id,
            "status": "ingested"
        }
    except Exception as e:
        logger.error(f"Error ingesting news: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/collections/stats")
async def get_collection_stats(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Get statistics for all collections
    
    Args:
        x_session_id: Session ID
        session_service: Session service
        
    Returns:
        Collection statistics
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    from src.vector_db import ChromaClient
    
    chroma_client = ChromaClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT
    )
    
    collections = [
        ChromaClient.COLLECTION_FINANCIAL_NEWS,
        ChromaClient.COLLECTION_COMPANY_ANALYSIS,
        ChromaClient.COLLECTION_CONVERSATION_HISTORY,
    ]
    
    stats = {}
    for collection_name in collections:
        stats[collection_name] = chroma_client.get_collection_stats(collection_name)
    
    return {
        "collections": stats
    }
