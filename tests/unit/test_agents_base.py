"""Unit tests for agents base module."""

from typing import Any
from unittest.mock import patch

import pytest

from agents.base import BaseAgent, CoordinationAnalysisState


class TestBaseAgent:
    """Test the BaseAgent abstract class."""

    class MockAgent(BaseAgent):
        """Mock agent for testing."""

        async def process(self, state: dict[str, Any]) -> dict[str, Any]:
            """Mock process implementation."""
            state["processed"] = True
            return state

    def test_base_agent_initialization(self):
        """Test BaseAgent initialization."""
        agent = self.MockAgent("test-agent")
        assert agent.name == "test-agent"
        assert agent.logger is not None

    def test_log_processing(self):
        """Test log_processing method."""
        agent = self.MockAgent("test-agent")
        state = {"key1": "value1", "key2": "value2"}

        with patch.object(agent.logger, "info") as mock_info:
            agent.log_processing(state)
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[1]["agent"] == "test-agent"
            assert "key1" in call_args[1]["state_keys"]
            assert "key2" in call_args[1]["state_keys"]

    def test_log_completion(self):
        """Test log_completion method."""
        agent = self.MockAgent("test-agent")
        result = {"result1": "value1", "result2": "value2"}

        with patch.object(agent.logger, "info") as mock_info:
            agent.log_completion(result)
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[1]["agent"] == "test-agent"
            assert "result1" in call_args[1]["result_keys"]
            assert "result2" in call_args[1]["result_keys"]

    def test_log_error(self):
        """Test log_error method."""
        agent = self.MockAgent("test-agent")
        state = {"key1": "value1"}
        error = ValueError("Test error")

        with patch.object(agent.logger, "error") as mock_error:
            agent.log_error(error, state)
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert call_args[1]["agent"] == "test-agent"
            assert call_args[1]["error"] == "Test error"
            assert "key1" in call_args[1]["state_keys"]

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execute method."""
        agent = self.MockAgent("test-agent")
        state = {"input": "test"}

        with (
            patch.object(agent, "log_processing") as mock_log_processing,
            patch.object(agent, "log_completion") as mock_log_completion,
            patch.object(agent, "log_error") as mock_log_error,
        ):
            result = await agent.execute(state)

            mock_log_processing.assert_called_once_with(state)
            mock_log_completion.assert_called_once()
            mock_log_error.assert_not_called()
            assert result["processed"] is True
            assert result["input"] == "test"

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """Test execute method with error handling."""

        class ErrorAgent(BaseAgent):
            """Agent that raises an error."""

            async def process(self, state: dict[str, Any]) -> dict[str, Any]:
                """Raise an error."""
                raise ValueError("Test error")

        agent = ErrorAgent("error-agent")
        state = {"input": "test"}

        with (
            patch.object(agent, "log_processing") as mock_log_processing,
            patch.object(agent, "log_completion") as mock_log_completion,
            patch.object(agent, "log_error") as mock_log_error,
        ):
            with pytest.raises(ValueError, match="Test error"):
                await agent.execute(state)

            mock_log_processing.assert_called_once_with(state)
            mock_log_completion.assert_not_called()
            mock_log_error.assert_called_once()


class TestCoordinationAnalysisState:
    """Test the CoordinationAnalysisState class."""

    def test_state_initialization(self):
        """Test state initialization."""
        state = CoordinationAnalysisState()
        assert state.attack_sessions == []
        assert state.correlation_results == {}
        assert state.enrichment_data == {}
        assert state.coordination_confidence == 0.0
        assert state.analysis_plan == {}
        assert state.tool_results == {}
        assert state.final_assessment == {}
        assert state.errors == []
        assert state.warnings == []

    def test_to_dict(self):
        """Test to_dict method."""
        state = CoordinationAnalysisState()
        state.attack_sessions = [{"ip": "192.168.1.1"}]
        state.correlation_results = {"correlation": 0.8}
        state.coordination_confidence = 0.75
        state.errors = ["error1"]
        state.warnings = ["warning1"]

        result = state.to_dict()

        assert result["attack_sessions"] == [{"ip": "192.168.1.1"}]
        assert result["correlation_results"] == {"correlation": 0.8}
        assert result["coordination_confidence"] == 0.75
        assert result["errors"] == ["error1"]
        assert result["warnings"] == ["warning1"]

    def test_from_dict(self):
        """Test from_dict class method."""
        data = {
            "attack_sessions": [{"ip": "192.168.1.1"}],
            "correlation_results": {"correlation": 0.8},
            "enrichment_data": {"enrichment": "data"},
            "coordination_confidence": 0.75,
            "analysis_plan": {"plan": "details"},
            "tool_results": {"tool": "results"},
            "final_assessment": {"assessment": "final"},
            "errors": ["error1"],
            "warnings": ["warning1"],
        }

        state = CoordinationAnalysisState.from_dict(data)

        assert state.attack_sessions == [{"ip": "192.168.1.1"}]
        assert state.correlation_results == {"correlation": 0.8}
        assert state.enrichment_data == {"enrichment": "data"}
        assert state.coordination_confidence == 0.75
        assert state.analysis_plan == {"plan": "details"}
        assert state.tool_results == {"tool": "results"}
        assert state.final_assessment == {"assessment": "final"}
        assert state.errors == ["error1"]
        assert state.warnings == ["warning1"]

    def test_from_dict_with_missing_keys(self):
        """Test from_dict with missing keys uses defaults."""
        data = {"attack_sessions": [{"ip": "192.168.1.1"}]}

        state = CoordinationAnalysisState.from_dict(data)

        assert state.attack_sessions == [{"ip": "192.168.1.1"}]
        assert state.correlation_results == {}
        assert state.enrichment_data == {}
        assert state.coordination_confidence == 0.0
        assert state.analysis_plan == {}
        assert state.tool_results == {}
        assert state.final_assessment == {}
        assert state.errors == []
        assert state.warnings == []
