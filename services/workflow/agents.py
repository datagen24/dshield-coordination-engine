"""Agent implementations for coordination analysis workflow.

This module contains the specialized agents that perform different aspects
of coordination analysis within the LangGraph workflow.
"""

from datetime import datetime
from typing import Any

import structlog

from services.llm import LLMClient

from .state import CoordinationAnalysisState

logger = structlog.get_logger(__name__)


class OrchestratorAgent:
    """Entry point agent that manages workflow and determines analysis strategy.

    This agent examines the initial attack session data and determines
    the appropriate analysis path and depth required.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """Initialize the orchestrator agent.

        Args:
            llm_client: LLM client for analysis decisions
        """
        self.llm_client = llm_client

    async def analyze_initial_data(
        self, state: CoordinationAnalysisState
    ) -> CoordinationAnalysisState:
        """Analyze initial data and determine analysis strategy.

        Args:
            state: Current workflow state

        Returns:
            Updated state with analysis plan
        """
        logger.info(
            "Orchestrator analyzing initial data",
            session_count=len(state.attack_sessions),
            analysis_depth=state.analysis_depth,
        )

        state.add_processing_step("orchestrator_analysis")
        state.workflow_start_time = datetime.utcnow()

        # Determine if deep analysis is needed
        needs_deep = await self._should_deep_analyze(state.attack_sessions)
        state.needs_deep_analysis = needs_deep

        # Create analysis plan
        state.analysis_plan = {
            "analysis_depth": state.analysis_depth,
            "needs_deep_analysis": needs_deep,
            "session_count": len(state.attack_sessions),
            "analysis_steps": self._determine_analysis_steps(state),
        }

        logger.info(
            "Orchestrator analysis complete",
            needs_deep_analysis=needs_deep,
            analysis_plan=state.analysis_plan,
        )

        return state

    async def _should_deep_analyze(self, sessions: list[dict[str, Any]]) -> bool:
        """Determine if deep analysis is required.

        Args:
            sessions: List of attack sessions

        Returns:
            True if deep analysis is needed, False otherwise
        """
        if len(sessions) < 3:
            return False

        # Quick heuristics for coordination indicators
        source_ips = {session.get("source_ip") for session in sessions}
        if len(source_ips) == 1:
            return False  # Single source, likely not coordinated

        # Check for timing patterns
        timestamps = []
        for session in sessions:
            timestamp = session.get("timestamp")
            if timestamp:
                # Convert string timestamp to datetime if needed
                if isinstance(timestamp, str):
                    try:
                        from datetime import datetime

                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    except ValueError:
                        continue
                timestamps.append(timestamp)

        if len(timestamps) >= 3:
            # Simple temporal clustering check
            sorted_times = sorted(timestamps)
            intervals = []
            for i in range(1, len(sorted_times)):
                interval = (sorted_times[i] - sorted_times[i - 1]).total_seconds()
                intervals.append(interval)

            # If many attacks within short intervals, might be coordinated
            short_intervals = [i for i in intervals if i < 300]  # 5 minutes
            if len(short_intervals) > len(intervals) * 0.5:
                return True

        return False

    def _determine_analysis_steps(self, state: CoordinationAnalysisState) -> list[str]:
        """Determine required analysis steps.

        Args:
            state: Current workflow state

        Returns:
            List of analysis steps to perform
        """
        steps = ["pattern_analysis"]

        if state.needs_deep_analysis:
            steps.extend(["tool_coordination", "confidence_scoring"])

        if state.analysis_depth == "deep":
            steps.append("elasticsearch_enrichment")

        return steps


class PatternAnalyzerAgent:
    """Agent for temporal and behavioral pattern analysis.

    This agent performs the core pattern analysis including temporal
    correlation, behavioral clustering, and infrastructure mapping.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """Initialize the pattern analyzer agent.

        Args:
            llm_client: LLM client for pattern analysis
        """
        self.llm_client = llm_client

    async def analyze_patterns(
        self, state: CoordinationAnalysisState
    ) -> CoordinationAnalysisState:
        """Analyze temporal and behavioral patterns.

        Args:
            state: Current workflow state

        Returns:
            Updated state with correlation results
        """
        logger.info(
            "Pattern analyzer starting analysis",
            session_count=len(state.attack_sessions),
        )

        state.add_processing_step("pattern_analysis")

        try:
            # Perform temporal analysis
            temporal_results = await self._temporal_analysis(state.attack_sessions)

            # Perform behavioral analysis
            behavioral_results = await self._behavioral_analysis(state.attack_sessions)

            # Perform infrastructure analysis
            infrastructure_results = await self._infrastructure_analysis(
                state.attack_sessions
            )

            # Combine results
            state.correlation_results = {
                "temporal": temporal_results,
                "behavioral": behavioral_results,
                "infrastructure": infrastructure_results,
            }

            logger.info(
                "Pattern analysis completed",
                temporal_score=temporal_results.get("correlation_score", 0.0),
                behavioral_score=behavioral_results.get("similarity_score", 0.0),
                infrastructure_score=infrastructure_results.get(
                    "clustering_score", 0.0
                ),
            )

        except Exception as e:
            logger.error("Pattern analysis failed", error=str(e))
            state.add_error(f"Pattern analysis failed: {str(e)}")
            # Set default values
            state.correlation_results = {
                "temporal": {"correlation_score": 0.0, "error": str(e)},
                "behavioral": {"similarity_score": 0.0, "error": str(e)},
                "infrastructure": {"clustering_score": 0.0, "error": str(e)},
            }

        return state

    async def _temporal_analysis(
        self, sessions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze temporal patterns in attack sessions.

        Args:
            sessions: List of attack sessions

        Returns:
            Temporal analysis results
        """
        if not self.llm_client:
            return {"correlation_score": 0.5, "method": "fallback"}

        try:
            result = await self.llm_client.analyze_coordination(
                sessions=sessions,
                analysis_type="temporal",
                context={"analysis_focus": "temporal_patterns"},
            )

            return {
                "correlation_score": result.coordination_confidence,
                "evidence": result.evidence_breakdown.get("temporal_correlation", 0.0),
                "reasoning": result.reasoning,
                "method": "llm_analysis",
            }

        except Exception as e:
            logger.warning("Temporal analysis failed, using fallback", error=str(e))
            return {"correlation_score": 0.5, "method": "fallback", "error": str(e)}

    async def _behavioral_analysis(
        self, sessions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze behavioral patterns in attack sessions.

        Args:
            sessions: List of attack sessions

        Returns:
            Behavioral analysis results
        """
        if not self.llm_client:
            return {"similarity_score": 0.5, "method": "fallback"}

        try:
            result = await self.llm_client.analyze_coordination(
                sessions=sessions,
                analysis_type="behavioral",
                context={"analysis_focus": "behavioral_patterns"},
            )

            return {
                "similarity_score": result.coordination_confidence,
                "evidence": result.evidence_breakdown.get("behavioral_similarity", 0.0),
                "reasoning": result.reasoning,
                "method": "llm_analysis",
            }

        except Exception as e:
            logger.warning("Behavioral analysis failed, using fallback", error=str(e))
            return {"similarity_score": 0.5, "method": "fallback", "error": str(e)}

    async def _infrastructure_analysis(
        self, sessions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze infrastructure patterns in attack sessions.

        Args:
            sessions: List of attack sessions

        Returns:
            Infrastructure analysis results
        """
        if not self.llm_client:
            return {"clustering_score": 0.5, "method": "fallback"}

        try:
            result = await self.llm_client.analyze_coordination(
                sessions=sessions,
                analysis_type="infrastructure",
                context={"analysis_focus": "infrastructure_patterns"},
            )

            return {
                "clustering_score": result.coordination_confidence,
                "evidence": result.evidence_breakdown.get(
                    "infrastructure_clustering", 0.0
                ),
                "reasoning": result.reasoning,
                "method": "llm_analysis",
            }

        except Exception as e:
            logger.warning(
                "Infrastructure analysis failed, using fallback", error=str(e)
            )
            return {"clustering_score": 0.5, "method": "fallback", "error": str(e)}


class ToolCoordinatorAgent:
    """Agent for coordinating external tool integrations.

    This agent orchestrates calls to external tools like BGP lookups,
    threat intelligence APIs, and geolocation services.
    """

    def __init__(self):
        """Initialize the tool coordinator agent."""
        pass

    async def execute_analysis_plan(
        self, state: CoordinationAnalysisState
    ) -> CoordinationAnalysisState:
        """Execute the analysis plan using external tools.

        Args:
            state: Current workflow state

        Returns:
            Updated state with tool results
        """
        logger.info(
            "Tool coordinator executing analysis plan",
            needs_deep_analysis=state.needs_deep_analysis,
        )

        state.add_processing_step("tool_coordination")

        try:
            tools_needed = self._determine_tools_needed(state)
            results = await self._execute_tools(tools_needed, state.attack_sessions)

            state.tool_results = results
            state.enrichment_data = self._synthesize_results(results)

            logger.info(
                "Tool coordination completed",
                tools_executed=list(results.keys()),
            )

        except Exception as e:
            logger.error("Tool coordination failed", error=str(e))
            state.add_error(f"Tool coordination failed: {str(e)}")
            state.tool_results = {"error": str(e)}
            state.enrichment_data = {}

        return state

    def _determine_tools_needed(self, state: CoordinationAnalysisState) -> list[str]:
        """Determine which tools are needed for analysis.

        Args:
            state: Current workflow state

        Returns:
            List of tool names needed
        """
        tools = []

        if state.needs_deep_analysis:
            tools.extend(["bgp_lookup", "threat_intel", "geolocation"])

        if state.analysis_depth == "deep":
            tools.append("asn_analysis")

        return tools

    async def _execute_tools(
        self, tools_needed: list[str], sessions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Execute the required tools.

        Args:
            tools_needed: List of tools to execute
            sessions: Attack session data

        Returns:
            Results from tool execution
        """
        results = {}

        # Extract unique IPs for tool lookups
        source_ips = list(
            {
                session.get("source_ip")
                for session in sessions
                if session.get("source_ip")
            }
        )

        for tool in tools_needed:
            try:
                if tool == "bgp_lookup":
                    results[tool] = await self._bgp_lookup(source_ips)
                elif tool == "threat_intel":
                    results[tool] = await self._threat_intel_lookup(source_ips)
                elif tool == "geolocation":
                    results[tool] = await self._geolocation_analysis(source_ips)
                elif tool == "asn_analysis":
                    results[tool] = await self._asn_analysis(source_ips)
            except Exception as e:
                logger.warning(f"Tool {tool} failed", error=str(e))
                results[tool] = {"error": str(e)}

        return results

    async def _bgp_lookup(self, ips: list[str]) -> dict[str, Any]:
        """Perform BGP lookup for IP addresses.

        Args:
            ips: List of IP addresses

        Returns:
            BGP lookup results
        """
        # TODO: Implement actual BGP lookup
        return {
            "method": "mock",
            "results": {
                ip: {"asn": "AS12345", "prefix": "192.168.0.0/16"} for ip in ips
            },
        }

    async def _threat_intel_lookup(self, ips: list[str]) -> dict[str, Any]:
        """Perform threat intelligence lookup.

        Args:
            ips: List of IP addresses

        Returns:
            Threat intelligence results
        """
        # TODO: Implement actual threat intel lookup
        return {
            "method": "mock",
            "results": {
                ip: {"threat_score": 0.3, "reputation": "unknown"} for ip in ips
            },
        }

    async def _geolocation_analysis(self, ips: list[str]) -> dict[str, Any]:
        """Perform geolocation analysis.

        Args:
            ips: List of IP addresses

        Returns:
            Geolocation results
        """
        # TODO: Implement actual geolocation lookup
        return {
            "method": "mock",
            "results": {ip: {"country": "US", "city": "Unknown"} for ip in ips},
        }

    async def _asn_analysis(self, ips: list[str]) -> dict[str, Any]:
        """Perform ASN analysis.

        Args:
            ips: List of IP addresses

        Returns:
            ASN analysis results
        """
        # TODO: Implement actual ASN analysis
        return {
            "method": "mock",
            "results": {ip: {"asn": "AS12345", "org": "Unknown"} for ip in ips},
        }

    def _synthesize_results(self, tool_results: dict[str, Any]) -> dict[str, Any]:
        """Synthesize results from multiple tools.

        Args:
            tool_results: Results from tool execution

        Returns:
            Synthesized enrichment data
        """
        synthesis = {
            "infrastructure_clustering": 0.0,
            "geographic_proximity": 0.0,
            "threat_correlation": 0.0,
        }

        # Analyze infrastructure clustering
        if "bgp_lookup" in tool_results:
            bgp_results = tool_results["bgp_lookup"].get("results", {})
            asns = {result.get("asn") for result in bgp_results.values()}
            if len(asns) == 1:
                synthesis["infrastructure_clustering"] = 0.8
            elif len(asns) < len(bgp_results):
                synthesis["infrastructure_clustering"] = 0.5

        # Analyze geographic proximity
        if "geolocation" in tool_results:
            geo_results = tool_results["geolocation"].get("results", {})
            countries = {result.get("country") for result in geo_results.values()}
            if len(countries) == 1:
                synthesis["geographic_proximity"] = 0.8
            elif len(countries) < len(geo_results):
                synthesis["geographic_proximity"] = 0.5

        # Analyze threat correlation
        if "threat_intel" in tool_results:
            threat_results = tool_results["threat_intel"].get("results", {})
            threat_scores = [
                result.get("threat_score", 0.0) for result in threat_results.values()
            ]
            if threat_scores:
                avg_threat_score = sum(threat_scores) / len(threat_scores)
                synthesis["threat_correlation"] = avg_threat_score

        return synthesis


class ConfidenceScorerAgent:
    """Agent for generating evidence-based confidence scores.

    This agent combines all analysis results to generate a final
    coordination confidence score with evidence breakdown.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """Initialize the confidence scorer agent.

        Args:
            llm_client: LLM client for confidence scoring
        """
        self.llm_client = llm_client

    async def calculate_coordination_score(
        self, state: CoordinationAnalysisState
    ) -> CoordinationAnalysisState:
        """Calculate coordination confidence score.

        Args:
            state: Current workflow state

        Returns:
            Updated state with confidence score
        """
        logger.info("Confidence scorer calculating coordination score")

        state.add_processing_step("confidence_scoring")

        try:
            # Extract evidence scores
            evidence_scores = self._extract_evidence_scores(state)

            # Calculate confidence score
            if self.llm_client:
                confidence_score = await self._llm_confidence_scoring(evidence_scores)
            else:
                confidence_score = self._statistical_confidence_scoring(evidence_scores)

            # Update state
            state.coordination_confidence = confidence_score
            state.evidence_breakdown = evidence_scores
            state.final_assessment = {
                "confidence_score": confidence_score,
                "evidence_scores": evidence_scores,
                "assessment": self._get_assessment(confidence_score),
                "reasoning": self._generate_reasoning(
                    evidence_scores, confidence_score
                ),
            }

            logger.info(
                "Confidence scoring completed",
                confidence_score=confidence_score,
                evidence_scores=evidence_scores,
            )

        except Exception as e:
            logger.error("Confidence scoring failed", error=str(e))
            state.add_error(f"Confidence scoring failed: {str(e)}")
            state.coordination_confidence = 0.5
            state.evidence_breakdown = {}
            state.final_assessment = {"error": str(e)}

        return state

    def _extract_evidence_scores(
        self, state: CoordinationAnalysisState
    ) -> dict[str, float]:
        """Extract evidence scores from analysis results.

        Args:
            state: Current workflow state

        Returns:
            Dictionary of evidence scores
        """
        scores = {}

        # Extract from correlation results
        if state.correlation_results:
            temporal = state.correlation_results.get("temporal", {})
            behavioral = state.correlation_results.get("behavioral", {})
            infrastructure = state.correlation_results.get("infrastructure", {})

            scores["temporal_correlation"] = temporal.get("correlation_score", 0.0)
            scores["behavioral_similarity"] = behavioral.get("similarity_score", 0.0)
            scores["infrastructure_clustering"] = infrastructure.get(
                "clustering_score", 0.0
            )

        # Extract from enrichment data
        if state.enrichment_data:
            scores["geographic_proximity"] = state.enrichment_data.get(
                "geographic_proximity", 0.0
            )
            scores["threat_correlation"] = state.enrichment_data.get(
                "threat_correlation", 0.0
            )

        # Calculate payload similarity (mock for now)
        scores["payload_similarity"] = 0.5

        return scores

    async def _llm_confidence_scoring(self, evidence_scores: dict[str, float]) -> float:
        """Use LLM for confidence scoring.

        Args:
            evidence_scores: Dictionary of evidence scores

        Returns:
            Confidence score (0-1)
        """
        if not self.llm_client:
            return self._statistical_confidence_scoring(evidence_scores)

        try:
            score = await self.llm_client.score_confidence(evidence_scores)
            return score
        except Exception as e:
            logger.warning(
                "LLM confidence scoring failed, using statistical", error=str(e)
            )
            return self._statistical_confidence_scoring(evidence_scores)

    def _statistical_confidence_scoring(
        self, evidence_scores: dict[str, float]
    ) -> float:
        """Use statistical methods for confidence scoring.

        Args:
            evidence_scores: Dictionary of evidence scores

        Returns:
            Confidence score (0-1)
        """
        if not evidence_scores:
            return 0.5

        # Weight the evidence scores
        weights = {
            "temporal_correlation": 0.25,
            "behavioral_similarity": 0.25,
            "infrastructure_clustering": 0.2,
            "geographic_proximity": 0.15,
            "payload_similarity": 0.15,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for evidence_type, score in evidence_scores.items():
            weight = weights.get(evidence_type, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.5

    def _get_assessment(self, confidence_score: float) -> str:
        """Get assessment based on confidence score.

        Args:
            confidence_score: Confidence score (0-1)

        Returns:
            Assessment string
        """
        if confidence_score >= 0.8:
            return "highly_coordinated"
        elif confidence_score >= 0.6:
            return "likely_coordinated"
        elif confidence_score >= 0.4:
            return "possibly_coordinated"
        elif confidence_score >= 0.2:
            return "likely_coincidental"
        else:
            return "coincidental"

    def _generate_reasoning(
        self, evidence_scores: dict[str, float], confidence_score: float
    ) -> str:
        """Generate reasoning for the confidence score.

        Args:
            evidence_scores: Dictionary of evidence scores
            confidence_score: Overall confidence score

        Returns:
            Reasoning string
        """
        high_evidence = [k for k, v in evidence_scores.items() if v > 0.7]
        low_evidence = [k for k, v in evidence_scores.items() if v < 0.3]

        reasoning = f"Confidence score: {confidence_score:.2f}. "

        if high_evidence:
            reasoning += f"Strong evidence in: {', '.join(high_evidence)}. "

        if low_evidence:
            reasoning += f"Weak evidence in: {', '.join(low_evidence)}. "

        assessment = self._get_assessment(confidence_score)
        reasoning += f"Assessment: {assessment}."

        return reasoning


class ElasticsearchEnricherAgent:
    """Agent for enriching Elasticsearch with analysis results.

    This agent updates Elasticsearch documents with coordination analysis
    results and metadata.
    """

    def __init__(self):
        """Initialize the Elasticsearch enricher agent."""
        pass

    async def enrich_attack_sessions(
        self, state: CoordinationAnalysisState
    ) -> CoordinationAnalysisState:
        """Enrich attack sessions with analysis results.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("Elasticsearch enricher updating sessions")

        state.add_processing_step("elasticsearch_enrichment")

        try:
            # TODO: Implement actual Elasticsearch enrichment
            # This would involve:
            # - Updating session documents with coordination metadata
            # - Adding confidence scores and evidence breakdown
            # - Storing final assessment and reasoning

            {
                "coordination_confidence": state.coordination_confidence,
                "evidence_breakdown": state.evidence_breakdown,
                "final_assessment": state.final_assessment,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_depth": state.analysis_depth,
                "processing_steps": state.processing_steps,
            }

            # Mock enrichment for now
            logger.info(
                "Elasticsearch enrichment completed (mock)",
                session_count=len(state.attack_sessions),
                confidence_score=state.coordination_confidence,
            )

        except Exception as e:
            logger.error("Elasticsearch enrichment failed", error=str(e))
            state.add_error(f"Elasticsearch enrichment failed: {str(e)}")

        state.workflow_end_time = datetime.utcnow()
        return state
