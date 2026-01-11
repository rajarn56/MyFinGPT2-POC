"""Ingestion service for Phase 4 Knowledge Layer"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from src.vector_db import ChromaClient, EmbeddingPipeline
from src.config import settings


class IngestionService:
    """Service for ingesting data into the knowledge layer"""
    
    def __init__(
        self,
        chroma_client: Optional[ChromaClient] = None,
        embedding_pipeline: Optional[EmbeddingPipeline] = None
    ):
        """
        Initialize ingestion service
        
        Args:
            chroma_client: ChromaClient instance (created if not provided)
            embedding_pipeline: EmbeddingPipeline instance (created if not provided)
        """
        self.chroma_client = chroma_client or ChromaClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()
    
    def ingest_news_article(
        self,
        title: str,
        content: str,
        symbol: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest a news article into the financial_news collection
        
        Args:
            title: Article title
            content: Article content/text
            symbol: Stock symbol (optional)
            source: News source (optional)
            url: Article URL (optional)
            published_at: Publication timestamp (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Document ID
        """
        # Combine title and content for embedding
        full_text = f"{title}\n\n{content}"
        
        # Generate embedding
        embedding = self.embedding_pipeline.generate_embedding(full_text)
        
        # Prepare metadata
        article_metadata = {
            "title": title,
            "symbol": symbol or "",
            "source": source or "unknown",
            "url": url or "",
            "published_at": published_at.isoformat() if published_at else datetime.utcnow().isoformat(),
            "type": "news_article",
            **(metadata or {})
        }
        
        # Add to Chroma
        doc_id = self.chroma_client.add_document(
            collection_name=ChromaClient.COLLECTION_FINANCIAL_NEWS,
            document=full_text,
            metadata=article_metadata,
            embedding=embedding
        )
        
        logger.info(f"Ingested news article: {title[:50]}... (ID: {doc_id})")
        return doc_id
    
    def ingest_analysis_report(
        self,
        report_content: str,
        symbols: List[str],
        query_type: Optional[str] = None,
        session_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest an analysis report into the company_analysis collection
        
        Args:
            report_content: Full report text content
            symbols: List of stock symbols analyzed
            query_type: Type of query/analysis (optional)
            session_id: Session ID (optional)
            transaction_id: Transaction ID (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Document ID
        """
        # Generate embedding
        embedding = self.embedding_pipeline.generate_embedding(report_content)
        
        # Prepare metadata
        report_metadata = {
            "symbols": ",".join(symbols),
            "symbol_count": len(symbols),
            "query_type": query_type or "general",
            "session_id": session_id or "",
            "transaction_id": transaction_id or "",
            "report_length": len(report_content),
            "type": "analysis_report",
            **(metadata or {})
        }
        
        # Add to Chroma
        doc_id = self.chroma_client.add_document(
            collection_name=ChromaClient.COLLECTION_COMPANY_ANALYSIS,
            document=report_content,
            metadata=report_metadata,
            embedding=embedding
        )
        
        logger.info(f"Ingested analysis report for {symbols} (ID: {doc_id})")
        return doc_id
    
    def ingest_conversation(
        self,
        user_message: str,
        agent_response: str,
        session_id: str,
        symbols: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest a conversation exchange into the conversation_history collection
        
        Args:
            user_message: User's message
            agent_response: Agent's response
            session_id: Session ID
            symbols: List of symbols mentioned (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Document ID
        """
        # Combine user message and agent response
        conversation_text = f"User: {user_message}\n\nAgent: {agent_response}"
        
        # Generate embedding
        embedding = self.embedding_pipeline.generate_embedding(conversation_text)
        
        # Prepare metadata
        conversation_metadata = {
            "session_id": session_id,
            "symbols": ",".join(symbols) if symbols else "",
            "user_message_length": len(user_message),
            "agent_response_length": len(agent_response),
            "type": "conversation",
            **(metadata or {})
        }
        
        # Add to Chroma
        doc_id = self.chroma_client.add_document(
            collection_name=ChromaClient.COLLECTION_CONVERSATION_HISTORY,
            document=conversation_text,
            metadata=conversation_metadata,
            embedding=embedding
        )
        
        logger.debug(f"Ingested conversation for session {session_id} (ID: {doc_id})")
        return doc_id
    
    def batch_ingest_news(
        self,
        articles: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Batch ingest multiple news articles
        
        Args:
            articles: List of article dictionaries with keys: title, content, symbol, source, url, published_at
            
        Returns:
            List of document IDs
        """
        doc_ids = []
        for article in articles:
            try:
                doc_id = self.ingest_news_article(
                    title=article.get("title", ""),
                    content=article.get("content", ""),
                    symbol=article.get("symbol"),
                    source=article.get("source"),
                    url=article.get("url"),
                    published_at=article.get("published_at"),
                    metadata=article.get("metadata")
                )
                doc_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Error ingesting article: {e}")
        
        logger.info(f"Batch ingested {len(doc_ids)}/{len(articles)} articles")
        return doc_ids
