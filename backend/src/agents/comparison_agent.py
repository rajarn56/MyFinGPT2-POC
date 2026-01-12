"""Comparison Agent implementation for Phase 6"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.utils.llm_client import LLMClient
from src.utils.token_tracker import TokenTracker
from src.vector_db.chroma_client import ChromaClient


class ComparisonAgent(BaseAgent):
    """Comparison Agent: Performs comparative analysis across multiple entities"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        chroma_client: Optional[ChromaClient] = None
    ):
        """
        Initialize Comparison Agent
        
        Args:
            llm_client: LLM client instance
            chroma_client: Chroma client for querying historical patterns (optional)
        """
        super().__init__("ComparisonAgent")
        self.llm_client = llm_client
        self.chroma_client = chroma_client
        self.token_tracker = TokenTracker()
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comparison agent
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.validate_state(state):
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append("Invalid state for ComparisonAgent")
            return state
        
        self.log_execution(state)
        
        # Ensure required state fields exist
        if "comparison_data" not in state:
            state["comparison_data"] = {}
        if "research_data" not in state:
            state["research_data"] = {}
        if "analyst_data" not in state:
            state["analyst_data"] = {}
        
        research_data = state.get("research_data", {})
        analyst_data = state.get("analyst_data", {})
        symbols = state.get("symbols", [])
        
        if not research_data:
            logger.warning("No research data available for comparison")
            state["errors"].append("No research data available for comparison")
            return state
        
        if len(symbols) < 2:
            logger.info("Single symbol detected, performing benchmark comparison")
            comparison_result = self._benchmark_comparison(symbols[0], research_data, analyst_data, state)
        else:
            logger.info(f"Multiple symbols detected ({len(symbols)}), performing side-by-side comparison")
            comparison_result = self._side_by_side_comparison(symbols, research_data, analyst_data, state)
        
        state["comparison_data"] = comparison_result
        state["updated_at"] = datetime.utcnow()
        
        return state
    
    def _benchmark_comparison(
        self,
        symbol: str,
        research_data: Dict[str, Any],
        analyst_data: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform benchmark comparison for a single symbol
        
        Args:
            symbol: Stock symbol
            research_data: Research data dictionary
            analyst_data: Analyst data dictionary
            state: AgentState dictionary
            
        Returns:
            Comparison result dictionary
        """
        if symbol not in research_data:
            logger.warning(f"No research data for symbol {symbol}")
            return {"error": f"No research data for {symbol}"}
        
        symbol_data = research_data[symbol]
        price_data = symbol_data.get("price", {})
        company_info = symbol_data.get("company_info", {})
        analysis = analyst_data.get(symbol, {})
        
        # Extract metrics
        metrics = self._extract_metrics(symbol, price_data, company_info, analysis)
        
        # Query historical patterns from vector DB if available
        historical_patterns = []
        if self.chroma_client:
            try:
                historical_patterns = self._query_historical_patterns(symbol, metrics)
            except Exception as e:
                logger.warning(f"Failed to query historical patterns: {e}")
        
        # Generate comparison insights using LLM
        insights = self._generate_benchmark_insights(symbol, metrics, historical_patterns, state)
        
        return {
            "comparison_type": "benchmark",
            "symbol": symbol,
            "metrics": metrics,
            "historical_patterns_count": len(historical_patterns),
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _side_by_side_comparison(
        self,
        symbols: List[str],
        research_data: Dict[str, Any],
        analyst_data: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform side-by-side comparison for multiple symbols
        
        Args:
            symbols: List of stock symbols
            research_data: Research data dictionary
            analyst_data: Analyst data dictionary
            state: AgentState dictionary
            
        Returns:
            Comparison result dictionary
        """
        # Extract metrics for each symbol
        metrics = {}
        for symbol in symbols:
            if symbol not in research_data:
                logger.warning(f"No research data for symbol {symbol}, skipping")
                continue
            
            symbol_data = research_data[symbol]
            price_data = symbol_data.get("price", {})
            company_info = symbol_data.get("company_info", {})
            analysis = analyst_data.get(symbol, {})
            
            metrics[symbol] = self._extract_metrics(symbol, price_data, company_info, analysis)
        
        if not metrics:
            return {"error": "No valid metrics extracted for comparison"}
        
        # Generate comparison table
        comparison_table = self._generate_comparison_table(metrics)
        
        # Generate comparison insights using LLM
        insights = self._generate_comparison_insights(metrics, comparison_table, state)
        
        return {
            "comparison_type": "side_by_side",
            "symbols": list(metrics.keys()),
            "metrics": metrics,
            "comparison_table": comparison_table,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _extract_metrics(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        company_info: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract comparison metrics from data
        
        Args:
            symbol: Stock symbol
            price_data: Price data dictionary
            company_info: Company info dictionary
            analysis: Analysis dictionary
            
        Returns:
            Metrics dictionary
        """
        # Extract sentiment safely - handle both dict and string formats
        raw_sentiment = analysis.get("sentiment", "neutral")
        sentiment_value = self._extract_sentiment_value(raw_sentiment)
        
        # Extract sentiment score - handle both dict and direct value
        sentiment_score = 0.0
        if isinstance(raw_sentiment, dict):
            sentiment_score = raw_sentiment.get("score", 0.0)
        else:
            sentiment_score = analysis.get("sentiment_score", 0.0)
        
        return {
            "symbol": symbol,
            "current_price": price_data.get("current_price") or price_data.get("price"),
            "market_cap": company_info.get("marketCap") or company_info.get("market_cap"),
            "pe_ratio": company_info.get("trailingPE") or company_info.get("pe_ratio"),
            "volume": price_data.get("volume"),
            "sector": company_info.get("sector"),
            "industry": company_info.get("industry"),
            "financial_metrics": {
                "revenue": company_info.get("totalRevenue"),
                "profit_margin": company_info.get("profitMargins"),
                "debt_to_equity": company_info.get("debtToEquity"),
            },
            "sentiment": sentiment_value,
            "sentiment_score": sentiment_score,
            "recommendation": analysis.get("recommendation", "hold")
        }
    
    def _generate_comparison_table(self, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comparison table from metrics
        
        Args:
            metrics: Dictionary mapping symbols to their metrics
            
        Returns:
            Comparison table dictionary
        """
        headers = ["Symbol", "Price", "Market Cap", "P/E Ratio", "Sector", "Sentiment"]
        rows = []
        
        for symbol, symbol_metrics in metrics.items():
            # Safely extract sentiment value - handle both dict and string formats
            sentiment = symbol_metrics.get("sentiment", "neutral")
            sentiment_value = self._extract_sentiment_value(sentiment)
            
            row = [
                symbol,
                f"${symbol_metrics.get('current_price', 'N/A')}",
                self._format_market_cap(symbol_metrics.get("market_cap")),
                symbol_metrics.get("pe_ratio", "N/A"),
                symbol_metrics.get("sector", "N/A"),
                sentiment_value.upper()
            ]
            rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows
        }
    
    def _extract_sentiment_value(self, sentiment: Any) -> str:
        """
        Safely extract sentiment value from dict or string
        
        Args:
            sentiment: Sentiment value (can be dict, string, or other type)
            
        Returns:
            Sentiment string value ("bullish", "bearish", or "neutral")
        """
        if isinstance(sentiment, dict):
            # Try common dict keys for sentiment value
            sentiment_value = (
                sentiment.get("sentiment") or
                sentiment.get("value") or
                sentiment.get("label")
            )
            if sentiment_value and isinstance(sentiment_value, str):
                return sentiment_value.lower()
            else:
                logger.warning(
                    f"Unexpected sentiment dict structure: {sentiment}. "
                    "Expected keys: 'sentiment', 'value', or 'label'"
                )
                return "neutral"
        elif isinstance(sentiment, str):
            return sentiment.lower()
        else:
            logger.warning(
                f"Unexpected sentiment type: {type(sentiment)}. "
                f"Value: {sentiment}. Defaulting to 'neutral'"
            )
            return "neutral"
    
    def _format_market_cap(self, market_cap: Optional[float]) -> str:
        """Format market cap for display"""
        if not market_cap:
            return "N/A"
        
        if market_cap >= 1e12:
            return f"${market_cap / 1e12:.2f}T"
        elif market_cap >= 1e9:
            return f"${market_cap / 1e9:.2f}B"
        elif market_cap >= 1e6:
            return f"${market_cap / 1e6:.2f}M"
        else:
            return f"${market_cap:.2f}"
    
    def _query_historical_patterns(self, symbol: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query historical comparison patterns from vector DB
        
        Args:
            symbol: Stock symbol
            metrics: Metrics dictionary
            
        Returns:
            List of historical patterns
        """
        if not self.chroma_client:
            return []
        
        try:
            # Create query text from metrics
            sector = metrics.get("sector", "")
            pe_ratio = metrics.get("pe_ratio")
            query_text = f"{symbol} {sector} P/E ratio {pe_ratio} comparison"
            
            # Query vector DB (simplified - would need embedding pipeline in real implementation)
            # For now, return empty list
            logger.debug(f"Querying historical patterns for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Error querying historical patterns: {e}")
            return []
    
    def _generate_benchmark_insights(
        self,
        symbol: str,
        metrics: Dict[str, Any],
        historical_patterns: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> str:
        """
        Generate benchmark comparison insights using LLM
        
        Args:
            symbol: Stock symbol
            metrics: Metrics dictionary
            historical_patterns: Historical patterns from vector DB
            state: AgentState dictionary
            
        Returns:
            Insights string
        """
        prompt = self._build_benchmark_prompt(symbol, metrics, historical_patterns)
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.completion(messages, temperature=0.7, max_tokens=1000)
            content = self.llm_client.get_content(response)
            
            # Track token usage
            if hasattr(response, "usage"):
                self.token_tracker.track_llm_call(state, self.name, response)
            
            return content
        except Exception as e:
            logger.error(f"Error generating benchmark insights: {e}")
            return f"Error generating insights: {str(e)}"
    
    def _generate_comparison_insights(
        self,
        metrics: Dict[str, Dict[str, Any]],
        comparison_table: Dict[str, Any],
        state: Dict[str, Any]
    ) -> str:
        """
        Generate side-by-side comparison insights using LLM
        
        Args:
            metrics: Dictionary mapping symbols to metrics
            comparison_table: Comparison table dictionary
            state: AgentState dictionary
            
        Returns:
            Insights string
        """
        prompt = self._build_comparison_prompt(metrics, comparison_table)
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.completion(messages, temperature=0.7, max_tokens=1500)
            content = self.llm_client.get_content(response)
            
            # Track token usage
            if hasattr(response, "usage"):
                self.token_tracker.track_llm_call(state, self.name, response)
            
            return content
        except Exception as e:
            logger.error(f"Error generating comparison insights: {e}")
            return f"Error generating insights: {str(e)}"
    
    def _build_benchmark_prompt(
        self,
        symbol: str,
        metrics: Dict[str, Any],
        historical_patterns: List[Dict[str, Any]]
    ) -> str:
        """Build benchmark comparison prompt"""
        return f"""Analyze and compare the following stock against benchmarks and historical patterns:

Symbol: {symbol}
Current Price: ${metrics.get('current_price', 'N/A')}
Market Cap: {self._format_market_cap(metrics.get('market_cap'))}
P/E Ratio: {metrics.get('pe_ratio', 'N/A')}
Sector: {metrics.get('sector', 'N/A')}
Industry: {metrics.get('industry', 'N/A')}

Financial Metrics:
{self._format_financial_metrics(metrics.get('financial_metrics', {}))}

Historical Patterns Found: {len(historical_patterns)} similar patterns

Provide a comprehensive comparison analysis including:
1. How this stock compares to sector/industry averages
2. Historical patterns and what they suggest
3. Relative valuation assessment
4. Key strengths and weaknesses compared to peers
5. Investment implications

Format your response as a clear, structured analysis."""
    
    def _build_comparison_prompt(
        self,
        metrics: Dict[str, Dict[str, Any]],
        comparison_table: Dict[str, Any]
    ) -> str:
        """Build side-by-side comparison prompt"""
        comparison_summary = "\n".join([
            f"{symbol}: Price=${m.get('current_price', 'N/A')}, "
            f"Market Cap={self._format_market_cap(m.get('market_cap'))}, "
            f"P/E={m.get('pe_ratio', 'N/A')}, "
            f"Sector={m.get('sector', 'N/A')}, "
            f"Sentiment={m.get('sentiment', 'neutral')}"
            for symbol, m in metrics.items()
        ])
        
        return f"""Compare the following stocks side-by-side and provide comprehensive analysis:

{comparison_summary}

Comparison Table:
Headers: {', '.join(comparison_table.get('headers', []))}
Rows: {len(comparison_table.get('rows', []))} stocks

Provide a detailed comparison analysis including:
1. Relative valuation comparison
2. Financial strength comparison
3. Market sentiment comparison
4. Sector/industry positioning
5. Risk assessment for each
6. Investment recommendation ranking
7. Key differentiators

Format your response as a clear, structured comparison analysis."""
    
    def _format_financial_metrics(self, financial_metrics: Dict[str, Any]) -> str:
        """Format financial metrics for prompt"""
        lines = []
        for key, value in financial_metrics.items():
            if value is not None:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines) if lines else "  N/A"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for comparison agent"""
        return """You are a financial analysis expert specializing in comparative analysis of stocks and companies.

Your role is to:
- Provide objective, data-driven comparisons
- Identify key differentiators between entities
- Assess relative valuation and investment potential
- Highlight strengths and weaknesses
- Provide actionable insights

Always base your analysis on the provided metrics and data. Be clear, concise, and structured in your responses."""
