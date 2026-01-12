"""LangGraph state model for Phase 2 and Phase 3"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from loguru import logger


def first_value_reducer(left: Any, right: Any) -> Any:
    """
    Reducer for immutable fields: always return the first (left) value.
    Used for fields that should never change during workflow execution.
    
    However, if left is empty/None and right has a value, prefer right.
    This handles the case where LangGraph initializes an empty state first.
    """
    # If left is None, empty string, or empty list, and right has a value, use right
    # This handles initial state setup where LangGraph might create empty state first
    if left is None:
        logger.debug(f"first_value_reducer: Replacing None with {right}")
        return right
    if isinstance(left, str) and left == "" and right:
        logger.debug(f"first_value_reducer: Replacing empty string with '{right}'")
        return right
    if isinstance(left, list) and len(left) == 0 and right and len(right) > 0:
        logger.debug(f"first_value_reducer: Replacing empty list with {right}")
        return right
    # Otherwise, return left to maintain immutability once set
    return left


def dict_merge_reducer(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reducer for dictionary fields: merge dictionaries, with right values taking precedence.
    Used for mutable dictionary fields that can be updated by multiple nodes.
    """
    result = left.copy() if left else {}
    if right:
        result.update(right)
    return result


def list_extend_reducer(left: List[Any], right: List[Any]) -> List[Any]:
    """
    Reducer for list fields: extend left list with right list, removing duplicates.
    Used for mutable list fields that can be updated by multiple nodes.
    """
    result = (left.copy() if left else [])
    if right:
        # Add items from right that aren't already in left
        for item in right:
            if item not in result:
                result.append(item)
    return result


def latest_datetime_reducer(left: datetime, right: datetime) -> datetime:
    """
    Reducer for datetime fields: return the latest (most recent) datetime.
    Used for updated_at field that can be updated by multiple nodes.
    """
    if not left:
        return right
    if not right:
        return left
    return max(left, right)


def optional_string_reducer(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """
    Reducer for optional string fields: prefer non-None value, otherwise take first.
    Used for fields like report and query_type that can be set by multiple nodes.
    """
    # Prefer non-None value
    if right is not None:
        return right
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
    
    # Research Agent Output (Phase 2) - can be read by multiple agents in parallel
    research_data: Annotated[Dict[str, Any], dict_merge_reducer]  # Symbol -> {price, company_info, etc.}
    
    # Analyst Agent Output (Phase 3) - can be read by multiple agents in parallel
    analyst_data: Annotated[Dict[str, Any], dict_merge_reducer]  # Symbol -> {analysis, sentiment, trends, etc.}
    
    # Reporting Agent Output (Phase 3) - can be set by reporting agent after parallel nodes merge
    report: Annotated[Optional[str], optional_string_reducer]  # Final report in Markdown format
    
    # EDGAR Agent Output (Phase 5)
    edgar_data: Annotated[Dict[str, Any], dict_merge_reducer]  # Symbol -> {company, filings, sections}
    
    # Comparison Agent Output (Phase 6) - updated by comparison agent
    comparison_data: Annotated[Dict[str, Any], dict_merge_reducer]  # Comparison results: {comparison_type, metrics, comparison_table, insights}
    
    # Trend Agent Output (Phase 6) - updated by trend agent
    trend_analysis: Annotated[Dict[str, Any], dict_merge_reducer]  # Symbol -> {price_trend, trend_strength, pattern_type, trend_prediction, etc.}
    
    # Query intent classification (Phase 6) - can be set by route_advanced node or query parser
    query_type: Annotated[Optional[str], optional_string_reducer]  # Type of query: "single_entity", "comparison", "trend", "comprehensive", etc.
    
    # Intent flags from query parser (Phase 7) - can be set by query parser or route_advanced node
    intent_flags: Annotated[Dict[str, Any], dict_merge_reducer]  # Intent flags: is_comparison, is_trend, is_edgar, etc.
    
    # Entities extracted from query (Phase 7) - can be set by query parser
    entities: Annotated[Dict[str, Any], dict_merge_reducer]  # Extracted entities: timeframes, metrics, filing_types, etc.
    
    # Errors - can be updated by multiple agents in parallel
    errors: Annotated[List[str], list_extend_reducer]  # List of error messages
    
    # Token usage tracking - can be updated by multiple agents in parallel
    token_usage: Annotated[Dict[str, Any], dict_merge_reducer]  # {agent_name: {prompt_tokens, completion_tokens, total_tokens}}
    
    # Citations - can be updated by multiple agents in parallel
    citations: Annotated[List[Dict[str, str]], list_extend_reducer]  # [{source, symbol, type}]
    
    # Timestamps
    created_at: Annotated[datetime, first_value_reducer]  # Immutable: creation time
    updated_at: Annotated[datetime, latest_datetime_reducer]  # Mutable: updated by each agent (take latest)
