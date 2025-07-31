"""Unit tests for workflow service."""

from datetime import datetime

import pytest

from services.workflow.agents import (
    ConfidenceScorerAgent,
    ElasticsearchEnricherAgent,
    OrchestratorAgent,
    PatternAnalyzerAgent,
    ToolCoordinatorAgent,
)
from services.workflow.graph import (
    create_coordination_analysis_workflow,
    run_coordination_analysis,
)
from services.workflow.state import CoordinationAnalysisState


class TestCoordinationAnalysisState:
    """Test CoordinationAnalysisState class."""

    def test_state_initialization(self):
        """Test state initialization."""
        state = CoordinationAnalysisState()

        assert state.attack_sessions == []
        assert state.analysis_depth == "standard"
        assert state.user_id is None
        assert state.coordination_confidence == 0.0
        assert state.evidence_breakdown == {}
        assert state.processing_steps == []
        assert state.errors == []

    def test_state_with_data(self):
        """Test state with attack session data."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        state = CoordinationAnalysisState(
            attack_sessions=sessions,
            analysis_depth="deep",
            user_id="test-user",
        )

        assert len(state.attack_sessions) == 1
        assert state.analysis_depth == "deep"
        assert state.user_id == "test-user"

    def test_add_processing_step(self):
        """Test adding processing steps."""
        state = CoordinationAnalysisState()

        state.add_processing_step("test_step")

        assert len(state.processing_steps) == 1
        assert "test_step:" in state.processing_steps[0]

    def test_add_error(self):
        """Test adding errors."""
        state = CoordinationAnalysisState()

        state.add_error("Test error message")

        assert len(state.errors) == 1
        assert "Test error message:" in state.errors[0]

    def test_is_complete(self):
        """Test completion status."""
        state = CoordinationAnalysisState()

        # Initially not complete
        assert not state.is_complete()

        # Set required fields
        state.coordination_confidence = 0.75
        state.final_assessment = {"test": "value"}
        state.workflow_end_time = datetime.utcnow()

        assert state.is_complete()

    def test_get_processing_time(self):
        """Test processing time calculation."""
        state = CoordinationAnalysisState()

        # No start time
        assert state.get_processing_time() is None

        # Set start and end times
        start_time = datetime(2025, 7, 28, 10, 0, 0)
        end_time = datetime(2025, 7, 28, 10, 1, 0)  # 1 minute later

        state.workflow_start_time = start_time
        state.workflow_end_time = end_time

        processing_time = state.get_processing_time()
        assert processing_time == 60.0  # 60 seconds

    def test_to_result_dict(self):
        """Test conversion to result dictionary."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        state = CoordinationAnalysisState(
            attack_sessions=sessions,
            analysis_depth="standard",
            user_id="test-user",
        )

        state.coordination_confidence = 0.75
        state.evidence_breakdown = {"temporal_correlation": 0.8}
        state.final_assessment = {"reasoning": "Test reasoning"}
        state.processing_steps = ["step1", "step2"]
        state.errors = ["error1"]

        result = state.to_result_dict()

        assert result["coordination_confidence"] == 0.75
        assert result["evidence_breakdown"]["temporal_correlation"] == 0.8
        assert result["final_assessment"]["reasoning"] == "Test reasoning"
        assert result["processing_steps"] == ["step1", "step2"]
        assert result["errors"] == ["error1"]
        assert result["analysis_depth"] == "standard"
        assert result["session_count"] == 1


class TestOrchestratorAgent:
    """Test OrchestratorAgent class."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator agent."""
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_analyze_initial_data(self, orchestrator):
        """Test initial data analysis."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
            {
                "source_ip": "192.168.1.2",
                "timestamp": "2025-07-28T10:01:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
        ]

        state = CoordinationAnalysisState(
            attack_sessions=sessions,
            analysis_depth="standard",
            user_id="test-user",
        )

        result = await orchestrator.analyze_initial_data(state)

        assert result.workflow_start_time is not None
        assert "orchestrator_analysis" in result.processing_steps[0]
        assert "session_count" in result.analysis_plan
        assert "analysis_steps" in result.analysis_plan

    @pytest.mark.asyncio
    async def test_should_deep_analyze_single_source(self, orchestrator):
        """Test deep analysis decision for single source."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
            {
                "source_ip": "192.168.1.1",  # Same source
                "timestamp": "2025-07-28T10:01:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
        ]

        result = await orchestrator._should_deep_analyze(sessions)
        assert result is False  # Single source, likely not coordinated

    @pytest.mark.asyncio
    async def test_should_deep_analyze_multiple_sources(self, orchestrator):
        """Test deep analysis decision for multiple sources."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
            {
                "source_ip": "192.168.1.2",
                "timestamp": "2025-07-28T10:01:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
            {
                "source_ip": "192.168.1.3",
                "timestamp": "2025-07-28T10:02:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
        ]

        result = await orchestrator._should_deep_analyze(sessions)
        # Should be True for multiple sources with timing patterns
        assert result is True


class TestPatternAnalyzerAgent:
    """Test PatternAnalyzerAgent class."""

    @pytest.fixture
    def pattern_analyzer(self):
        """Create pattern analyzer agent."""
        return PatternAnalyzerAgent()

    @pytest.mark.asyncio
    async def test_analyze_patterns(self, pattern_analyzer):
        """Test pattern analysis."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
            {
                "source_ip": "192.168.1.2",
                "timestamp": "2025-07-28T10:01:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
        ]

        state = CoordinationAnalysisState(attack_sessions=sessions)

        result = await pattern_analyzer.analyze_patterns(state)

        assert "pattern_analysis" in result.processing_steps[0]
        assert "temporal" in result.correlation_results
        assert "behavioral" in result.correlation_results
        assert "infrastructure" in result.correlation_results

    @pytest.mark.asyncio
    async def test_temporal_analysis_fallback(self, pattern_analyzer):
        """Test temporal analysis with fallback."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        result = await pattern_analyzer._temporal_analysis(sessions)

        assert "correlation_score" in result
        assert "method" in result
        assert result["method"] == "fallback"


class TestToolCoordinatorAgent:
    """Test ToolCoordinatorAgent class."""

    @pytest.fixture
    def tool_coordinator(self):
        """Create tool coordinator agent."""
        return ToolCoordinatorAgent()

    @pytest.mark.asyncio
    async def test_execute_analysis_plan(self, tool_coordinator):
        """Test analysis plan execution."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        state = CoordinationAnalysisState(
            attack_sessions=sessions,
            needs_deep_analysis=True,
        )

        result = await tool_coordinator.execute_analysis_plan(state)

        assert "tool_coordination" in result.processing_steps[0]
        assert "bgp_lookup" in result.tool_results
        assert "infrastructure_clustering" in result.enrichment_data

    def test_determine_tools_needed(self, tool_coordinator):
        """Test tool determination."""
        # Deep analysis needed
        state = CoordinationAnalysisState(needs_deep_analysis=True)
        tools = tool_coordinator._determine_tools_needed(state)
        assert "bgp_lookup" in tools
        assert "threat_intel" in tools
        assert "geolocation" in tools

        # Deep analysis with deep depth
        state = CoordinationAnalysisState(
            needs_deep_analysis=True,
            analysis_depth="deep",
        )
        tools = tool_coordinator._determine_tools_needed(state)
        assert "asn_analysis" in tools

    @pytest.mark.asyncio
    async def test_bgp_lookup(self, tool_coordinator):
        """Test BGP lookup."""
        ips = ["192.168.1.1", "192.168.1.2"]

        result = await tool_coordinator._bgp_lookup(ips)

        assert "method" in result
        assert "results" in result
        assert "192.168.1.1" in result["results"]
        assert "192.168.1.2" in result["results"]


