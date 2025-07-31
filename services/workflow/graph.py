"""LangGraph workflow definition for coordination analysis.

This module defines the LangGraph workflow that orchestrates all agents
for performing coordination analysis of attack sessions.
"""

from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from services.llm import LLMClient

from .agents import (
    ConfidenceScorerAgent,
    ElasticsearchEnricherAgent,
    OrchestratorAgent,
    PatternAnalyzerAgent,
    ToolCoordinatorAgent,
)
from .state import CoordinationAnalysisState

logger = structlog.get_logger(__name__)


def create_coordination_analysis_workflow(
    llm_client: LLMClient = None,
) -> StateGraph:
    """Create the coordination analysis workflow.

    Args:
        llm_client: LLM client for agent initialization

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize agents
    orchestrator = OrchestratorAgent(llm_client=llm_client)
    pattern_analyzer = PatternAnalyzerAgent(llm_client=llm_client)
    tool_coordinator = ToolCoordinatorAgent()
    confidence_scorer = ConfidenceScorerAgent(llm_client=llm_client)
    elasticsearch_enricher = ElasticsearchEnricherAgent()

    # Create workflow graph
    workflow = StateGraph(CoordinationAnalysisState)

    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node(orchestrator))
    workflow.add_node("pattern_analyzer", pattern_analyzer_node(pattern_analyzer))
    workflow.add_node("tool_coordinator", tool_coordinator_node(tool_coordinator))
    workflow.add_node("confidence_scorer", confidence_scorer_node(confidence_scorer))
    workflow.add_node(
        "elasticsearch_enricher", elasticsearch_enricher_node(elasticsearch_enricher)
    )

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Add conditional edges
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "pattern_analyzer": "pattern_analyzer",
            "confidence_scorer": "confidence_scorer",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "pattern_analyzer",
        route_after_pattern_analysis,
        {
            "tool_coordinator": "tool_coordinator",
            "confidence_scorer": "confidence_scorer",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "tool_coordinator",
        route_after_tool_coordination,
        {
            "confidence_scorer": "confidence_scorer",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "confidence_scorer",
        route_after_confidence_scoring,
        {
            "elasticsearch_enricher": "elasticsearch_enricher",
            "end": END,
        },
    )

    # Add final edge
    workflow.add_edge("elasticsearch_enricher", END)

    return workflow.compile()


def orchestrator_node(orchestrator: OrchestratorAgent):
    """Create orchestrator node function.

    Args:
        orchestrator: Orchestrator agent instance

    Returns:
        Node function for orchestrator
    """

    async def node(state: CoordinationAnalysisState) -> CoordinationAnalysisState:
        """Orchestrator node function.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing orchestrator node")
        return await orchestrator.analyze_initial_data(state)

    return node


def pattern_analyzer_node(pattern_analyzer: PatternAnalyzerAgent):
    """Create pattern analyzer node function.

    Args:
        pattern_analyzer: Pattern analyzer agent instance

    Returns:
        Node function for pattern analyzer
    """

    async def node(state: CoordinationAnalysisState) -> CoordinationAnalysisState:
        """Pattern analyzer node function.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing pattern analyzer node")
        return await pattern_analyzer.analyze_patterns(state)

    return node


def tool_coordinator_node(tool_coordinator: ToolCoordinatorAgent):
    """Create tool coordinator node function.

    Args:
        tool_coordinator: Tool coordinator agent instance

    Returns:
        Node function for tool coordinator
    """

    async def node(state: CoordinationAnalysisState) -> CoordinationAnalysisState:
        """Tool coordinator node function.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing tool coordinator node")
        return await tool_coordinator.execute_analysis_plan(state)

    return node


def confidence_scorer_node(confidence_scorer: ConfidenceScorerAgent):
    """Create confidence scorer node function.

    Args:
        confidence_scorer: Confidence scorer agent instance

    Returns:
        Node function for confidence scorer
    """

    async def node(state: CoordinationAnalysisState) -> CoordinationAnalysisState:
        """Confidence scorer node function.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing confidence scorer node")
        return await confidence_scorer.calculate_coordination_score(state)

    return node


def elasticsearch_enricher_node(elasticsearch_enricher: ElasticsearchEnricherAgent):
    """Create Elasticsearch enricher node function.

    Args:
        elasticsearch_enricher: Elasticsearch enricher agent instance

    Returns:
        Node function for Elasticsearch enricher
    """

    async def node(state: CoordinationAnalysisState) -> CoordinationAnalysisState:
        """Elasticsearch enricher node function.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Executing Elasticsearch enricher node")
        return await elasticsearch_enricher.enrich_attack_sessions(state)

    return node


