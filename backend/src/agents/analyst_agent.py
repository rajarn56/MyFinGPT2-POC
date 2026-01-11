"""Analyst Agent implementation for Phase 3"""

from typing import Dict, Any
from datetime import datetime
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.utils.llm_client import LLMClient
from src.utils.token_tracker import TokenTracker


class AnalystAgent(BaseAgent):
    """Analyst Agent: Performs financial analysis and sentiment analysis"""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize Analyst Agent
        
        Args:
            llm_client: LLM client instance
        """
        super().__init__("AnalystAgent")
        self.llm_client = llm_client
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute analyst agent
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.validate_state(state):
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append("Invalid state for AnalystAgent")
            return state
        
        self.log_execution(state)
        
        # Ensure required state fields exist
        if "analyst_data" not in state:
            state["analyst_data"] = {}
        if "research_data" not in state:
            state["research_data"] = {}
        
        research_data = state.get("research_data", {})
        symbols = state.get("symbols", [])
        
        if not research_data:
            logger.warning("No research data available for analysis")
            state["errors"].append("No research data available for analysis")
            return state
        
        # Analyze each symbol
        for symbol in symbols:
            if symbol not in research_data:
                logger.warning(f"No research data for symbol {symbol}")
                continue
            
            try:
                analysis = self._analyze_symbol(symbol, research_data[symbol], state)
                state["analyst_data"][symbol] = analysis
                logger.info(f"Completed analysis for {symbol}")
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(f"Failed to analyze {symbol}: {str(e)}")
        
        state["updated_at"] = datetime.utcnow()
        return state
    
    def _analyze_symbol(self, symbol: str, research_data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single symbol
        
        Args:
            symbol: Stock symbol
            research_data: Research data for the symbol
            state: AgentState dictionary
            
        Returns:
            Analysis dictionary
        """
        # Prepare context for LLM
        price_data = research_data.get("price", {})
        company_info = research_data.get("company_info", {})
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(symbol, price_data, company_info, state.get("query", ""))
        
        # Call LLM for analysis
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.completion(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Track token usage
            usage = self.llm_client.get_usage(response)
            if usage:
                TokenTracker.track_llm_call(state, self.name, response)
            
            # Extract analysis content
            analysis_content = self.llm_client.get_content(response)
            
            # Parse analysis (expecting structured output)
            analysis = self._parse_analysis(analysis_content, symbol, price_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis failed for {symbol}: {e}")
            # Return basic analysis without LLM
            return self._fallback_analysis(symbol, price_data, company_info)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for analyst agent"""
        return """You are a financial analyst agent. Your role is to analyze financial data and provide:
1. Financial Analysis: Key metrics, trends, and insights
2. Sentiment Analysis: Overall market sentiment (bullish, bearish, neutral)
3. Key Trends: Important patterns or changes
4. Risk Assessment: Potential risks or concerns

Provide your analysis in a structured format with clear sections."""
    
    def _build_analysis_prompt(self, symbol: str, price_data: Dict[str, Any], 
                              company_info: Dict[str, Any], query: str) -> str:
        """Build analysis prompt"""
        prompt = f"""Analyze the following financial data for {symbol}:

**Price Data:**
- Current Price: ${price_data.get('current_price', 'N/A')}
- Previous Close: ${price_data.get('previous_close', 'N/A')}
- Market Cap: {price_data.get('market_cap', 'N/A')}
- Volume: {price_data.get('volume', 'N/A')}
- 52-Week High: ${price_data.get('52_week_high', 'N/A')}
- 52-Week Low: ${price_data.get('52_week_low', 'N/A')}

**Company Information:**
- Name: {company_info.get('name', 'N/A')}
- Sector: {company_info.get('sector', 'N/A')}
- Industry: {company_info.get('industry', 'N/A')}

**User Query:** {query}

Please provide:
1. **Financial Analysis**: Key insights about the stock's financial position
2. **Sentiment**: Overall sentiment (bullish/bearish/neutral) with reasoning
3. **Trends**: Key trends or patterns observed
4. **Risk Assessment**: Potential risks or concerns

Format your response as structured text with clear sections."""
        
        return prompt
    
    def _parse_analysis(self, content: str, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM analysis content into structured format
        
        Args:
            content: LLM response content
            symbol: Stock symbol
            price_data: Price data for context
            
        Returns:
            Structured analysis dictionary
        """
        # Extract sections from content
        analysis = {
            "symbol": symbol,
            "financial_analysis": self._extract_section(content, "Financial Analysis"),
            "sentiment": self._extract_sentiment(content),
            "trends": self._extract_section(content, "Trends"),
            "risk_assessment": self._extract_section(content, "Risk Assessment"),
            "raw_content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from content"""
        # Look for section headers (various formats)
        patterns = [
            f"**{section_name}**:",
            f"## {section_name}",
            f"# {section_name}",
            f"{section_name}:"
        ]
        
        for pattern in patterns:
            if pattern in content:
                start_idx = content.find(pattern) + len(pattern)
                # Find next section or end
                next_section = content.find("**", start_idx + 1)
                if next_section == -1:
                    next_section = content.find("##", start_idx + 1)
                if next_section == -1:
                    next_section = len(content)
                
                section_content = content[start_idx:next_section].strip()
                return section_content
        
        return ""
    
    def _extract_sentiment(self, content: str) -> Dict[str, Any]:
        """Extract sentiment from content"""
        content_lower = content.lower()
        
        # Determine sentiment
        sentiment = "neutral"
        if any(word in content_lower for word in ["bullish", "positive", "upward", "growth", "strong"]):
            sentiment = "bullish"
        elif any(word in content_lower for word in ["bearish", "negative", "downward", "decline", "weak"]):
            sentiment = "bearish"
        
        # Extract sentiment score (if mentioned)
        score = 0.5  # Default neutral
        if sentiment == "bullish":
            score = 0.7
        elif sentiment == "bearish":
            score = 0.3
        
        return {
            "sentiment": sentiment,
            "score": score,
            "reasoning": self._extract_section(content, "Sentiment") or ""
        }
    
    def _fallback_analysis(self, symbol: str, price_data: Dict[str, Any], 
                          company_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        current_price = price_data.get("current_price", 0)
        previous_close = price_data.get("previous_close", 0)
        
        # Basic sentiment based on price change
        if current_price > previous_close:
            sentiment = "bullish"
            score = 0.6
        elif current_price < previous_close:
            sentiment = "bearish"
            score = 0.4
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "symbol": symbol,
            "financial_analysis": f"Current price: ${current_price}. Previous close: ${previous_close}.",
            "sentiment": {
                "sentiment": sentiment,
                "score": score,
                "reasoning": f"Price change: {current_price - previous_close}"
            },
            "trends": "Basic analysis - LLM analysis unavailable",
            "risk_assessment": "Unable to assess risks - LLM analysis unavailable",
            "raw_content": "",
            "timestamp": datetime.utcnow().isoformat()
        }