class TestConfidenceScorerAgent:
    """Test ConfidenceScorerAgent class."""

    @pytest.fixture
    def confidence_scorer(self):
        """Create confidence scorer agent."""
        return ConfidenceScorerAgent()

    @pytest.mark.asyncio
    async def test_calculate_coordination_score(self, confidence_scorer):
        """Test coordination score calculation."""
        state = CoordinationAnalysisState()
        state.correlation_results = {
            "temporal": {"correlation_score": 0.8},
            "behavioral": {"similarity_score": 0.7},
            "infrastructure": {"clustering_score": 0.6},
        }
        state.enrichment_data = {
            "geographic_proximity": 0.5,
            "threat_correlation": 0.3,
        }

        result = await confidence_scorer.calculate_coordination_score(state)

        assert "confidence_scoring" in result.processing_steps[0]
        assert result.coordination_confidence > 0.0
        assert result.evidence_breakdown
        assert result.final_assessment

    def test_statistical_confidence_scoring(self, confidence_scorer):
        """Test statistical confidence scoring."""
        evidence_scores = {
            "temporal_correlation": 0.8,
            "behavioral_similarity": 0.7,
            "infrastructure_clustering": 0.6,
            "geographic_proximity": 0.5,
            "payload_similarity": 0.9,
        }

        score = confidence_scorer._statistical_confidence_scoring(evidence_scores)

        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be weighted average

    def test_get_assessment(self, confidence_scorer):
        """Test assessment determination."""
        assert confidence_scorer._get_assessment(0.9) == "highly_coordinated"
        assert confidence_scorer._get_assessment(0.7) == "likely_coordinated"
        assert confidence_scorer._get_assessment(0.5) == "possibly_coordinated"
        assert confidence_scorer._get_assessment(0.3) == "likely_coincidental"
        assert confidence_scorer._get_assessment(0.1) == "coincidental"


class TestElasticsearchEnricherAgent:
    """Test ElasticsearchEnricherAgent class."""

    @pytest.fixture
    def elasticsearch_enricher(self):
        """Create Elasticsearch enricher agent."""
        return ElasticsearchEnricherAgent()

    @pytest.mark.asyncio
    async def test_enrich_attack_sessions(self, elasticsearch_enricher):
        """Test attack session enrichment."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        state = CoordinationAnalysisState(
            attack_sessions=sessions,
            coordination_confidence=0.75,
            evidence_breakdown={"temporal_correlation": 0.8},
            final_assessment={"reasoning": "Test reasoning"},
        )

        result = await elasticsearch_enricher.enrich_attack_sessions(state)

        assert "elasticsearch_enrichment" in result.processing_steps[0]
        assert result.workflow_end_time is not None


class TestWorkflowGraph:
    """Test workflow graph functionality."""

    @pytest.mark.asyncio
    async def test_run_coordination_analysis(self):
        """Test coordination analysis workflow execution."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
            {
                "source_ip": "192.168.1.2",
                "timestamp": "2025-07-28T10:01:00Z",
                "payload": "GET /admin HTTP/1.1",
            },
        ]

        result = await run_coordination_analysis(
            attack_sessions=sessions,
            analysis_depth="standard",
            user_id="test-user",
        )

        assert "coordination_confidence" in result
        assert "evidence_breakdown" in result
        assert "final_assessment" in result
        assert "processing_steps" in result
        assert "session_count" in result
        assert result["session_count"] == 2

    def test_create_workflow(self):
        """Test workflow creation."""
        workflow = create_coordination_analysis_workflow()

        # Check that workflow is created successfully
        assert workflow is not None
        # The workflow should be a compiled LangGraph workflow
        assert hasattr(workflow, "ainvoke")
