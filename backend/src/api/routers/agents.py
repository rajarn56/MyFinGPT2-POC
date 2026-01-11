"""Agent execution API endpoints"""

from fastapi import APIRouter, Header, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid
from loguru import logger

from src.services.session_service import SessionService
from src.services.auth_service import AuthService
from src.services.ingestion_service import IngestionService
from src.orchestrator.workflow import MyFinGPTWorkflow
from src.mcp.mcp_client import MCPClient
from src.agents.research_agent import ResearchAgent
from src.agents.analyst_agent import AnalystAgent
from src.agents.reporting_agent import ReportingAgent
from src.agents.edgar_agent import EdgarAgent
from src.agents.comparison_agent import ComparisonAgent
from src.agents.trend_agent import TrendAgent
from src.graph_db.neo4j_client import Neo4jClient
from src.vector_db.chroma_client import ChromaClient
from src.vector_db.embeddings import EmbeddingPipeline
from src.utils.llm_client import LLMClient
from src.config import settings


router = APIRouter()


class ExecuteRequest(BaseModel):
    """Request model for agent execution"""
    query: str
    symbols: List[str]


def get_session_service() -> SessionService:
    """Dependency for session service"""
    return SessionService()


def get_auth_service() -> AuthService:
    """Dependency for auth service"""
    return AuthService()


def get_ingestion_service() -> IngestionService:
    """Dependency for ingestion service (Phase 4)"""
    return IngestionService()


def get_workflow() -> MyFinGPTWorkflow:
    """
    Dependency for workflow
    - Phase 3: includes Analyst and Reporting agents
    - Phase 4: knowledge layer
    - Phase 5: EDGAR agent
    - Phase 6: Comparison and Trend agents with conditional routing
    """
    mcp_client = MCPClient()
    
    # Phase 4: Initialize ingestion service for knowledge layer
    ingestion_service = get_ingestion_service()
    
    # Phase 4: Pass ingestion service to Research Agent
    research_agent = ResearchAgent(mcp_client, ingestion_service=ingestion_service)
    
    # Phase 3: Add Analyst and Reporting agents
    llm_client = LLMClient()
    analyst_agent = AnalystAgent(llm_client)
    
    # Phase 4: Pass ingestion service to Reporting Agent
    reporting_agent = ReportingAgent(llm_client, ingestion_service=ingestion_service)
    
    # Phase 5: Initialize EDGAR Agent
    edgar_agent = None
    try:
        neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        embedding_pipeline = EmbeddingPipeline()
        edgar_agent = EdgarAgent(neo4j_client, embedding_pipeline)
        logger.info("EDGAR Agent initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize EDGAR Agent: {e}")
        logger.warning("EDGAR functionality will be disabled")
    
    # Phase 6: Initialize Comparison and Trend agents
    comparison_agent = None
    trend_agent = None
    try:
        chroma_client = ChromaClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        comparison_agent = ComparisonAgent(llm_client, chroma_client=chroma_client)
        trend_agent = TrendAgent(llm_client, chroma_client=chroma_client)
        logger.info("Comparison and Trend agents initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize Comparison/Trend agents: {e}")
        logger.warning("Comparison and Trend functionality will be disabled")
    
    return MyFinGPTWorkflow(
        research_agent=research_agent,
        analyst_agent=analyst_agent,
        reporting_agent=reporting_agent,
        edgar_agent=edgar_agent,  # Phase 5
        comparison_agent=comparison_agent,  # Phase 6
        trend_agent=trend_agent,  # Phase 6
        enable_parallel=True,  # Enable parallel execution for Phase 3
        enable_conditional=True  # Enable conditional routing for Phase 6
    )


def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    return f"txn_{uuid.uuid4().hex[:16]}"


@router.post("/execute")
async def execute_agents(
    request: ExecuteRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    workflow: MyFinGPTWorkflow = Depends(get_workflow)
):
    """
    Execute agent workflow
    
    Args:
        request: Execution request with query and symbols
        x_session_id: Session ID from header
        session_service: Session service dependency
        workflow: Workflow dependency
        
    Returns:
        Execution result with transaction ID and status
    """
    # Validate session
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Update session activity
    session_service.update_activity(x_session_id)
    
    # Generate transaction ID
    transaction_id = generate_transaction_id()
    
    # Create initial state (Phase 3: includes analyst_data and report fields, Phase 5: includes edgar_data, Phase 6: includes comparison_data and trend_analysis)
    now = datetime.utcnow()
    state = {
        "transaction_id": transaction_id,
        "session_id": x_session_id,
        "query": request.query,
        "symbols": request.symbols,
        "research_data": {},
        "analyst_data": {},  # Phase 3
        "report": None,  # Phase 3
        "edgar_data": {},  # Phase 5
        "comparison_data": {},  # Phase 6
        "trend_analysis": {},  # Phase 6
        "query_type": None,  # Phase 6
        "errors": [],
        "token_usage": {},
        "citations": [],
        "created_at": now,
        "updated_at": now
    }
    
    logger.info(f"Executing agent workflow for transaction {transaction_id}")
    
    try:
        # Execute workflow
        result = workflow.execute(state)
        
        # Determine status
        status = "completed"
        if result.get("errors"):
            status = "completed_with_errors"
        
        return {
            "transaction_id": result["transaction_id"],
            "status": status,
            "result": {
                "research_data": result.get("research_data", {}),
                "analyst_data": result.get("analyst_data", {}),  # Phase 3
                "report": result.get("report"),  # Phase 3
                "edgar_data": result.get("edgar_data", {}),  # Phase 5
                "comparison_data": result.get("comparison_data", {}),  # Phase 6
                "trend_analysis": result.get("trend_analysis", {}),  # Phase 6
                "query_type": result.get("query_type"),  # Phase 6
                "citations": result.get("citations", []),
                "errors": result.get("errors", []),
                "token_usage": result.get("token_usage", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
