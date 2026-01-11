"""Trend Agent implementation for Phase 6"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import statistics

from src.agents.base_agent import BaseAgent
from src.utils.llm_client import LLMClient
from src.utils.token_tracker import TokenTracker
from src.vector_db.chroma_client import ChromaClient


class TrendAgent(BaseAgent):
    """Trend Agent: Identifies and analyzes market trends and patterns"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        chroma_client: Optional[ChromaClient] = None
    ):
        """
        Initialize Trend Agent
        
        Args:
            llm_client: LLM client instance
            chroma_client: Chroma client for querying historical trends (optional)
        """
        super().__init__("TrendAgent")
        self.llm_client = llm_client
        self.chroma_client = chroma_client
        self.token_tracker = TokenTracker()
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute trend agent
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.validate_state(state):
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append("Invalid state for TrendAgent")
            return state
        
        self.log_execution(state)
        
        # Ensure required state fields exist
        if "trend_analysis" not in state:
            state["trend_analysis"] = {}
        if "research_data" not in state:
            state["research_data"] = {}
        
        research_data = state.get("research_data", {})
        symbols = state.get("symbols", [])
        
        if not research_data:
            logger.warning("No research data available for trend analysis")
            state["errors"].append("No research data available for trend analysis")
            return state
        
        # Analyze trends for each symbol
        for symbol in symbols:
            if symbol not in research_data:
                logger.warning(f"No research data for symbol {symbol}")
                continue
            
            try:
                trend_result = self._analyze_trend(symbol, research_data[symbol], state)
                state["trend_analysis"][symbol] = trend_result
                logger.info(f"Completed trend analysis for {symbol}")
            except Exception as e:
                logger.error(f"Error analyzing trends for {symbol}: {e}")
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(f"Failed to analyze trends for {symbol}: {str(e)}")
        
        state["updated_at"] = datetime.utcnow()
        return state
    
    def _analyze_trend(
        self,
        symbol: str,
        symbol_data: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze trends for a single symbol
        
        Args:
            symbol: Stock symbol
            symbol_data: Research data for the symbol
            state: AgentState dictionary
            
        Returns:
            Trend analysis dictionary
        """
        price_data = symbol_data.get("price", {})
        company_info = symbol_data.get("company_info", {})
        
        # Extract historical price data (if available)
        # In a real implementation, this would fetch historical prices from MCP
        # For now, we'll use current price and simulate trend calculation
        historical_prices = self._extract_historical_prices(price_data, symbol_data)
        
        if not historical_prices or len(historical_prices) < 2:
            logger.warning(f"Insufficient historical data for {symbol}, using basic trend analysis")
            return self._basic_trend_analysis(symbol, price_data, company_info, state)
        
        # Calculate trend metrics
        price_trend = self._calculate_price_trend(historical_prices)
        trend_strength = self._calculate_trend_strength(historical_prices)
        pattern_type = self._identify_pattern(historical_prices)
        support_level, resistance_level = self._calculate_support_resistance(historical_prices)
        
        # Query historical trends from vector DB if available
        historical_trends = []
        if self.chroma_client:
            try:
                historical_trends = self._query_historical_trends(symbol, price_trend, pattern_type)
            except Exception as e:
                logger.warning(f"Failed to query historical trends: {e}")
        
        # Generate trend prediction using LLM
        trend_prediction = self._generate_trend_prediction(
            symbol,
            price_trend,
            trend_strength,
            pattern_type,
            support_level,
            resistance_level,
            historical_prices,
            historical_trends,
            state
        )
        
        # Store trend pattern in vector DB if available
        if self.chroma_client:
            try:
                self._store_trend_pattern(symbol, price_trend, pattern_type, trend_strength)
            except Exception as e:
                logger.warning(f"Failed to store trend pattern: {e}")
        
        return {
            "price_trend": price_trend,
            "trend_strength": trend_strength,
            "trend_duration": self._calculate_trend_duration(historical_prices),
            "pattern_type": pattern_type,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "trend_prediction": trend_prediction,
            "data_points": len(historical_prices),
            "period": self._get_period(historical_prices),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _extract_historical_prices(
        self,
        price_data: Dict[str, Any],
        symbol_data: Dict[str, Any]
    ) -> List[float]:
        """
        Extract historical price data
        
        Args:
            price_data: Current price data
            symbol_data: Full symbol data
            
        Returns:
            List of historical prices (most recent first)
        """
        # In a real implementation, this would fetch historical prices from MCP
        # For now, return empty list or simulate with current price
        current_price = price_data.get("current_price") or price_data.get("price")
        
        if current_price:
            # Simulate historical prices (in real implementation, fetch from MCP)
            # Return empty list to trigger basic trend analysis
            return []
        
        return []
    
    def _basic_trend_analysis(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        company_info: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform basic trend analysis when historical data is unavailable
        
        Args:
            symbol: Stock symbol
            price_data: Price data
            company_info: Company info
            state: AgentState dictionary
            
        Returns:
            Basic trend analysis dictionary
        """
        current_price = price_data.get("current_price") or price_data.get("price")
        
        # Generate basic trend prediction using LLM
        prompt = self._build_basic_trend_prompt(symbol, current_price, company_info)
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.completion(messages, temperature=0.7, max_tokens=800)
            content = self.llm_client.get_content(response)
            
            # Track token usage
            if hasattr(response, "usage"):
                self.token_tracker.track_llm_call(state, self.name, response)
            
            return {
                "price_trend": "unknown",
                "trend_strength": "unknown",
                "trend_duration": "unknown",
                "pattern_type": "insufficient_data",
                "support_level": None,
                "resistance_level": None,
                "trend_prediction": {
                    "direction": "unknown",
                    "confidence": "low",
                    "timeframe": "unknown",
                    "reasoning": content
                },
                "data_points": 1,
                "period": "current",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating basic trend analysis: {e}")
            return {
                "price_trend": "unknown",
                "trend_strength": "unknown",
                "error": str(e)
            }
    
    def _calculate_price_trend(self, prices: List[float]) -> str:
        """
        Calculate price trend direction
        
        Args:
            prices: List of historical prices (most recent first)
            
        Returns:
            Trend direction: "upward", "downward", or "sideways"
        """
        if len(prices) < 2:
            return "unknown"
        
        # Simple linear regression slope
        n = len(prices)
        x = list(range(n))
        y = prices
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "sideways"
        
        slope = numerator / denominator
        
        # Threshold for trend determination (adjust based on price scale)
        threshold = y_mean * 0.01  # 1% of average price
        
        if slope > threshold:
            return "upward"
        elif slope < -threshold:
            return "downward"
        else:
            return "sideways"
    
    def _calculate_trend_strength(self, prices: List[float]) -> str:
        """
        Calculate trend strength
        
        Args:
            prices: List of historical prices
            
        Returns:
            Trend strength: "strong", "moderate", or "weak"
        """
        if len(prices) < 3:
            return "weak"
        
        # Calculate coefficient of variation
        if statistics.mean(prices) == 0:
            return "weak"
        
        cv = statistics.stdev(prices) / statistics.mean(prices)
        
        # Calculate trend consistency
        trend_direction = self._calculate_price_trend(prices)
        if trend_direction == "sideways":
            return "weak"
        
        # Strong trend: low variation and consistent direction
        if cv < 0.05:
            return "strong"
        elif cv < 0.15:
            return "moderate"
        else:
            return "weak"
    
    def _identify_pattern(self, prices: List[float]) -> str:
        """
        Identify price pattern type
        
        Args:
            prices: List of historical prices
            
        Returns:
            Pattern type string
        """
        if len(prices) < 5:
            return "insufficient_data"
        
        # Simple pattern identification
        trend = self._calculate_price_trend(prices)
        
        # Check for triangle patterns
        if self._is_ascending_triangle(prices):
            return "ascending_triangle"
        elif self._is_descending_triangle(prices):
            return "descending_triangle"
        
        # Check for head and shoulders (simplified)
        if self._is_head_and_shoulders(prices):
            return "head_and_shoulders"
        
        # Default to trend-based pattern
        if trend == "upward":
            return "uptrend"
        elif trend == "downward":
            return "downtrend"
        else:
            return "sideways"
    
    def _is_ascending_triangle(self, prices: List[float]) -> bool:
        """Check if prices form an ascending triangle pattern"""
        if len(prices) < 5:
            return False
        
        # Simplified check: increasing lows, similar highs
        first_half = prices[:len(prices)//2]
        second_half = prices[len(prices)//2:]
        
        if min(first_half) < min(second_half) and max(first_half) == max(second_half):
            return True
        
        return False
    
    def _is_descending_triangle(self, prices: List[float]) -> bool:
        """Check if prices form a descending triangle pattern"""
        if len(prices) < 5:
            return False
        
        # Simplified check: decreasing highs, similar lows
        first_half = prices[:len(prices)//2]
        second_half = prices[len(prices)//2:]
        
        if max(first_half) > max(second_half) and min(first_half) == min(second_half):
            return True
        
        return False
    
    def _is_head_and_shoulders(self, prices: List[float]) -> bool:
        """Check if prices form a head and shoulders pattern"""
        if len(prices) < 7:
            return False
        
        # Simplified check: three peaks with middle peak highest
        # This is a very simplified version
        return False  # Placeholder
    
    def _calculate_support_resistance(
        self,
        prices: List[float]
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Calculate support and resistance levels
        
        Args:
            prices: List of historical prices
            
        Returns:
            Tuple of (support_level, resistance_level)
        """
        if len(prices) < 3:
            return None, None
        
        support_level = min(prices)
        resistance_level = max(prices)
        
        return support_level, resistance_level
    
    def _calculate_trend_duration(self, prices: List[float]) -> str:
        """
        Calculate trend duration
        
        Args:
            prices: List of historical prices
            
        Returns:
            Duration string
        """
        # In a real implementation, this would use actual timestamps
        # For now, estimate based on data points
        data_points = len(prices)
        
        if data_points < 5:
            return "short_term"
        elif data_points < 20:
            return "medium_term"
        else:
            return "long_term"
    
    def _get_period(self, prices: List[float]) -> str:
        """
        Get time period for the data
        
        Args:
            prices: List of historical prices
            
        Returns:
            Period string
        """
        # In a real implementation, this would use actual timestamps
        data_points = len(prices)
        
        if data_points < 5:
            return "days"
        elif data_points < 20:
            return "weeks"
        else:
            return "months"
    
    def _query_historical_trends(
        self,
        symbol: str,
        price_trend: str,
        pattern_type: str
    ) -> List[Dict[str, Any]]:
        """
        Query historical trends from vector DB
        
        Args:
            symbol: Stock symbol
            price_trend: Current price trend
            pattern_type: Current pattern type
            
        Returns:
            List of historical trends
        """
        if not self.chroma_client:
            return []
        
        try:
            # Create query text from trend characteristics
            query_text = f"{symbol} {price_trend} trend {pattern_type} pattern"
            
            # Query vector DB (simplified - would need embedding pipeline in real implementation)
            logger.debug(f"Querying historical trends for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Error querying historical trends: {e}")
            return []
    
    def _store_trend_pattern(
        self,
        symbol: str,
        price_trend: str,
        pattern_type: str,
        trend_strength: str
    ):
        """
        Store trend pattern in vector DB
        
        Args:
            symbol: Stock symbol
            price_trend: Price trend
            pattern_type: Pattern type
            trend_strength: Trend strength
        """
        if not self.chroma_client:
            return
        
        try:
            # Create trend description
            trend_description = f"{symbol} {price_trend} trend {pattern_type} pattern {trend_strength} strength"
            
            # Store in vector DB (simplified - would need embedding pipeline in real implementation)
            logger.debug(f"Storing trend pattern for {symbol}")
        except Exception as e:
            logger.error(f"Error storing trend pattern: {e}")
    
    def _generate_trend_prediction(
        self,
        symbol: str,
        price_trend: str,
        trend_strength: str,
        pattern_type: str,
        support_level: Optional[float],
        resistance_level: Optional[float],
        historical_prices: List[float],
        historical_trends: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trend prediction using LLM
        
        Args:
            symbol: Stock symbol
            price_trend: Price trend direction
            trend_strength: Trend strength
            pattern_type: Pattern type
            support_level: Support level
            resistance_level: Resistance level
            historical_prices: Historical prices
            historical_trends: Historical trends from vector DB
            state: AgentState dictionary
            
        Returns:
            Trend prediction dictionary
        """
        prompt = self._build_trend_prediction_prompt(
            symbol,
            price_trend,
            trend_strength,
            pattern_type,
            support_level,
            resistance_level,
            historical_prices,
            historical_trends
        )
        
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
            
            # Parse prediction from LLM response (simplified)
            return {
                "direction": price_trend,
                "confidence": trend_strength,
                "timeframe": "short_term",  # Would be extracted from LLM response
                "reasoning": content
            }
        except Exception as e:
            logger.error(f"Error generating trend prediction: {e}")
            return {
                "direction": price_trend,
                "confidence": "low",
                "timeframe": "unknown",
                "reasoning": f"Error: {str(e)}"
            }
    
    def _build_basic_trend_prompt(
        self,
        symbol: str,
        current_price: Optional[float],
        company_info: Dict[str, Any]
    ) -> str:
        """Build basic trend prompt when historical data is unavailable"""
        return f"""Analyze the current market position for {symbol}:

Current Price: ${current_price if current_price else 'N/A'}
Sector: {company_info.get('sector', 'N/A')}
Industry: {company_info.get('industry', 'N/A')}

Provide a basic trend analysis including:
1. Current market position assessment
2. Potential trend directions based on sector/industry
3. Key factors to monitor
4. Risk considerations

Note: Historical price data is limited. Base your analysis on current market conditions and sector trends."""
    
    def _build_trend_prediction_prompt(
        self,
        symbol: str,
        price_trend: str,
        trend_strength: str,
        pattern_type: str,
        support_level: Optional[float],
        resistance_level: Optional[float],
        historical_prices: List[float],
        historical_trends: List[Dict[str, Any]]
    ) -> str:
        """Build trend prediction prompt"""
        price_range = f"${min(historical_prices):.2f} - ${max(historical_prices):.2f}" if historical_prices else "N/A"
        
        return f"""Analyze the following price trend data for {symbol}:

Historical Data:
- Price Range: {price_range}
- Data Points: {len(historical_prices)}
- Price Trend: {price_trend}
- Trend Strength: {trend_strength}
- Pattern Type: {pattern_type}
- Support Level: ${support_level:.2f if support_level else 'N/A'}
- Resistance Level: ${resistance_level:.2f if resistance_level else 'N/A'}

Historical Patterns Found: {len(historical_trends)} similar patterns

Provide trend analysis including:
1. Trend confirmation and strength
2. Pattern identification and interpretation
3. Support and resistance levels analysis
4. Trend prediction and timeframe
5. Risk factors and considerations

Format your response as structured analysis."""
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for trend agent"""
        return """You are a financial market trend analysis expert specializing in technical analysis and pattern recognition.

Your role is to:
- Analyze price trends and patterns objectively
- Identify support and resistance levels
- Provide trend predictions with appropriate confidence levels
- Highlight risk factors and considerations
- Base predictions on data-driven analysis

Always be clear about the confidence level of your predictions and the factors that influence them."""
