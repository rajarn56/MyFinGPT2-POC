"""LangGraph state model for Phase 2 and Phase 3"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime


def first_value_reducer(left: Any, right: Any) -> Any:
    """
    Reducer for immutable fields: always return the first (left) value.
    Used for fields that should never change during workflow execution.
    """
    return left


class AgentState(TypedDict):
    """
    Shared state structure for LangGraph orchestration (Phase 2-3).
    This is the central context repository for all agents.
    """
    # Query information (immutable fields - use Annotated with reducer)
    transaction_id: Annotated[str, first_value_reducer]  # Unique transaction identifier for this query
    session_id: Annotated[str, first_value_reducer]  # Session identifier
    query: Annotated[str, first_value_reducer]  # Original user query
    symbols: Annotated[List[str], first_value_reducer]  # Stock symbols extracted from query
    
    # Research Agent Output (Phase 2)
    research_data: Dict[str, Any]  # Symbol -> {price, company_info, etc.}
    
    # Analyst Agent Output (Phase 3)
    analyst_data: Dict[str, Any]  # Symbol -> {analysis, sentiment, trends, etc.}
    
    # Reporting Agent Output (Phase 3)
    report: Optional[str]  # Final report in Markdown format
    
    # EDGAR Agent Output (Phase 5)
    edgar_data: Dict[str, Any]  # Symbol -> {company, filings, sections}
    
    # Comparison Agent Output (Phase 6)
    comparison_data: Dict[str, Any]  # Comparison results: {comparison_type, metrics, comparison_table, insights}
    
    # Trend Agent Output (Phase 6)
    trend_analysis: Dict[str, Any]  # Symbol -> {price_trend, trend_strength, pattern_type, trend_prediction, etc.}
    
    # Query intent classification (Phase 6)
    query_type: Optional[str]  # Type of query: "single_entity", "comparison", "trend", "comprehensive", etc.
    
    # Errors
    errors: List[str]  # List of error messages
    
    # Token usage tracking
    token_usage: Dict[str, Any]  # {agent_name: {prompt_tokens, completion_tokens, total_tokens}}
    
    # Citations
    citations: List[Dict[str, str]]  # [{source, symbol, type}]
    
    # Timestamps
    created_at: Annotated[datetime, first_value_reducer]  # Immutable: creation time
    updated_at: datetime  # Mutable: updated by each agent
