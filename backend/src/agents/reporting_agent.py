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
            
            # Generate summary for chat messages
            try:
                summary = self._generate_summary(query, symbols, research_data, analyst_data, state)
                state["summary"] = summary
            except Exception as e:
                logger.warning(f"Summary generation failed, will use report excerpt: {e}")
                # Fallback: use first paragraph of report as summary
                if report:
                    first_paragraph = report.split('\n\n')[0] if '\n\n' in report else report[:300]
                    state["summary"] = first_paragraph + "\n\n*See full report in Results panel.*"
                else:
                    state["summary"] = None
            
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
            # Generate fallback report (include state for trend data)
            state["report"] = self._fallback_report(query, symbols, research_data, analyst_data, state)
        
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
4. Trend Analysis (if available)
5. Recommendations (if applicable)
6. Citations

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
        
        # Add trend analysis data if available
        trend_analysis = state.get("trend_analysis", {})
        if trend_analysis:
            prompt += "\n**Trend Analysis Data:**\n"
            for symbol in symbols:
                if symbol in trend_analysis:
                    trend_data = trend_analysis[symbol]
                    prompt += f"\n### {symbol} Trend Analysis:\n"
                    prompt += f"- Price Trend: {trend_data.get('price_trend', 'N/A')}\n"
                    prompt += f"- Trend Strength: {trend_data.get('trend_strength', 'N/A')}\n"
                    prompt += f"- Pattern Type: {trend_data.get('pattern_type', 'N/A')}\n"
                    if trend_data.get('trend_prediction'):
                        prediction = trend_data['trend_prediction']
                        if isinstance(prediction, dict):
                            prompt += f"- Trend Prediction: {prediction.get('direction', 'N/A')} "
                            prompt += f"(Confidence: {prediction.get('confidence', 'N/A')})\n"
                            if prediction.get('reasoning'):
                                prompt += f"- Reasoning: {str(prediction.get('reasoning', ''))[:200]}...\n"
                        else:
                            prompt += f"- Trend Prediction: {str(prediction)[:200]}...\n"
                    if trend_data.get('support_level'):
                        prompt += f"- Support Level: ${trend_data.get('support_level')}\n"
                    if trend_data.get('resistance_level'):
                        prompt += f"- Resistance Level: ${trend_data.get('resistance_level')}\n"
        
        # Add comparison data if available
        comparison_data = state.get("comparison_data", {})
        if comparison_data and comparison_data.get("comparison_type") == "side_by_side":
            prompt += "\n**Comparison Data:**\n"
            if comparison_data.get("comparison_table"):
                table = comparison_data["comparison_table"]
                prompt += f"- Comparison Table: {len(table.get('rows', []))} symbols compared\n"
            if comparison_data.get("insights"):
                prompt += f"- Comparison Insights: {str(comparison_data['insights'])[:300]}...\n"
        
        prompt += """
Please generate a comprehensive report in Markdown format with:
1. **Executive Summary** - High-level overview
2. **Key Findings** - Main insights
3. **Detailed Analysis** - Per-symbol analysis
4. **Trend Analysis** - Price trends and patterns (if trend data is available)
5. **Recommendations** - Actionable recommendations (if applicable)
6. **Citations** - Reference the data sources

Use clear formatting and include specific metrics and data points. If trend analysis data is provided, include a dedicated section analyzing price trends, patterns, and predictions."""
        
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
                        analyst_data: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> str:
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
        
        # Add trend analysis if available
        if state:
            trend_analysis = state.get("trend_analysis", {})
            if trend_analysis:
                report += "## Trend Analysis\n\n"
                for symbol in symbols:
                    if symbol in trend_analysis:
                        trend_data = trend_analysis[symbol]
                        report += f"### {symbol}\n"
                        report += f"- Price Trend: {trend_data.get('price_trend', 'N/A')}\n"
                        report += f"- Trend Strength: {trend_data.get('trend_strength', 'N/A')}\n"
                        if trend_data.get('trend_prediction'):
                            prediction = trend_data['trend_prediction']
                            if isinstance(prediction, dict):
                                report += f"- Prediction: {prediction.get('direction', 'N/A')}\n"
                            else:
                                report += f"- Prediction: {str(prediction)[:100]}...\n"
                        report += "\n"
        
        report += "## Note\n\n"
        report += "This is a basic report. Full LLM-powered analysis was unavailable.\n"
        
        return report
    
    def _generate_summary(self, query: str, symbols: List[str], research_data: Dict[str, Any],
                         analyst_data: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Generate concise summary for chat messages
        
        Args:
            query: Original user query
            symbols: List of symbols analyzed
            research_data: Research data from Research Agent
            analyst_data: Analysis data from Analyst Agent
            state: AgentState dictionary
            
        Returns:
            Markdown-formatted summary (2-3 paragraphs max)
        """
        if not symbols:
            return "Analysis completed. See full report for details."
        
        summary_parts = []
        
        # Extract key information for each symbol
        for symbol in symbols:
            symbol_summary = []
            
            # Company name and symbol
            company_name = "Unknown"
            if symbol in research_data:
                rd = research_data[symbol]
                company_info = rd.get("company_info", {})
                company_name = company_info.get("name", symbol)
            
            symbol_summary.append(f"**{company_name} ({symbol})**")
            
            # Current price and key metrics
            price_info = []
            if symbol in research_data:
                rd = research_data[symbol]
                price_data = rd.get("price", {})
                current_price = price_data.get("current_price") or price_data.get("price")
                if current_price:
                    price_info.append(f"**Current Price:** ${current_price:.2f}")
                
                company_info = rd.get("company_info", {})
                market_cap = company_info.get("marketCap") or company_info.get("market_cap")
                if market_cap:
                    if market_cap >= 1e12:
                        market_cap_str = f"${market_cap / 1e12:.2f}T"
                    elif market_cap >= 1e9:
                        market_cap_str = f"${market_cap / 1e9:.2f}B"
                    elif market_cap >= 1e6:
                        market_cap_str = f"${market_cap / 1e6:.2f}M"
                    else:
                        market_cap_str = f"${market_cap:.2f}"
                    price_info.append(f"**Market Cap:** {market_cap_str}")
                
                pe_ratio = company_info.get("trailingPE") or company_info.get("pe_ratio")
                if pe_ratio:
                    price_info.append(f"**P/E Ratio:** {pe_ratio:.2f}")
            
            if price_info:
                symbol_summary.append(" | ".join(price_info))
            
            # Sentiment
            sentiment_str = "Neutral"
            if symbol in analyst_data:
                ad = analyst_data[symbol]
                sentiment = ad.get("sentiment", {})
                if isinstance(sentiment, dict):
                    sentiment_value = sentiment.get("sentiment", "neutral")
                else:
                    sentiment_value = str(sentiment).lower()
                
                sentiment_map = {
                    "bullish": "Bullish",
                    "bearish": "Bearish",
                    "neutral": "Neutral"
                }
                sentiment_str = sentiment_map.get(sentiment_value.lower(), "Neutral")
            
            symbol_summary.append(f"**Sentiment:** {sentiment_str}")
            
            # Key findings (extract from financial analysis)
            key_findings = []
            if symbol in analyst_data:
                ad = analyst_data[symbol]
                financial_analysis = ad.get("financial_analysis", "")
                if financial_analysis:
                    # Extract first 2-3 sentences or bullet points
                    sentences = financial_analysis.split('.')[:3]
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if sentence and len(sentence) > 20:
                            key_findings.append(sentence)
            
            if key_findings:
                symbol_summary.append("\n**Key Findings:**")
                for finding in key_findings[:3]:
                    symbol_summary.append(f"• {finding}")
            
            # Recommendation (if available)
            recommendation = None
            if symbol in analyst_data:
                ad = analyst_data[symbol]
                recommendation = ad.get("recommendation")
            
            if recommendation:
                symbol_summary.append(f"\n**Recommendation:** {recommendation}")
            
            summary_parts.append("\n".join(symbol_summary))
        
        # Combine all symbol summaries
        if len(symbols) == 1:
            summary = f"## Quick Summary\n\n{summary_parts[0]}"
        else:
            summary = f"## Comparison Summary\n\n" + "\n\n---\n\n".join(summary_parts)
        
        summary += "\n\n*See full report in the Results panel for detailed analysis.*"
        
        return summary
    
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
