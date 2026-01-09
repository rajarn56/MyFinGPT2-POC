from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict

from src.vector_db import ChromaClient
from src.graph_db import Neo4jClient
from src.config import settings

router = APIRouter()


def get_chroma_client() -> ChromaClient:
    return ChromaClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)


def get_neo4j_client() -> Neo4jClient:
    return Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )


@router.get("/")
async def health_check(
    chroma: ChromaClient = Depends(get_chroma_client),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
) -> Dict:
    """Health check endpoint"""
    chroma_healthy = chroma.health_check()
    neo4j_healthy = neo4j.health_check()
    
    status = "healthy" if (chroma_healthy and neo4j_healthy) else "unhealthy"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "chroma": "connected" if chroma_healthy else "disconnected",
            "neo4j": "connected" if neo4j_healthy else "disconnected"
        }
    }

