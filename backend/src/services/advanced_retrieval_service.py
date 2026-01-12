"""Advanced retrieval service for Phase 9: Reranking and multi-stage retrieval"""

from typing import Dict, Any, List, Optional
from loguru import logger
import math

from src.services.vector_search_service import VectorSearchService
from src.vector_db import ChromaClient, EmbeddingPipeline


class AdvancedRetrievalService:
    """
    Advanced retrieval service with:
    - Multi-stage retrieval
    - Reranking
    - Result filtering and optimization
    """
    
    def __init__(
        self,
        vector_search_service: Optional[VectorSearchService] = None,
        chroma_client: Optional[ChromaClient] = None,
        embedding_pipeline: Optional[EmbeddingPipeline] = None
    ):
        """
        Initialize advanced retrieval service
        
        Args:
            vector_search_service: VectorSearchService instance
            chroma_client: ChromaClient instance (for direct access)
            embedding_pipeline: EmbeddingPipeline instance
        """
        self.vector_search_service = vector_search_service or VectorSearchService(
            chroma_client=chroma_client,
            embedding_pipeline=embedding_pipeline
        )
        self.chroma_client = chroma_client or self.vector_search_service.chroma_client
        self.embedding_pipeline = embedding_pipeline or self.vector_search_service.embedding_pipeline
    
    def multi_stage_retrieval(
        self,
        query: str,
        collection_name: str,
        initial_k: int = 20,
        final_k: int = 5,
        symbol: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-stage retrieval: retrieve more candidates, then rerank
        
        Args:
            query: Search query
            collection_name: Collection to search
            initial_k: Number of initial candidates to retrieve
            final_k: Number of final results to return
            symbol: Optional symbol filter
            min_score: Minimum similarity score
            
        Returns:
            Reranked and filtered results
        """
        # Stage 1: Retrieve initial candidates
        query_embedding = self.embedding_pipeline.generate_embedding(query)
        
        where = None
        if symbol:
            where = {"symbol": symbol}
        
        candidates = self.chroma_client.search_similar(
            collection_name=collection_name,
            query_embedding=query_embedding,
            n_results=initial_k,
            where=where
        )
        
        logger.debug(f"Multi-stage retrieval: Retrieved {len(candidates)} candidates")
        
        # Stage 2: Rerank candidates
        reranked = self._rerank_results(query, candidates)
        
        # Stage 3: Filter and return top results
        filtered = self._filter_results(reranked, min_score=min_score)
        
        return filtered[:final_k]
    
    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        method: str = "distance_weighted"
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using various strategies
        
        Args:
            query: Original query text
            results: Initial search results
            method: Reranking method ("distance_weighted", "metadata_boost", "hybrid")
            
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        if method == "distance_weighted":
            return self._rerank_by_distance_weighted(query, results)
        elif method == "metadata_boost":
            return self._rerank_by_metadata_boost(query, results)
        elif method == "hybrid":
            return self._rerank_hybrid(query, results)
        else:
            logger.warning(f"Unknown reranking method: {method}, using default")
            return self._rerank_by_distance_weighted(query, results)
    
    def _rerank_by_distance_weighted(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank by distance with recency and relevance weighting
        
        Args:
            query: Query text
            results: Search results
            
        Returns:
            Reranked results
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        scored_results = []
        for result in results:
            score = 0.0
            
            # Base similarity score (inverse distance)
            distance = result.get("distance", 1.0)
            similarity = 1.0 / (1.0 + distance) if distance > 0 else 1.0
            score += similarity * 0.6  # 60% weight on similarity
            
            # Recency boost (if timestamp available)
            metadata = result.get("metadata", {})
            timestamp = metadata.get("timestamp")
            if timestamp:
                try:
                    from datetime import datetime
                    doc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    now = datetime.utcnow()
                    age_days = (now - doc_time.replace(tzinfo=None)).days
                    
                    # Boost recent documents (exponential decay)
                    recency_score = math.exp(-age_days / 30.0)  # 30-day half-life
                    score += recency_score * 0.2  # 20% weight on recency
                except Exception:
                    pass
            
            # Keyword match boost
            document_text = result.get("document", "").lower()
            doc_terms = set(document_text.split())
            matching_terms = query_terms.intersection(doc_terms)
            if matching_terms:
                keyword_score = len(matching_terms) / len(query_terms)
                score += keyword_score * 0.2  # 20% weight on keyword match
            
            scored_results.append({
                **result,
                "rerank_score": score
            })
        
        # Sort by rerank score
        scored_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        
        return scored_results
    
    def _rerank_by_metadata_boost(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank by boosting results with relevant metadata
        
        Args:
            query: Query text
            results: Search results
            
        Returns:
            Reranked results
        """
        query_lower = query.lower()
        
        scored_results = []
        for result in results:
            score = 0.0
            
            # Base similarity
            distance = result.get("distance", 1.0)
            similarity = 1.0 / (1.0 + distance) if distance > 0 else 1.0
            score += similarity * 0.5
            
            # Metadata boosts
            metadata = result.get("metadata", {})
            
            # Symbol match boost
            symbol = metadata.get("symbol", "").lower()
            if symbol and symbol in query_lower:
                score += 0.2
            
            # Source quality boost (if available)
            source = metadata.get("source", "").lower()
            quality_sources = ["sec", "edgar", "yahoo finance", "bloomberg"]
            if any(qs in source for qs in quality_sources):
                score += 0.15
            
            # Type boost (if available)
            doc_type = metadata.get("type", "").lower()
            if "analysis" in doc_type or "report" in doc_type:
                score += 0.1
            
            scored_results.append({
                **result,
                "rerank_score": score
            })
        
        scored_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        
        return scored_results
    
    def _rerank_hybrid(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Hybrid reranking combining multiple strategies
        
        Args:
            query: Query text
            results: Search results
            
        Returns:
            Reranked results
        """
        # Combine distance-weighted and metadata-boosted scores
        distance_weighted = self._rerank_by_distance_weighted(query, results)
        metadata_boosted = self._rerank_by_metadata_boost(query, results)
        
        # Create score map
        score_map = {}
        for result in distance_weighted:
            doc_id = result.get("id")
            if doc_id:
                score_map[doc_id] = {
                    "distance_score": result.get("rerank_score", 0.0),
                    "result": result
                }
        
        for result in metadata_boosted:
            doc_id = result.get("id")
            if doc_id and doc_id in score_map:
                score_map[doc_id]["metadata_score"] = result.get("rerank_score", 0.0)
        
        # Combine scores
        hybrid_results = []
        for doc_id, scores in score_map.items():
            combined_score = (
                scores.get("distance_score", 0.0) * 0.6 +
                scores.get("metadata_score", 0.0) * 0.4
            )
            result = scores["result"]
            result["rerank_score"] = combined_score
            hybrid_results.append(result)
        
        hybrid_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        
        return hybrid_results
    
    def _filter_results(
        self,
        results: List[Dict[str, Any]],
        min_score: Optional[float] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter results by score and limit
        
        Args:
            results: Search results
            min_score: Minimum rerank score threshold
            max_results: Maximum number of results
            
        Returns:
            Filtered results
        """
        filtered = results
        
        # Filter by minimum score
        if min_score is not None:
            filtered = [
                r for r in filtered
                if r.get("rerank_score", 0.0) >= min_score
            ]
        
        # Limit results
        if max_results is not None:
            filtered = filtered[:max_results]
        
        return filtered
    
    def retrieve_with_reranking(
        self,
        query: str,
        collection_name: str,
        n_results: int = 5,
        symbol: Optional[str] = None,
        rerank_method: str = "hybrid",
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank results
        
        Args:
            query: Search query
            collection_name: Collection to search
            n_results: Number of results to return
            symbol: Optional symbol filter
            rerank_method: Reranking method
            min_score: Minimum score threshold
            
        Returns:
            Reranked results
        """
        # Use multi-stage retrieval
        return self.multi_stage_retrieval(
            query=query,
            collection_name=collection_name,
            initial_k=n_results * 4,  # Retrieve 4x for reranking
            final_k=n_results,
            symbol=symbol,
            min_score=min_score
        )
