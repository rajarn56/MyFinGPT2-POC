"""Context merging utilities for Phase 3"""

from typing import Dict, Any, List
from loguru import logger


class ContextMerger:
    """Utility for merging context from parallel agent executions"""
    
    @staticmethod
    def merge_research_data(states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge research data from multiple parallel executions
        
        Args:
            states: List of AgentState dictionaries from parallel Research Agent executions
            
        Returns:
            Merged research_data dictionary
        """
        merged = {}
        
        for state in states:
            research_data = state.get("research_data", {})
            for symbol, data in research_data.items():
                if symbol not in merged:
                    merged[symbol] = data
                else:
                    # Merge data, preferring newer or more complete data
                    merged[symbol] = ContextMerger._merge_symbol_data(
                        merged[symbol], data
                    )
        
        logger.debug(f"Merged research data for {len(merged)} symbols")
        return merged
    
    @staticmethod
    def _merge_symbol_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge data for a single symbol
        
        Args:
            existing: Existing symbol data
            new: New symbol data
            
        Returns:
            Merged symbol data
        """
        merged = existing.copy()
        
        # Merge price data
        if "price" in new and "price" in existing:
            # Prefer data with more fields or newer timestamp
            if len(new.get("price", {})) > len(existing.get("price", {})):
                merged["price"] = new["price"]
        elif "price" in new:
            merged["price"] = new["price"]
        
        # Merge company info
        if "company_info" in new and "company_info" in existing:
            # Merge dictionaries, preferring non-empty values
            merged_company_info = existing["company_info"].copy()
            for key, value in new["company_info"].items():
                if value and (key not in merged_company_info or not merged_company_info[key]):
                    merged_company_info[key] = value
            merged["company_info"] = merged_company_info
        elif "company_info" in new:
            merged["company_info"] = new["company_info"]
        
        # Update timestamp to most recent
        if "timestamp" in new:
            merged["timestamp"] = new["timestamp"]
        
        # Merge sources
        if "source" in new:
            if "source" in existing:
                if isinstance(existing["source"], list):
                    if new["source"] not in existing["source"]:
                        merged["source"] = existing["source"] + [new["source"]]
                    else:
                        merged["source"] = existing["source"]
                else:
                    merged["source"] = [existing["source"], new["source"]]
            else:
                merged["source"] = new["source"]
        
        return merged
    
    @staticmethod
    def merge_analyst_data(states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge analyst data from multiple parallel executions
        
        Args:
            states: List of AgentState dictionaries from parallel Analyst Agent executions
            
        Returns:
            Merged analyst_data dictionary
        """
        merged = {}
        
        for state in states:
            analyst_data = state.get("analyst_data", {})
            for symbol, data in analyst_data.items():
                if symbol not in merged:
                    merged[symbol] = data
                else:
                    # For analyst data, prefer more detailed analysis
                    if len(data.get("raw_content", "")) > len(merged[symbol].get("raw_content", "")):
                        merged[symbol] = data
        
        logger.debug(f"Merged analyst data for {len(merged)} symbols")
        return merged
    
    @staticmethod
    def merge_citations(states: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Merge citations from multiple states
        
        Args:
            states: List of AgentState dictionaries
            
        Returns:
            Merged citations list (deduplicated)
        """
        citations = []
        seen = set()
        
        for state in states:
            state_citations = state.get("citations", [])
            for citation in state_citations:
                # Create a unique key for deduplication
                citation_key = (
                    citation.get("source", ""),
                    citation.get("symbol", ""),
                    citation.get("type", "")
                )
                if citation_key not in seen:
                    seen.add(citation_key)
                    citations.append(citation)
        
        logger.debug(f"Merged {len(citations)} unique citations")
        return citations
    
    @staticmethod
    def merge_errors(states: List[Dict[str, Any]]) -> List[str]:
        """
        Merge errors from multiple states
        
        Args:
            states: List of AgentState dictionaries
            
        Returns:
            Merged errors list (deduplicated)
        """
        errors = []
        seen = set()
        
        for state in states:
            state_errors = state.get("errors", [])
            for error in state_errors:
                if error not in seen:
                    seen.add(error)
                    errors.append(error)
        
        return errors
    
    @staticmethod
    def merge_token_usage(states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge token usage from multiple states
        
        Args:
            states: List of AgentState dictionaries
            
        Returns:
            Merged token_usage dictionary
        """
        merged = {}
        
        for state in states:
            token_usage = state.get("token_usage", {})
            for agent_name, usage in token_usage.items():
                if agent_name not in merged:
                    merged[agent_name] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                
                if isinstance(usage, dict):
                    merged[agent_name]["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    merged[agent_name]["completion_tokens"] += usage.get("completion_tokens", 0)
                    merged[agent_name]["total_tokens"] += usage.get("total_tokens", 0)
        
        return merged
    
    @staticmethod
    def merge_comparison_data(states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge comparison data from multiple states (Phase 6)
        
        Args:
            states: List of AgentState dictionaries
            
        Returns:
            Merged comparison_data dictionary
        """
        merged = {}
        
        for state in states:
            comparison_data = state.get("comparison_data", {})
            if comparison_data:
                # For comparison data, prefer the most complete/comprehensive result
                if not merged or len(str(comparison_data)) > len(str(merged)):
                    merged = comparison_data
        
        logger.debug(f"Merged comparison data: {len(merged)} keys")
        return merged
    
    @staticmethod
    def merge_trend_analysis(states: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge trend analysis from multiple states (Phase 6)
        
        Args:
            states: List of AgentState dictionaries
            
        Returns:
            Merged trend_analysis dictionary
        """
        merged = {}
        
        for state in states:
            trend_analysis = state.get("trend_analysis", {})
            for symbol, analysis in trend_analysis.items():
                if symbol not in merged:
                    merged[symbol] = analysis
                else:
                    # Prefer more detailed analysis
                    if len(str(analysis)) > len(str(merged[symbol])):
                        merged[symbol] = analysis
        
        logger.debug(f"Merged trend analysis for {len(merged)} symbols")
        return merged
    
    @staticmethod
    def merge_parallel_agent_outputs(
        comparison_state: Dict[str, Any],
        trend_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge outputs from parallel Comparison and Trend agents (Phase 6)
        
        Args:
            comparison_state: State dictionary from Comparison Agent
            trend_state: State dictionary from Trend Agent
            
        Returns:
            Merged state dictionary
        """
        merged = comparison_state.copy()
        
        # Merge comparison data
        if "comparison_data" in trend_state:
            merged["comparison_data"] = trend_state["comparison_data"]
        
        # Merge trend analysis
        if "trend_analysis" in trend_state:
            merged["trend_analysis"] = trend_state["trend_analysis"]
        
        # Merge citations
        merged["citations"] = ContextMerger.merge_citations([comparison_state, trend_state])
        
        # Merge errors
        merged["errors"] = ContextMerger.merge_errors([comparison_state, trend_state])
        
        # Merge token usage
        merged["token_usage"] = ContextMerger.merge_token_usage([comparison_state, trend_state])
        
        logger.debug("Merged parallel Comparison and Trend agent outputs")
        return merged