"""Hybrid search service for Phase 5: Vector + Graph search"""

from typing import Dict, Any, List, Optional
from loguru import logger

from src.graph_db.neo4j_client import Neo4jClient
from src.graph_db.edgar_schema import EdgarNeo4jSchema
from src.vector_db.embeddings import EmbeddingPipeline


class HybridSearchService:
    """
    Hybrid search service combining vector similarity and graph traversal
    
    This service enables:
    1. Vector similarity search for semantic matching
    2. Graph traversal for structured queries
    3. Combined hybrid queries for best results
    """
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedding_pipeline: Optional[EmbeddingPipeline] = None
    ):
        """
        Initialize hybrid search service
        
        Args:
            neo4j_client: Neo4j client
            embedding_pipeline: Embedding pipeline for query embeddings
        """
        self.client = neo4j_client
        self.edgar_schema = EdgarNeo4jSchema(neo4j_client)
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()
    
    def search(
        self,
        query: str,
        limit: int = 10,
        company_ticker: Optional[str] = None,
        form_type: Optional[str] = None,
        semantic_type: Optional[str] = None,
        use_vector: bool = True,
        use_graph: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: combine vector and graph search
        
        Args:
            query: Search query text
            limit: Maximum number of results
            company_ticker: Filter by company ticker
            form_type: Filter by form type
            semantic_type: Filter by semantic type
            use_vector: Enable vector similarity search
            use_graph: Enable graph traversal search
            
        Returns:
            List of search results with scores
        """
        results = []
        
        # Vector search
        if use_vector:
            try:
                # Generate query embedding
                query_embedding = self.embedding_pipeline.generate_embedding(query)
                
                if query_embedding:
                    # Get company CIK if ticker provided
                    company_cik = None
                    if company_ticker:
                        company_cik = self._get_company_cik(company_ticker)
                    
                    vector_results = self.edgar_schema.search_chunks_by_vector(
                        query_embedding=query_embedding,
                        limit=limit * 2,  # Get more for merging
                        semantic_type=semantic_type,
                        company_cik=company_cik,
                        form_type=form_type
                    )
                    
                    # Add search type marker
                    for result in vector_results:
                        result["search_type"] = "vector"
                        result["score"] = result.get("similarity_score", 0.0)
                    
                    results.extend(vector_results)
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # Graph search (fallback or complement)
        if use_graph:
            try:
                graph_results = self.edgar_schema.search_chunks_by_graph(
                    company_ticker=company_ticker,
                    form_type=form_type,
                    limit=limit * 2
                )
                
                # Add search type marker and score
                for result in graph_results:
                    result["search_type"] = "graph"
                    result["score"] = 0.5  # Default score for graph results
                
                results.extend(graph_results)
            except Exception as e:
                logger.warning(f"Graph search failed: {e}")
        
        # Merge and deduplicate results
        merged_results = self._merge_results(results, limit)
        
        return merged_results
    
    def _merge_results(
        self,
        results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate search results
        
        Args:
            results: List of search results
            limit: Maximum number of results
            
        Returns:
            Merged and deduplicated results
        """
        # Deduplicate by chunk_id
        seen_chunks = {}
        
        for result in results:
            chunk_id = result.get("chunk_id")
            if not chunk_id:
                continue
            
            # If we've seen this chunk, keep the one with higher score
            if chunk_id in seen_chunks:
                existing_score = seen_chunks[chunk_id].get("score", 0.0)
                new_score = result.get("score", 0.0)
                
                if new_score > existing_score:
                    seen_chunks[chunk_id] = result
            else:
                seen_chunks[chunk_id] = result
        
        # Sort by score and return top results
        merged = list(seen_chunks.values())
        merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return merged[:limit]
    
    def _get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get company CIK by ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Company CIK or None
        """
        query = """
        MATCH (c:Company {ticker: $ticker})
        RETURN c.cik AS cik
        LIMIT 1
        """
        
        try:
            results = self.client.execute_query(query, {"ticker": ticker})
            if results:
                return results[0].get("cik")
        except Exception as e:
            logger.error(f"Error getting CIK for {ticker}: {e}")
        
        return None
    
    def search_by_company_and_topic(
        self,
        company_ticker: str,
        topic: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for specific topic within a company's filings
        
        Args:
            company_ticker: Company ticker symbol
            topic: Topic to search for
            limit: Maximum number of results
            
        Returns:
            List of relevant chunks
        """
        return self.search(
            query=topic,
            limit=limit,
            company_ticker=company_ticker,
            use_vector=True,
            use_graph=True
        )
    
    def search_risk_factors(
        self,
        company_ticker: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for risk factor discussions
        
        Args:
            company_ticker: Filter by company ticker
            limit: Maximum number of results
            
        Returns:
            List of risk factor chunks
        """
        return self.search(
            query="risk factors business risks",
            limit=limit,
            company_ticker=company_ticker,
            semantic_type="risk_discussion",
            use_vector=True,
            use_graph=False
        )
    
    def search_financial_analysis(
        self,
        company_ticker: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for financial analysis discussions
        
        Args:
            company_ticker: Filter by company ticker
            limit: Maximum number of results
            
        Returns:
            List of financial analysis chunks
        """
        return self.search(
            query="financial results revenue earnings",
            limit=limit,
            company_ticker=company_ticker,
            semantic_type="financial_analysis",
            use_vector=True,
            use_graph=False
        )
