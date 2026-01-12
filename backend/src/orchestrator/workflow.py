"""LangGraph workflow for Phase 2, Phase 3, Phase 5, Phase 6, and Phase 7"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, List, Optional
from loguru import logger

from src.agents.research_agent import ResearchAgent
from src.agents.analyst_agent import AnalystAgent
from src.agents.reporting_agent import ReportingAgent
from src.agents.edgar_agent import EdgarAgent
from src.agents.comparison_agent import ComparisonAgent
from src.agents.trend_agent import TrendAgent
from src.models.state import AgentState
from src.utils.context_merger import ContextMerger
from src.utils.query_intent import QueryIntentClassifier
from src.utils.query_parser import QueryParser
from src.utils.llm_client import LLMClient
from src.services.progress_manager import ProgressTracker


class MyFinGPTWorkflow:
    """LangGraph workflow for agent orchestration (Phase 2-3, Phase 5, Phase 6)"""
    
    def __init__(
        self,
        research_agent: ResearchAgent,
        analyst_agent: Optional[AnalystAgent] = None,
        reporting_agent: Optional[ReportingAgent] = None,
        edgar_agent: Optional[EdgarAgent] = None,
        comparison_agent: Optional[ComparisonAgent] = None,
        trend_agent: Optional[TrendAgent] = None,
        enable_parallel: bool = True,
        enable_conditional: bool = True,
        query_parser: Optional[QueryParser] = None
    ):
        """
        Initialize workflow
        
        Args:
            research_agent: Research Agent instance
            analyst_agent: Analyst Agent instance (Phase 3)
            reporting_agent: Reporting Agent instance (Phase 3)
            edgar_agent: EDGAR Agent instance (Phase 5)
            comparison_agent: Comparison Agent instance (Phase 6)
            trend_agent: Trend Agent instance (Phase 6)
            enable_parallel: Enable parallel execution for multiple symbols (Phase 3)
            enable_conditional: Enable conditional routing based on query intent (Phase 6)
            query_parser: Query parser for symbol extraction (optional)
        """
        self.research_agent = research_agent
        self.analyst_agent = analyst_agent
        self.reporting_agent = reporting_agent
        self.edgar_agent = edgar_agent
        self.comparison_agent = comparison_agent
        self.trend_agent = trend_agent
        self.enable_parallel = enable_parallel
        self.enable_conditional = enable_conditional
        
        # Initialize query parser and intent classifier
        if enable_conditional:
            llm_client = LLMClient()
            if query_parser is None:
                query_parser = QueryParser(llm_client=llm_client)
            self.intent_classifier = QueryIntentClassifier(
                llm_client=llm_client,
                query_parser=query_parser
            )
        else:
            self.intent_classifier = None
        
        self.progress_tracker: Optional[ProgressTracker] = None  # Phase 7: Progress tracking
        self.graph = self._build_graph()
        logger.info(
            f"MyFinGPTWorkflow initialized "
            f"(Phase 5: edgar={edgar_agent is not None}, "
            f"Phase 6: comparison={comparison_agent is not None}, trend={trend_agent is not None}, "
            f"parallel={enable_parallel}, conditional={enable_conditional})"
        )
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow with conditional routing (Phase 6)
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        if self.enable_parallel:
            workflow.add_node("research_parallel", self._research_parallel_node)
        else:
            workflow.add_node("research", self._research_node)
        
        # Phase 5: Add EDGAR agent node
        if self.edgar_agent:
            workflow.add_node("edgar", self._edgar_node)
        
        if self.analyst_agent:
            workflow.add_node("analyst", self._analyst_node)
        
        # Phase 6: Add Comparison and Trend agent nodes
        if self.comparison_agent:
            workflow.add_node("comparison", self._comparison_node)
        
        if self.trend_agent:
            workflow.add_node("trend", self._trend_node)
        
        # Phase 6: Add conditional routing node
        if self.enable_conditional and (self.comparison_agent or self.trend_agent):
            workflow.add_node("route_advanced", self._route_advanced_agents)
        
        if self.reporting_agent:
            workflow.add_node("reporting", self._reporting_node)
        
        # Set entry point
        if self.enable_parallel:
            workflow.set_entry_point("research_parallel")
        else:
            workflow.set_entry_point("research")
        
        # Build edges with conditional routing
        self._build_edges(workflow)
        
        # Compile graph
        compiled = workflow.compile()
        logger.info("LangGraph workflow compiled successfully")
        return compiled
    
    def _build_edges(self, workflow: StateGraph):
        """
        Build workflow edges with conditional routing (Phase 6)
        
        Args:
            workflow: StateGraph instance
        """
        # Research -> EDGAR (if exists) -> Analyst or Advanced Agents
        research_node = "research_parallel" if self.enable_parallel else "research"
        
        if self.edgar_agent:
            workflow.add_edge(research_node, "edgar")
            after_research = "edgar"
        else:
            after_research = research_node
        
        # After research/edgar: Analyst or Advanced Agents
        if self.analyst_agent:
            workflow.add_edge(after_research, "analyst")
            after_analyst = "analyst"
        else:
            after_analyst = after_research
        
        # Phase 6: Conditional routing for Comparison and Trend agents
        if self.enable_conditional and (self.comparison_agent or self.trend_agent):
            workflow.add_edge(after_analyst, "route_advanced")
            
            # Route to Comparison and/or Trend agents based on query intent
            if self.comparison_agent and self.trend_agent:
                # Both agents can run in parallel
                workflow.add_edge("route_advanced", "comparison")
                workflow.add_edge("route_advanced", "trend")
                # Merge after both complete
                workflow.add_edge("comparison", "reporting")
                workflow.add_edge("trend", "reporting")
            elif self.comparison_agent:
                workflow.add_edge("route_advanced", "comparison")
                workflow.add_edge("comparison", "reporting")
            elif self.trend_agent:
                workflow.add_edge("route_advanced", "trend")
                workflow.add_edge("trend", "reporting")
            else:
                workflow.add_edge("route_advanced", "reporting")
        else:
            # No conditional routing, go directly to reporting
            if self.reporting_agent:
                workflow.add_edge(after_analyst, "reporting")
            else:
                workflow.add_edge(after_analyst, END)
        
        # Reporting -> END
        if self.reporting_agent:
            workflow.add_edge("reporting", END)
    
    def _research_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research node wrapper (sequential)
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        agent_name = "ResearchAgent"
        try:
            if self.progress_tracker:
                self.progress_tracker.start_agent(agent_name, ["Gathering market data", "Fetching company information"])
            result = self.research_agent.execute(state)
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            return result
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _research_parallel_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research node wrapper (parallel execution for multiple symbols)
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary with merged results
        """
        agent_name = "ResearchAgent"
        symbols = state.get("symbols", [])
        
        try:
            if self.progress_tracker:
                tasks = [f"Gathering data for {symbol}" for symbol in symbols]
                self.progress_tracker.start_agent(agent_name, tasks)
            
            if len(symbols) <= 1:
                # Single symbol, no need for parallel execution
                result = self.research_agent.execute(state)
                if self.progress_tracker:
                    self.progress_tracker.complete_agent(agent_name)
                return result
            
            # Execute research for each symbol in parallel
            # Note: LangGraph doesn't natively support parallel execution within a node,
            # so we simulate it by creating separate states and merging results
            logger.info(f"Executing parallel research for {len(symbols)} symbols")
            
            # For now, execute sequentially but prepare for true parallel execution
            # In a production system, you might use asyncio or threading here
            results = []
            for symbol in symbols:
                symbol_state = state.copy()
                symbol_state["symbols"] = [symbol]
                result = self.research_agent.execute(symbol_state)
                results.append(result)
            
            # Merge results
            merged_state = state.copy()
            merged_state["research_data"] = ContextMerger.merge_research_data(results)
            merged_state["citations"] = ContextMerger.merge_citations(results)
            merged_state["errors"] = ContextMerger.merge_errors(results)
            merged_state["token_usage"] = ContextMerger.merge_token_usage(results)
            
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            
            return merged_state
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _analyst_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyst node wrapper
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.analyst_agent:
            logger.warning("Analyst agent not configured, skipping")
            return state
        
        agent_name = "AnalystAgent"
        try:
            if self.progress_tracker:
                self.progress_tracker.start_agent(agent_name, ["Analyzing data", "Generating insights"])
            result = self.analyst_agent.execute(state)
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            return result
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _edgar_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        EDGAR node wrapper (Phase 5)
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.edgar_agent:
            logger.warning("EDGAR agent not configured, skipping")
            return state
        
        agent_name = "EdgarAgent"
        try:
            if self.progress_tracker:
                self.progress_tracker.start_agent(agent_name, ["Fetching SEC filings", "Processing documents"])
            result = self.edgar_agent.execute(state)
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            return result
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _reporting_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reporting node wrapper
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.reporting_agent:
            logger.warning("Reporting agent not configured, skipping")
            return state
        
        agent_name = "ReportingAgent"
        try:
            if self.progress_tracker:
                self.progress_tracker.start_agent(agent_name, ["Generating report", "Formatting output"])
            result = self.reporting_agent.execute(state)
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            return result
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _comparison_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comparison node wrapper (Phase 6)
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.comparison_agent:
            logger.warning("Comparison agent not configured, skipping")
            return state
        
        agent_name = "ComparisonAgent"
        try:
            if self.progress_tracker:
                self.progress_tracker.start_agent(agent_name, ["Comparing entities", "Analyzing differences"])
            result = self.comparison_agent.execute(state)
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            return result
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _trend_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trend node wrapper (Phase 6)
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary
        """
        if not self.trend_agent:
            logger.warning("Trend agent not configured, skipping")
            return state
        
        agent_name = "TrendAgent"
        try:
            if self.progress_tracker:
                self.progress_tracker.start_agent(agent_name, ["Analyzing trends", "Identifying patterns"])
            result = self.trend_agent.execute(state)
            if self.progress_tracker:
                self.progress_tracker.complete_agent(agent_name)
            return result
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.fail_agent(agent_name, str(e))
            raise
    
    def _route_advanced_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to advanced agents based on query intent (Phase 6)
        
        This node classifies the query and sets flags for conditional execution.
        If query was already parsed in API router, use that information.
        Otherwise, classify using intent classifier.
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary with query_type and routing flags
        """
        # If query was already parsed in API router, use that information
        if "query_type" in state and state.get("query_type") and "intent_flags" in state:
            logger.info(f"Using pre-parsed query type: {state['query_type']}")
            return state
        
        # Otherwise, classify using intent classifier
        if not self.intent_classifier:
            # No classifier, skip routing
            logger.warning("No intent classifier available, skipping routing")
            return state
        
        query = state.get("query", "")
        symbols = state.get("symbols", [])
        
        # Classify query intent (classifier will extract symbols if not provided)
        classification = self.intent_classifier.classify(query, symbols=symbols)
        
        # Update state with classification
        state["query_type"] = classification.get("query_type", "single_entity")
        state["intent_flags"] = classification.get("intent_flags", {})
        
        # Update symbols if classifier extracted them
        if classification.get("symbols") and not symbols:
            state["symbols"] = classification.get("symbols", [])
            logger.info(f"Intent classifier extracted symbols: {state['symbols']}")
        
        logger.info(f"Query classified as: {state['query_type']}, flags={state.get('intent_flags', {})}")
        return state
    
    def execute(
        self,
        state: Dict[str, Any],
        progress_tracker: Optional[ProgressTracker] = None
    ) -> Dict[str, Any]:
        """
        Execute the workflow
        
        Args:
            state: Initial AgentState dictionary
            progress_tracker: Optional progress tracker for Phase 7
            
        Returns:
            Final AgentState dictionary
        """
        # Set progress tracker for this execution
        self.progress_tracker = progress_tracker
        
        logger.info(f"Executing workflow for transaction {state.get('transaction_id')}")
        
        try:
            result = self.graph.invoke(state)
            logger.info(f"Workflow completed for transaction {state.get('transaction_id')}")
            return result
        finally:
            # Clean up progress tracker
            self.progress_tracker = None