def route_after_orchestrator(state: CoordinationAnalysisState) -> str:
    """Route after orchestrator node.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    # Always go to pattern analysis first
    return "pattern_analyzer"


def route_after_pattern_analysis(state: CoordinationAnalysisState) -> str:
    """Route after pattern analysis node.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    # Check if deep analysis is needed
    if state.needs_deep_analysis:
        return "tool_coordinator"
    else:
        return "confidence_scorer"


def route_after_tool_coordination(state: CoordinationAnalysisState) -> str:
    """Route after tool coordination node.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    # Always go to confidence scoring after tool coordination
    return "confidence_scorer"


def route_after_confidence_scoring(state: CoordinationAnalysisState) -> str:
    """Route after confidence scoring node.

    Args:
        state: Current workflow state

    Returns:
        Next node name
    """
    # Check if deep analysis is needed for Elasticsearch enrichment
    if state.analysis_depth == "deep":
        return "elasticsearch_enricher"
    else:
        return "end"


async def run_coordination_analysis(
    attack_sessions: list[dict[str, Any]],
    analysis_depth: str = "standard",
    user_id: str = None,
    llm_client: LLMClient = None,
) -> dict[str, Any]:
    """Run coordination analysis workflow.

    Args:
        attack_sessions: List of attack session data
        analysis_depth: Analysis depth level
        user_id: User identifier
        llm_client: LLM client for analysis

    Returns:
        Analysis results dictionary
    """
    logger.info(
        "Starting coordination analysis workflow",
        session_count=len(attack_sessions),
        analysis_depth=analysis_depth,
        user_id=user_id,
    )

    try:
        # Create workflow
        workflow = create_coordination_analysis_workflow(llm_client=llm_client)

        # Initialize state
        initial_state = CoordinationAnalysisState(
            attack_sessions=attack_sessions,
            analysis_depth=analysis_depth,
            user_id=user_id,
        )

        # Run workflow
        final_state_dict = await workflow.ainvoke(initial_state)

        # Convert back to state object for logging
        final_state = CoordinationAnalysisState(**final_state_dict)

        logger.info(
            "Coordination analysis workflow completed",
            confidence_score=final_state.coordination_confidence,
            processing_time=final_state.get_processing_time(),
        )

        return final_state.to_result_dict()

    except Exception as e:
        logger.error("Coordination analysis workflow failed", error=str(e))
        raise


async def run_bulk_coordination_analysis(
    session_batches: list[list[dict[str, Any]]],
    analysis_depth: str = "standard",
    user_id: str = None,
    llm_client: LLMClient = None,
) -> list[dict[str, Any]]:
    """Run bulk coordination analysis workflow.

    Args:
        session_batches: List of attack session batches
        analysis_depth: Analysis depth level
        user_id: User identifier
        llm_client: LLM client for analysis

    Returns:
        List of analysis results dictionaries
    """
    logger.info(
        "Starting bulk coordination analysis workflow",
        batch_count=len(session_batches),
        analysis_depth=analysis_depth,
        user_id=user_id,
    )

    results = []

    for i, batch in enumerate(session_batches):
        try:
            logger.info(f"Processing batch {i + 1}/{len(session_batches)}")

            batch_result = await run_coordination_analysis(
                attack_sessions=batch,
                analysis_depth=analysis_depth,
                user_id=user_id,
                llm_client=llm_client,
            )

            batch_result["batch_index"] = i
            results.append(batch_result)

        except Exception as e:
            logger.error(f"Batch {i + 1} analysis failed", error=str(e))
            results.append(
                {
                    "batch_index": i,
                    "error": str(e),
                    "status": "failed",
                }
            )

    logger.info(
        "Bulk coordination analysis workflow completed",
        successful_batches=len([r for r in results if "error" not in r]),
        total_batches=len(results),
    )

    return results
