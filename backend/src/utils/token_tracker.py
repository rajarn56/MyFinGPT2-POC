"""Token usage tracking utility for Phase 2"""

from typing import Dict, Any, Optional
from loguru import logger


class TokenTracker:
    """Track token usage across agents"""
    
    @staticmethod
    def track_llm_call(state: Dict[str, Any], agent_name: str, response: Any):
        """
        Track token usage from LLM call
        
        Args:
            state: AgentState dictionary
            agent_name: Name of the agent making the call
            response: LLM response object (with usage attribute)
        """
        if not hasattr(response, "usage"):
            logger.warning(f"Response object does not have usage attribute for {agent_name}")
            return
        
        usage = response.usage
        
        # Initialize token_usage if not present
        if "token_usage" not in state:
            state["token_usage"] = {}
        
        # Initialize agent token usage if not present
        if agent_name not in state["token_usage"]:
            state["token_usage"][agent_name] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        
        # Add token usage
        state["token_usage"][agent_name]["prompt_tokens"] += usage.prompt_tokens
        state["token_usage"][agent_name]["completion_tokens"] += usage.completion_tokens
        state["token_usage"][agent_name]["total_tokens"] += usage.total_tokens
        
        logger.debug(
            f"Tracked tokens for {agent_name}: "
            f"{usage.total_tokens} total ({usage.prompt_tokens} prompt, {usage.completion_tokens} completion)"
        )
    
    @staticmethod
    def get_total_tokens(state: Dict[str, Any]) -> int:
        """
        Get total tokens used across all agents
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Total token count
        """
        if "token_usage" not in state:
            return 0
        
        total = 0
        for agent_usage in state["token_usage"].values():
            if isinstance(agent_usage, dict) and "total_tokens" in agent_usage:
                total += agent_usage["total_tokens"]
        
        return total
