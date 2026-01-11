"""Reporting Agent implementation for Phase 3 with Phase 4 Knowledge Layer integration"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.utils.llm_client import LLMClient
from src.utils.token_tracker import TokenTracker
from src.services.ingestion_service import IngestionService


class ReportingAgent(BaseAgent):
    """Reporting Agent: Synthesizes reports from multiple agent outputs"""
    
    def __init__(self, llm_client: LLMClient, ingestion_service: Optional[IngestionService] = None):
        """
        Initialize Reporting Agent
        
        Args:
            llm_client: LLM client instance
            ingestion_service: IngestionService for storing reports in knowledge layer (optional)
        """
        super().__init__("ReportingAgent")
        self.llm_client = llm_client
        self.ingestion_service = ingestion_service
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute reporting agent
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.validate_state(state):
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append("Invalid state for ReportingAgent")
            return state
        
        self.log_execution(state)
        
        # Ensure required state fields exist
        if "research_data" not in state:
            state["research_data"] = {}
        if "analyst_data" not in state:
            state["analyst_data"] = {}
        if "citations" not in state:
            state["citations"] = []
        
        research_data = state.get("research_data", {})
        analyst_data = state.get("analyst_data", {})
        query = state.get("query", "")
        symbols = state.get("symbols", [])
        
        if not research_data and not analyst_data:
            logger.warning("No data available for report generation")
            state["errors"].append("No data available for report generation")
            return state
        
        try:
            # Generate report
            report = self._generate_report(query, symbols, research_data, analyst_data, state)
            state["report"] = report
            
            # Phase 4: Store report in knowledge layer if ingestion service available
            if self.ingestion_service:
                try:
                    session_id = state.get("session_id", "")
                    transaction_id = state.get("transaction_id", "")
                    query_type = self._determine_query_type(query)
                    
                    self.ingestion_service.ingest_analysis_report(
                        report_content=report,
                        symbols=symbols,
                        query_type=query_type,
                        session_id=session_id,
                        transaction_id=transaction_id,
                        metadata={"agent": "ReportingAgent"}
                    )
                    
                    # Also store conversation in conversation history
                    if session_id:
                        user_query = state.get("query", "")
                        self.ingestion_service.ingest_conversation(
                            user_message=user_query,
                            agent_response=report[:500] + "..." if len(report) > 500 else report,  # Truncate for storage
                            session_id=session_id,
                            symbols=symbols,
                            metadata={"transaction_id": transaction_id}
                        )
                except Exception as e:
                    logger.warning(f"Failed to ingest report to knowledge layer: {e}")
            
            logger.info("Report generated successfully")
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Failed to generate report: {str(e)}")
            # Generate fallback report
            state["report"] = self._fallback_report(query, symbols, research_data, analyst_data)
        
        state["updated_at"] = datetime.utcnow()
        return state
    
    def _generate_report(self, query: str, symbols: List[str], research_data: Dict[str, Any],
                        analyst_data: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Generate comprehensive report
        
        Args:
            query: Original user query
            symbols: List of symbols analyzed
            research_data: Research data from Research Agent
            analyst_data: Analysis data from Analyst Agent
            state: AgentState dictionary
            
        Returns:
            Markdown-formatted report
        """
        # Build report generation prompt
        prompt = self._build_report_prompt(query, symbols, research_data, analyst_data, state)
        
        # Call LLM for report synthesis
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.completion(
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            # Track token usage
            usage = self.llm_client.get_usage(response)
            if usage:
                TokenTracker.track_llm_call(state, self.name, response)
            
            # Extract report content
            report_content = self.llm_client.get_content(response)
            
            # Add citations to report
            report_with_citations = self._add_citations(report_content, state.get("citations", []))
            
            return report_with_citations
            
        except Exception as e:
            logger.error(f"LLM report generation failed: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for reporting agent"""
        return """You are a financial reporting agent. Your role is to synthesize comprehensive financial reports from research data and analysis.

Create well-structured reports in Markdown format with:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Recommendations (if applicable)
5. Citations

Use clear headings, bullet points, and formatting. Include specific data points and metrics."""
    
    def _build_report_prompt(self, query: str, symbols: List[str], research_data: Dict[str, Any],
                           analyst_data: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Build report generation prompt"""
        prompt = f"""Generate a comprehensive financial analysis report based on the following data:

**User Query:** {query}

**Symbols Analyzed:** {', '.join(symbols)}

**Research Data:**
"""
        
        # Add research data for each symbol
        for symbol in symbols:
            if symbol in research_data:
                rd = research_data[symbol]
                prompt += f"\n### {symbol} Research Data:\n"
                prompt += f"- Price: ${rd.get('price', {}).get('current_price', 'N/A')}\n"
                prompt += f"- Company: {rd.get('company_info', {}).get('name', 'N/A')}\n"
                prompt += f"- Sector: {rd.get('company_info', {}).get('sector', 'N/A')}\n"
        
        prompt += "\n**Analysis Data:**\n"
        
        # Add analysis data for each symbol
        for symbol in symbols:
            if symbol in analyst_data:
                ad = analyst_data[symbol]
                prompt += f"\n### {symbol} Analysis:\n"
                prompt += f"- Sentiment: {ad.get('sentiment', {}).get('sentiment', 'N/A')}\n"
                prompt += f"- Financial Analysis: {ad.get('financial_analysis', 'N/A')[:200]}...\n"
                prompt += f"- Trends: {ad.get('trends', 'N/A')[:200]}...\n"
        
        prompt += """
Please generate a comprehensive report in Markdown format with:
1. **Executive Summary** - High-level overview
2. **Key Findings** - Main insights
3. **Detailed Analysis** - Per-symbol analysis
4. **Recommendations** - Actionable recommendations (if applicable)
5. **Citations** - Reference the data sources

Use clear formatting and include specific metrics and data points."""
        
        return prompt
    
    def _add_citations(self, report: str, citations: List[Dict[str, str]]) -> str:
        """
        Add citations section to report
        
        Args:
            report: Report content
            citations: List of citations
            
        Returns:
            Report with citations section
        """
        if not citations:
            return report
        
        citations_section = "\n\n## Citations\n\n"
        for i, citation in enumerate(citations, 1):
            source = citation.get("source", "Unknown")
            symbol = citation.get("symbol", "")
            citation_type = citation.get("type", "")
            
            citations_section += f"{i}. {source}"
            if symbol:
                citations_section += f" - {symbol}"
            if citation_type:
                citations_section += f" ({citation_type})"
            citations_section += "\n"
        
        return report + citations_section
    
    def _fallback_report(self, query: str, symbols: List[str], research_data: Dict[str, Any],
                        analyst_data: Dict[str, Any]) -> str:
        """Generate fallback report when LLM fails"""
        report = f"# Financial Analysis Report\n\n"
        report += f"**Query:** {query}\n\n"
        report += f"**Symbols Analyzed:** {', '.join(symbols)}\n\n"
        
        report += "## Summary\n\n"
        report += "This report was generated with limited analysis capabilities.\n\n"
        
        report += "## Research Data\n\n"
        for symbol in symbols:
            if symbol in research_data:
                rd = research_data[symbol]
                report += f"### {symbol}\n"
                report += f"- Price: ${rd.get('price', {}).get('current_price', 'N/A')}\n"
                report += f"- Company: {rd.get('company_info', {}).get('name', 'N/A')}\n\n"
        
        report += "## Analysis\n\n"
        for symbol in symbols:
            if symbol in analyst_data:
                ad = analyst_data[symbol]
                report += f"### {symbol}\n"
                report += f"- Sentiment: {ad.get('sentiment', {}).get('sentiment', 'N/A')}\n\n"
        
        report += "## Note\n\n"
        report += "This is a basic report. Full LLM-powered analysis was unavailable.\n"
        
        return report
    
    def _determine_query_type(self, query: str) -> str:
        """
        Determine query type from user query
        
        Args:
            query: User query text
            
        Returns:
            Query type string (e.g., "analysis", "comparison", "trend")
        """
        query_lower = query.lower()
        if any(word in query_lower for word in ["compare", "comparison", "vs", "versus"]):
            return "comparison"
        elif any(word in query_lower for word in ["trend", "history", "historical", "over time"]):
            return "trend"
        elif any(word in query_lower for word in ["analyze", "analysis", "evaluate", "assess"]):
            return "analysis"
        else:
            return "general"
