"""MCP client wrapper for Phase 2 and Phase 3"""

from typing import Dict, Any, Optional
from loguru import logger
import httpx
import yfinance as yf
from datetime import datetime

from src.config import settings


class MCPClient:
    """
    MCP client wrapper for Yahoo Finance integration.
    For Phase 2, we use yfinance directly. In later phases, this can be extended
    to support HTTP-based MCP servers.
    """
    
    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize MCP client
        
        Args:
            server_url: Optional MCP server URL (for future HTTP-based MCP servers)
        """
        self.server_url = server_url
        logger.info(f"Initialized MCPClient (server_url={server_url})")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool response dictionary
            
        Raises:
            Exception: If tool call fails
        """
        logger.debug(f"Calling MCP tool: {tool_name} with arguments: {arguments}")
        
        try:
            # Yahoo Finance tools (Phase 2)
            if tool_name == "yahoo_finance_get_price":
                return self._get_stock_price(arguments.get("symbol"))
            elif tool_name == "yahoo_finance_get_info":
                return self._get_company_info(arguments.get("symbol"))
            
            # Alpha Vantage tools (Phase 3)
            elif tool_name == "alpha_vantage_get_quote":
                return self._alpha_vantage_get_quote(arguments.get("symbol"))
            elif tool_name == "alpha_vantage_get_overview":
                return self._alpha_vantage_get_overview(arguments.get("symbol"))
            
            # FMP tools (Phase 3)
            elif tool_name == "fmp_get_quote":
                return self._fmp_get_quote(arguments.get("symbol"))
            elif tool_name == "fmp_get_profile":
                return self._fmp_get_profile(arguments.get("symbol"))
            elif tool_name == "fmp_get_key_metrics":
                return self._fmp_get_key_metrics(arguments.get("symbol"))
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f"MCP tool call failed: {tool_name}, error: {e}")
            raise
    
    def _get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price using yfinance
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with price data
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            current_data = ticker.history(period="1d")
            
            price_data = {
                "symbol": symbol,
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose"),
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Validate we got price data
            if price_data["current_price"] is None:
                raise ValueError(f"No price data available for {symbol}")
            
            logger.debug(f"Retrieved price data for {symbol}: ${price_data['current_price']}")
            return price_data
            
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            raise
    
    def _get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get company information using yfinance
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with company info
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            company_info = {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "description": info.get("longBusinessSummary"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Retrieved company info for {symbol}: {company_info.get('name')}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            raise
    
    def _alpha_vantage_get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock quote from Alpha Vantage
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with quote data
        """
        if not settings.ALPHA_VANTAGE_API_KEY:
            raise ValueError("ALPHA_VANTAGE_API_KEY not configured")
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            quote = data.get("Global Quote", {})
            if not quote:
                raise ValueError(f"No quote data returned for {symbol}")
            
            return {
                "symbol": symbol,
                "current_price": float(quote.get("05. price", 0)),
                "previous_close": float(quote.get("08. previous close", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%"),
                "volume": int(quote.get("06. volume", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "open": float(quote.get("02. open", 0)),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alpha_vantage"
            }
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage quote for {symbol}: {e}")
            raise
    
    def _alpha_vantage_get_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company overview from Alpha Vantage
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with company overview
        """
        if not settings.ALPHA_VANTAGE_API_KEY:
            raise ValueError("ALPHA_VANTAGE_API_KEY not configured")
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": settings.ALPHA_VANTAGE_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if "Symbol" not in data:
                raise ValueError(f"No overview data returned for {symbol}")
            
            return {
                "symbol": symbol,
                "name": data.get("Name", ""),
                "sector": data.get("Sector", ""),
                "industry": data.get("Industry", ""),
                "description": data.get("Description", ""),
                "market_cap": data.get("MarketCapitalization", ""),
                "pe_ratio": data.get("PERatio", ""),
                "eps": data.get("EPS", ""),
                "dividend_yield": data.get("DividendYield", ""),
                "52_week_high": data.get("52WeekHigh", ""),
                "52_week_low": data.get("52WeekLow", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alpha_vantage"
            }
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage overview for {symbol}: {e}")
            raise
    
    def _fmp_get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock quote from Financial Modeling Prep
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with quote data
        """
        if not settings.FMP_API_KEY:
            raise ValueError("FMP_API_KEY not configured")
        
        try:
            url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
            params = {
                "apikey": settings.FMP_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if not data or len(data) == 0:
                raise ValueError(f"No quote data returned for {symbol}")
            
            quote = data[0]
            return {
                "symbol": symbol,
                "current_price": quote.get("price", 0),
                "previous_close": quote.get("previousClose", 0),
                "change": quote.get("change", 0),
                "change_percent": quote.get("changesPercentage", 0),
                "volume": quote.get("volume", 0),
                "high": quote.get("dayHigh", 0),
                "low": quote.get("dayLow", 0),
                "open": quote.get("open", 0),
                "market_cap": quote.get("marketCap", 0),
                "pe_ratio": quote.get("pe", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fmp"
            }
        except Exception as e:
            logger.error(f"Error fetching FMP quote for {symbol}: {e}")
            raise
    
    def _fmp_get_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get company profile from Financial Modeling Prep
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with company profile
        """
        if not settings.FMP_API_KEY:
            raise ValueError("FMP_API_KEY not configured")
        
        try:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
            params = {
                "apikey": settings.FMP_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if not data or len(data) == 0:
                raise ValueError(f"No profile data returned for {symbol}")
            
            profile = data[0]
            return {
                "symbol": symbol,
                "name": profile.get("companyName", ""),
                "sector": profile.get("sector", ""),
                "industry": profile.get("industry", ""),
                "description": profile.get("description", ""),
                "website": profile.get("website", ""),
                "ceo": profile.get("ceo", ""),
                "employees": profile.get("fullTimeEmployees", 0),
                "market_cap": profile.get("mktCap", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fmp"
            }
        except Exception as e:
            logger.error(f"Error fetching FMP profile for {symbol}: {e}")
            raise
    
    def _fmp_get_key_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get key metrics from Financial Modeling Prep
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with key metrics
        """
        if not settings.FMP_API_KEY:
            raise ValueError("FMP_API_KEY not configured")
        
        try:
            url = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{symbol}"
            params = {
                "apikey": settings.FMP_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if not data or len(data) == 0:
                raise ValueError(f"No key metrics returned for {symbol}")
            
            metrics = data[0]
            return {
                "symbol": symbol,
                "pe_ratio": metrics.get("peRatioTTM", 0),
                "price_to_sales": metrics.get("priceToSalesRatioTTM", 0),
                "price_to_book": metrics.get("priceToBookRatioTTM", 0),
                "ev_to_revenue": metrics.get("enterpriseValueOverEBITDATTM", 0),
                "roe": metrics.get("roeTTM", 0),
                "roa": metrics.get("roaTTM", 0),
                "current_ratio": metrics.get("currentRatioTTM", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fmp"
            }
        except Exception as e:
            logger.error(f"Error fetching FMP key metrics for {symbol}: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client (if using HTTP-based MCP)"""
        # For yfinance, nothing to close, but keep for future compatibility
        pass
