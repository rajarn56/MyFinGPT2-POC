"""Chroma vector database client for Phase 4 Knowledge Layer"""

import chromadb
from chromadb.config import Settings
from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class ChromaClient:
    """Chroma vector database client with collection management and search capabilities"""
    
    # Phase 4 collections
    COLLECTION_FINANCIAL_NEWS = "financial_news"
    COLLECTION_COMPANY_ANALYSIS = "company_analysis"
    COLLECTION_CONVERSATION_HISTORY = "conversation_history"
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        """
        Initialize Chroma client
        
        Args:
            host: Chroma server host
            port: Chroma server port
        """
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(allow_reset=True)
        )
        logger.info(f"Connected to Chroma at {host}:{port}")
        
        # Initialize collections on startup
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize Phase 4 collections if they don't exist"""
        collections_to_create = [
            self.COLLECTION_FINANCIAL_NEWS,
            self.COLLECTION_COMPANY_ANALYSIS,
            self.COLLECTION_CONVERSATION_HISTORY,
        ]
        
        for collection_name in collections_to_create:
            try:
                self._get_or_create_collection(collection_name)
            except Exception as e:
                logger.error(f"Failed to initialize collection {collection_name}: {e}")
    
    def _get_or_create_collection(self, name: str):
        """Get existing collection or create if it doesn't exist"""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            # Collection doesn't exist, create it
            collection = self.client.create_collection(name=name)
            logger.info(f"Created collection: {name}")
            return collection
    
    def create_collection(self, name: str, metadata: Optional[Dict] = None):
        """Create a new collection"""
        try:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created collection: {name}")
            return collection
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            raise
    
    def get_collection(self, name: str):
        """Get existing collection"""
        try:
            return self.client.get_collection(name)
        except Exception as e:
            logger.error(f"Error getting collection {name}: {e}")
            raise
    
    def add_document(
        self,
        collection_name: str,
        document: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        document_id: Optional[str] = None
    ) -> str:
        """
        Add a document to a collection
        
        Args:
            collection_name: Name of the collection
            document: Document text content
            metadata: Document metadata
            embedding: Pre-computed embedding (if None, must be computed externally)
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            Document ID
        """
        if document_id is None:
            document_id = str(uuid.uuid4())
        
        collection = self._get_or_create_collection(collection_name)
        
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.utcnow().isoformat()
        
        try:
            if embedding:
                collection.add(
                    ids=[document_id],
                    documents=[document],
                    metadatas=[metadata],
                    embeddings=[embedding]
                )
            else:
                # Chroma will compute embedding if not provided
                collection.add(
                    ids=[document_id],
                    documents=[document],
                    metadatas=[metadata]
                )
            
            logger.debug(f"Added document {document_id} to collection {collection_name}")
            return document_id
        except Exception as e:
            logger.error(f"Error adding document to {collection_name}: {e}")
            raise
    
    def search_similar(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            collection_name: Name of the collection
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter (e.g., {"symbol": "AAPL"})
            
        Returns:
            List of similar documents with metadata and distances
        """
        collection = self._get_or_create_collection(collection_name)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            logger.debug(f"Found {len(formatted_results)} similar documents in {collection_name}")
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {e}")
            raise
    
    def search_by_text(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using query text (Chroma computes embedding)
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of similar documents
        """
        collection = self._get_or_create_collection(collection_name)
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            logger.debug(f"Found {len(formatted_results)} similar documents in {collection_name}")
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {e}")
            raise
    
    def delete_document(self, collection_name: str, document_id: str):
        """Delete a document from a collection"""
        collection = self._get_or_create_collection(collection_name)
        try:
            collection.delete(ids=[document_id])
            logger.debug(f"Deleted document {document_id} from {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection"""
        collection = self._get_or_create_collection(collection_name)
        try:
            count = collection.count()
            return {
                "collection_name": collection_name,
                "document_count": count
            }
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return {"collection_name": collection_name, "document_count": 0}
    
    def health_check(self) -> bool:
        """Check if Chroma is healthy"""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"Chroma health check failed: {e}")
            return False

