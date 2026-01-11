"""Research Agent implementation for Phase 2 with Phase 4 Knowledge Layer integration"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.mcp.mcp_client import MCPClient
from src.services.ingestion_service import IngestionService


class ResearchAgent(BaseAgent):
    """Research Agent: Fetches financial data from MCP servers"""
    
    def __init__(self, mcp_client: MCPClient, ingestion_service: Optional[IngestionService] = None):
        """
        Initialize Research Agent
        
        Args:
            mcp_client: MCP client instance
            ingestion_service: IngestionService for storing data in knowledge layer (optional)
        """
        super().__init__("ResearchAgent")
        self.mcp_client = mcp_client
        self.ingestion_service = ingestion_service
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute research agent
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.validate_state(state):
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append("Invalid state for ResearchAgent")
            return state
        
        self.log_execution(state)
        
        symbols = state.get("symbols", [])
        research_data = {}
        
        # Ensure citations list exists
        if "citations" not in state:
            state["citations"] = []
        
        for symbol in symbols:
            try:
                # Fetch stock price from Yahoo Finance MCP
                price_data = self.mcp_client.call_tool(
                    "yahoo_finance_get_price",
                    {"symbol": symbol}
                )
                
                # Fetch company info
                company_info = self.mcp_client.call_tool(
                    "yahoo_finance_get_info",
                    {"symbol": symbol}
                )
                
                research_data[symbol] = {
                    "price": price_data,
                    "company_info": company_info,
                    "source": "yahoo_finance",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Add citation
                state["citations"].append({
                    "source": "Yahoo Finance",
                    "symbol": symbol,
                    "type": "price_data"
                })
                
                # Phase 4: Store company info in knowledge layer if ingestion service available
                if self.ingestion_service:
                    try:
                        # Extract company name for news ingestion
                        company_name = company_info.get("name", symbol)
                        # Create a simple news-like entry for company information
                        # In a real scenario, this would be actual news articles
                        self.ingestion_service.ingest_news_article(
                            title=f"Company Information: {company_name}",
                            content=f"Company: {company_name}\nSector: {company_info.get('sector', 'N/A')}\nIndustry: {company_info.get('industry', 'N/A')}\nCurrent Price: ${price_data.get('current_price', 'N/A')}",
                            symbol=symbol,
                            source="Yahoo Finance",
                            metadata={"type": "company_info", "agent": "ResearchAgent"}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to ingest data to knowledge layer for {symbol}: {e}")
                
                logger.info(f"Successfully fetched data for {symbol}")
                
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(f"Failed to fetch data for {symbol}: {str(e)}")
        
        state["research_data"] = research_data
        state["updated_at"] = datetime.utcnow()
        
        return state
