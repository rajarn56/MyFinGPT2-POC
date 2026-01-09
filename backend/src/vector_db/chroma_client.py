import chromadb
from chromadb.config import Settings
from loguru import logger
from typing import List, Dict, Any, Optional


class ChromaClient:
    def __init__(self, host: str = "localhost", port: int = 8001):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(allow_reset=True)
        )
        logger.info(f"Connected to Chroma at {host}:{port}")
    
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
    
    def health_check(self) -> bool:
        """Check if Chroma is healthy"""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"Chroma health check failed: {e}")
            return False

