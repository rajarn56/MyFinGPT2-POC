from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

from src.utils.logging import setup_logging
from src.api.routers import health, auth, agents, knowledge, edgar, websocket, performance
from src.api.middleware.error_handler import error_handler
from src.config import settings
from src.exceptions import MyFinGPTException
from fastapi.exceptions import RequestValidationError
from src.graph_db import Neo4jClient, Neo4jSchema
from src.graph_db.edgar_schema import EdgarNeo4jSchema
from src.vector_db.embeddings import EmbeddingPipeline

# Setup logging first
setup_logging()

app = FastAPI(
    title="MyFinGPT-POC-V2",
    version="0.1.0",
    description="Production-grade multi-agent financial analysis system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])  # Phase 4
app.include_router(edgar.router, prefix="/api/edgar", tags=["edgar"])  # Phase 5
app.include_router(websocket.router, tags=["websocket"])  # Phase 7: WebSocket for progress updates
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])  # Phase 9: Performance monitoring

# Add exception handlers
app.add_exception_handler(MyFinGPTException, error_handler)
app.add_exception_handler(RequestValidationError, error_handler)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting MyFinGPT-POC-V2 backend")
    
    # Phase 4: Initialize Neo4j schema
    try:
        neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        schema = Neo4jSchema(neo4j_client)
        schema.initialize_schema()
        logger.info("Neo4j schema initialized")
        
        # Phase 5: Initialize EDGAR schema
        try:
            embedding_pipeline = EmbeddingPipeline()
            embedding_dimension = embedding_pipeline.get_embedding_dimension()
            edgar_schema = EdgarNeo4jSchema(neo4j_client)
            edgar_schema.initialize_schema(embedding_dimension=embedding_dimension)
            logger.info(f"EDGAR Neo4j schema initialized (embedding dimension: {embedding_dimension})")
        except Exception as e:
            logger.warning(f"Failed to initialize EDGAR schema: {e}")
            logger.warning("EDGAR functionality may be limited")
    except Exception as e:
        logger.warning(f"Failed to initialize Neo4j schema (may not be available): {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MyFinGPT-POC-V2 backend")


if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

