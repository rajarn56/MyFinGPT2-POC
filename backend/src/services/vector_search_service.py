"""Vector search service for Phase 4 Knowledge Layer"""

from typing import Dict, Any, List, Optional
from loguru import logger

from src.vector_db import ChromaClient, EmbeddingPipeline
from src.config import settings


class VectorSearchService:
    """Service for semantic search in the knowledge layer"""
    
    def __init__(
        self,
        chroma_client: Optional[ChromaClient] = None,
        embedding_pipeline: Optional[EmbeddingPipeline] = None
    ):
        """
        Initialize vector search service
        
        Args:
            chroma_client: ChromaClient instance (created if not provided)
            embedding_pipeline: EmbeddingPipeline instance (created if not provided)
        """
        self.chroma_client = chroma_client or ChromaClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()
    
    def search_news(
        self,
        query: str,
        symbol: Optional[str] = None,
        n_results: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search financial news articles
        
        Args:
            query: Search query text
            symbol: Filter by stock symbol (optional)
            n_results: Number of results to return
            min_score: Minimum similarity score (optional, filters by distance threshold)
            
        Returns:
            List of matching news articles
        """
        # Generate query embedding
        query_embedding = self.embedding_pipeline.generate_embedding(query)
        
        # Build metadata filter
        where = None
        if symbol:
            where = {"symbol": symbol}
        
        # Search
        results = self.chroma_client.search_similar(
            collection_name=ChromaClient.COLLECTION_FINANCIAL_NEWS,
            query_embedding=query_embedding,
            n_results=n_results,
            where=where
        )
        
        # Filter by minimum score if specified
        if min_score is not None:
            results = [
                r for r in results
                if r.get("distance") is not None and r["distance"] <= (1.0 - min_score)
            ]
        
        logger.debug(f"Found {len(results)} news articles for query: {query[:50]}...")
        return results
    
    def search_analysis_reports(
        self,
        query: str,
        symbols: Optional[List[str]] = None,
        n_results: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search analysis reports
        
        Args:
            query: Search query text
            symbols: Filter by stock symbols (optional)
            n_results: Number of results to return
            min_score: Minimum similarity score (optional)
            
        Returns:
            List of matching analysis reports
        """
        # Generate query embedding
        query_embedding = self.embedding_pipeline.generate_embedding(query)
        
        # Build metadata filter
        where = None
        if symbols:
            # Chroma supports filtering, but for multiple symbols we'd need OR logic
            # For now, search without filter and filter results
            pass
        
        # Search
        results = self.chroma_client.search_similar(
            collection_name=ChromaClient.COLLECTION_COMPANY_ANALYSIS,
            query_embedding=query_embedding,
            n_results=n_results * 2 if symbols else n_results,  # Get more to filter
            where=where
        )
        
        # Filter by symbols if specified
        if symbols:
            symbol_set = set(symbols)
            filtered_results = []
            for result in results:
                result_symbols = result.get("metadata", {}).get("symbols", "")
                result_symbol_list = [s.strip() for s in result_symbols.split(",") if s.strip()]
                if any(s in symbol_set for s in result_symbol_list):
                    filtered_results.append(result)
                if len(filtered_results) >= n_results:
                    break
            results = filtered_results
        
        # Filter by minimum score if specified
        if min_score is not None:
            results = [
                r for r in results
                if r.get("distance") is not None and r["distance"] <= (1.0 - min_score)
            ]
        
        logger.debug(f"Found {len(results)} analysis reports for query: {query[:50]}...")
        return results
    
    def search_conversation_history(
        self,
        query: str,
        session_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search conversation history
        
        Args:
            query: Search query text
            session_id: Filter by session ID (optional)
            n_results: Number of results to return
            
        Returns:
            List of matching conversations
        """
        # Generate query embedding
        query_embedding = self.embedding_pipeline.generate_embedding(query)
        
        # Build metadata filter
        where = None
        if session_id:
            where = {"session_id": session_id}
        
        # Search
        results = self.chroma_client.search_similar(
            collection_name=ChromaClient.COLLECTION_CONVERSATION_HISTORY,
            query_embedding=query_embedding,
            n_results=n_results,
            where=where
        )
        
        logger.debug(f"Found {len(results)} conversations for query: {query[:50]}...")
        return results
    
    def get_relevant_context(
        self,
        query: str,
        symbols: Optional[List[str]] = None,
        include_news: bool = True,
        include_reports: bool = True,
        n_results_per_source: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get relevant context from multiple sources
        
        Args:
            query: Search query
            symbols: Stock symbols to filter by (optional)
            include_news: Include news articles (default: True)
            include_reports: Include analysis reports (default: True)
            n_results_per_source: Number of results per source
            
        Returns:
            Dictionary with 'news' and/or 'reports' keys containing results
        """
        context = {}
        
        if include_news:
            symbol = symbols[0] if symbols else None
            context["news"] = self.search_news(
                query=query,
                symbol=symbol,
                n_results=n_results_per_source
            )
        
        if include_reports:
            context["reports"] = self.search_analysis_reports(
                query=query,
                symbols=symbols,
                n_results=n_results_per_source
            )
        
        return context
