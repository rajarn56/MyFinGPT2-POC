"""Query intent classification utility for Phase 6"""

from typing import Dict, Any, List, Optional
from loguru import logger
import re

from src.utils.llm_client import LLMClient


class QueryIntentClassifier:
    """Classify user query intent for conditional agent execution"""
    
    # Intent keywords
    COMPARISON_KEYWORDS = [
        "compare", "comparison", "versus", "vs", "vs.", "against",
        "difference", "differences", "better", "best", "worse", "worst",
        "side by side", "side-by-side", "relative", "relatively"
    ]
    
    TREND_KEYWORDS = [
        "trend", "trends", "trending", "pattern", "patterns",
        "direction", "momentum", "movement", "movements",
        "historical", "history", "over time", "performance",
        "chart", "charts", "technical", "technical analysis"
    ]
    
    EDGAR_KEYWORDS = [
        "10-k", "10-q", "sec filing", "edgar", "filing", "filings",
        "annual report", "quarterly report", "form 10-k", "form 10-q",
        "sec", "securities and exchange commission"
    ]
    
    COMPREHENSIVE_KEYWORDS = [
        "comprehensive", "complete", "full", "detailed", "deep dive",
        "in-depth", "thorough", "extensive", "all", "everything"
    ]
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize query intent classifier
        
        Args:
            llm_client: LLM client for advanced classification (optional)
        """
        self.llm_client = llm_client
        logger.info("Initialized QueryIntentClassifier")
    
    def classify(self, query: str, symbols: List[str]) -> Dict[str, Any]:
        """
        Classify query intent
        
        Args:
            query: User query string
            symbols: List of symbols extracted from query
            
        Returns:
            Classification dictionary with intent and flags
        """
        query_lower = query.lower()
        
        # Rule-based classification (can be enhanced with LLM)
        intent_flags = {
            "is_comparison": self._is_comparison_query(query_lower, symbols),
            "is_trend": self._is_trend_query(query_lower),
            "is_edgar": self._is_edgar_query(query_lower),
            "is_comprehensive": self._is_comprehensive_query(query_lower),
            "is_single_entity": len(symbols) == 1,
            "is_multi_entity": len(symbols) > 1
        }
        
        # Determine primary query type
        query_type = self._determine_query_type(intent_flags, symbols)
        
        # Use LLM for advanced classification if available
        if self.llm_client:
            try:
                llm_classification = self._llm_classify(query, symbols, intent_flags)
                # Merge LLM results with rule-based results
                intent_flags.update(llm_classification)
                if llm_classification.get("query_type"):
                    query_type = llm_classification["query_type"]
            except Exception as e:
                logger.warning(f"LLM classification failed, using rule-based: {e}")
        
        result = {
            "query_type": query_type,
            "intent_flags": intent_flags,
            "symbols": symbols,
            "original_query": query
        }
        
        logger.info(f"Classified query: type={query_type}, flags={intent_flags}")
        return result
    
    def _is_comparison_query(self, query_lower: str, symbols: List[str]) -> bool:
        """Check if query is a comparison query"""
        # Multiple symbols indicate comparison
        if len(symbols) > 1:
            return True
        
        # Check for comparison keywords
        for keyword in self.COMPARISON_KEYWORDS:
            if keyword in query_lower:
                return True
        
        return False
    
    def _is_trend_query(self, query_lower: str) -> bool:
        """Check if query is a trend query"""
        for keyword in self.TREND_KEYWORDS:
            if keyword in query_lower:
                return True
        return False
    
    def _is_edgar_query(self, query_lower: str) -> bool:
        """Check if query is an EDGAR/filing query"""
        for keyword in self.EDGAR_KEYWORDS:
            if keyword in query_lower:
                return True
        return False
    
    def _is_comprehensive_query(self, query_lower: str) -> bool:
        """Check if query requests comprehensive analysis"""
        for keyword in self.COMPREHENSIVE_KEYWORDS:
            if keyword in query_lower:
                return True
        return False
    
    def _determine_query_type(
        self,
        intent_flags: Dict[str, bool],
        symbols: List[str]
    ) -> str:
        """
        Determine primary query type from intent flags
        
        Args:
            intent_flags: Intent flags dictionary
            symbols: List of symbols
            
        Returns:
            Query type string
        """
        if intent_flags.get("is_edgar"):
            return "filing_analysis"
        
        if intent_flags.get("is_comparison") or len(symbols) > 1:
            if intent_flags.get("is_comprehensive"):
                return "comprehensive_comparison"
            return "comparison"
        
        if intent_flags.get("is_trend"):
            if intent_flags.get("is_comprehensive"):
                return "comprehensive_trend"
            return "trend"
        
        if intent_flags.get("is_comprehensive"):
            return "comprehensive_analysis"
        
        # Default to single entity analysis
        return "single_entity"
    
    def _llm_classify(
        self,
        query: str,
        symbols: List[str],
        rule_based_flags: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Use LLM for advanced query classification
        
        Args:
            query: User query
            symbols: List of symbols
            rule_based_flags: Rule-based classification flags
            
        Returns:
            LLM classification dictionary
        """
        if not self.llm_client:
            return {}
        
        prompt = f"""Classify the following financial analysis query:

Query: "{query}"
Symbols: {', '.join(symbols) if symbols else 'None'}

Rule-based classification:
- Comparison: {rule_based_flags.get('is_comparison', False)}
- Trend: {rule_based_flags.get('is_trend', False)}
- EDGAR: {rule_based_flags.get('is_edgar', False)}
- Comprehensive: {rule_based_flags.get('is_comprehensive', False)}

Provide a JSON response with:
{{
    "query_type": "single_entity|comparison|trend|filing_analysis|comprehensive_analysis|comprehensive_comparison|comprehensive_trend",
    "confidence": "high|medium|low",
    "requires_comparison_agent": true|false,
    "requires_trend_agent": true|false,
    "requires_edgar_agent": true|false,
    "reasoning": "brief explanation"
}}

Only respond with valid JSON, no additional text."""
        
        messages = [
            {"role": "system", "content": "You are a query classification expert. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.completion(messages, temperature=0.3, max_tokens=200)
            content = self.llm_client.get_content(response)
            
            # Parse JSON response (simplified - would need proper JSON parsing)
            # For now, return empty dict and rely on rule-based classification
            logger.debug(f"LLM classification response: {content[:200]}")
            return {}
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {}
    
    def should_use_comparison_agent(self, classification: Dict[str, Any]) -> bool:
        """Check if Comparison Agent should be used"""
        intent_flags = classification.get("intent_flags", {})
        return (
            intent_flags.get("is_comparison", False) or
            intent_flags.get("is_multi_entity", False) or
            classification.get("query_type") in ["comparison", "comprehensive_comparison"]
        )
    
    def should_use_trend_agent(self, classification: Dict[str, Any]) -> bool:
        """Check if Trend Agent should be used"""
        intent_flags = classification.get("intent_flags", {})
        return (
            intent_flags.get("is_trend", False) or
            classification.get("query_type") in ["trend", "comprehensive_trend", "comprehensive_analysis"]
        )
    
    def should_use_edgar_agent(self, classification: Dict[str, Any]) -> bool:
        """Check if EDGAR Agent should be used"""
        intent_flags = classification.get("intent_flags", {})
        return (
            intent_flags.get("is_edgar", False) or
            classification.get("query_type") in ["filing_analysis", "comprehensive_analysis"]
        )
