"""Base agent class for Phase 2"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from loguru import logger


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str):
        """
        Initialize base agent
        
        Args:
            name: Agent name
        """
        self.name = name
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        pass
    
    def validate_state(self, state: Dict[str, Any]) -> bool:
        """
        Validate required state fields
        
        Args:
            state: AgentState dictionary
            
        Returns:
            True if all required fields exist
        """
        required_fields = ["transaction_id", "session_id", "query"]
        missing = [field for field in required_fields if field not in state]
        if missing:
            logger.warning(f"{self.name}: Missing required state fields: {missing}")
            return False
        return True
    
    def log_execution(self, state: Dict[str, Any]):
        """
        Log agent execution
        
        Args:
            state: AgentState dictionary
        """
        logger.info(f"{self.name} executing for transaction {state.get('transaction_id')}")
