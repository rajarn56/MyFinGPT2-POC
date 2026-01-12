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
from src.services.progress_manager import progress_manager
from src.services.vector_search_service import VectorSearchService
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
from src.utils.query_parser import QueryParser
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


def get_query_parser() -> QueryParser:
    """Dependency for query parser"""
    llm_client = LLMClient()
    return QueryParser(llm_client=llm_client)


def get_vector_search_service() -> VectorSearchService:
    """Dependency for vector search service"""
    chroma_client = ChromaClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT
    )
    embedding_pipeline = EmbeddingPipeline()
    return VectorSearchService(chroma_client, embedding_pipeline)


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
    
    # Initialize query parser for workflow
    llm_client = LLMClient()
    query_parser = QueryParser(llm_client=llm_client)
    
    return MyFinGPTWorkflow(
        research_agent=research_agent,
        analyst_agent=analyst_agent,
        reporting_agent=reporting_agent,
        edgar_agent=edgar_agent,  # Phase 5
        comparison_agent=comparison_agent,  # Phase 6
        trend_agent=trend_agent,  # Phase 6
        enable_parallel=True,  # Enable parallel execution for Phase 3
        enable_conditional=True,  # Enable conditional routing for Phase 6
        query_parser=query_parser  # Pass query parser to workflow
    )


def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    return f"txn_{uuid.uuid4().hex[:16]}"


@router.post("/execute")
async def execute_agents(
    request: ExecuteRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    session_service: SessionService = Depends(get_session_service),
    workflow: MyFinGPTWorkflow = Depends(get_workflow),
    query_parser: QueryParser = Depends(get_query_parser),
    vector_search: VectorSearchService = Depends(get_vector_search_service)
):
    """
    Execute agent workflow
    
    Args:
        request: Execution request with query and symbols
        x_session_id: Session ID from header
        session_service: Session service dependency
        workflow: Workflow dependency
        query_parser: Query parser dependency
        vector_search: Vector search service dependency
        
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
    
    # Step 1: Retrieve conversation context for follow-up queries
    conversation_context = None
    try:
        # Search for recent conversation history for this session
        recent_conversations = vector_search.search_conversation_history(
            query=request.query,
            session_id=x_session_id,
            n_results=3
        )
        if recent_conversations:
            # Combine recent conversations into context
            conversation_context = "\n".join([
                conv.get("document", "") for conv in recent_conversations[:2]
            ])
            logger.info(f"Retrieved conversation context for session {x_session_id} ({len(recent_conversations)} conversations)")
    except Exception as e:
        logger.warning(f"Failed to retrieve conversation context: {e}")
        # Continue without context
    
    # Step 2: Parse query to extract symbols, intent, and entities
    logger.info(f"Parsing query: {request.query[:100]}...")
    parsed_result = query_parser.parse(
        query=request.query,
        conversation_context=conversation_context
    )
    
    # Extract parsed information
    extracted_symbols = parsed_result.get("symbols", [])
    parsed_intent_type = parsed_result.get("intent_type", "analysis")
    parsed_intent_flags = parsed_result.get("intent_flags", {})
    parsed_entities = parsed_result.get("entities", {})
    extraction_method = parsed_result.get("extraction_method", "unknown")
    needs_clarification = parsed_result.get("needs_clarification", False)
    
    # Use extracted symbols if frontend didn't provide them or if extraction found more
    final_symbols = extracted_symbols if extracted_symbols else request.symbols
    
    # Log extraction results
    logger.info(
        f"Query parsing completed: method={extraction_method}, "
        f"symbols={final_symbols}, intent={parsed_intent_type}, "
        f"entities={parsed_entities}, needs_clarification={needs_clarification}"
    )
    
    # Handle clarification requests
    if needs_clarification and not final_symbols:
        clarification_question = parsed_result.get("clarification_question", "Please provide a stock symbol or company name to analyze.")
        return {
            "transaction_id": transaction_id,
            "status": "needs_clarification",
            "clarification_question": clarification_question,
            "result": {
                "query": request.query,
                "extracted_symbols": extracted_symbols,
                "extraction_method": extraction_method
            }
        }
    
    # Create initial state (Phase 3: includes analyst_data and report fields, Phase 5: includes edgar_data, Phase 6: includes comparison_data and trend_analysis)
    # IMPORTANT: Ensure all fields match AgentState TypedDict exactly
    now = datetime.utcnow()
    state = {
        "transaction_id": transaction_id,
        "session_id": x_session_id,
        "query": request.query,
        "symbols": final_symbols if final_symbols else [],  # Ensure it's a list, not None
        "research_data": {},
        "analyst_data": {},  # Phase 3
        "report": None,  # Phase 3
        "edgar_data": {},  # Phase 5
        "comparison_data": {},  # Phase 6
        "trend_analysis": {},  # Phase 6
        "query_type": parsed_intent_type,  # Use parsed intent type
        "intent_flags": parsed_intent_flags if parsed_intent_flags else {},  # Ensure it's a dict
        "entities": parsed_entities if parsed_entities else {},  # Ensure it's a dict
        "errors": [],
        "token_usage": {},
        "citations": [],
        "created_at": now,
        "updated_at": now
    }
    
    # Validate state before passing to workflow
    logger.info(
        f"Created initial state for transaction {transaction_id}: "
        f"query='{request.query}', symbols={final_symbols}, intent={parsed_intent_type}, "
        f"state_keys={list(state.keys())}, "
        f"symbols_type={type(state['symbols'])}, symbols_value={state['symbols']}"
    )
    
    # Ensure symbols is a list (not None, not empty string)
    if not isinstance(state["symbols"], list):
        logger.error(f"symbols is not a list! Type: {type(state['symbols'])}, Value: {state['symbols']}")
        state["symbols"] = []
    
    logger.info(
        f"Executing agent workflow for transaction {transaction_id}: "
        f"query='{request.query}', symbols={final_symbols}, intent={parsed_intent_type}"
    )
    
    # Phase 7: Create progress tracker for WebSocket updates
    progress_tracker = progress_manager.create_tracker(x_session_id, transaction_id)
    
    # Final validation before executing workflow
    logger.info(
        f"Final state validation before workflow execution - "
        f"transaction_id={state.get('transaction_id')}, "
        f"query='{state.get('query', '')}', "
        f"symbols={state.get('symbols', [])}, "
        f"symbols_type={type(state.get('symbols'))}, "
        f"all_keys={list(state.keys())}"
    )
    
    # Ensure critical fields are present and correct type
    if not state.get("transaction_id"):
        raise ValueError(f"Missing transaction_id in state! Keys: {list(state.keys())}")
    if not state.get("query"):
        raise ValueError(f"Missing query in state! Keys: {list(state.keys())}")
    if not isinstance(state.get("symbols"), list):
        logger.error(f"symbols is not a list! Type: {type(state.get('symbols'))}, Value: {state.get('symbols')}")
        state["symbols"] = []
    
    try:
        # Execute workflow with progress tracking
        result = workflow.execute(state, progress_tracker=progress_tracker)
        
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
    finally:
        # Phase 7: Clean up progress tracker
        progress_manager.cleanup_tracker(transaction_id)