"""Base agent class for coordination analysis."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all coordination analysis agents."""

    def __init__(self, name: str):
        """Initialize the agent."""
        self.name = name
        self.logger = logger.bind(agent=name)

    @abstractmethod
    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Process the current state and return updated state."""
        pass

    def log_processing(self, state: dict[str, Any]) -> None:
        """Log processing start."""
        self.logger.info(
            "Agent processing started", agent=self.name, state_keys=list(state.keys())
        )

    def log_completion(self, state: dict[str, Any]) -> None:
        """Log processing completion."""
        self.logger.info(
            "Agent processing completed",
            agent=self.name,
            result_keys=list(state.keys()),
        )

    def log_error(self, error: Exception, state: dict[str, Any]) -> None:
        """Log processing error."""
        self.logger.error(
            "Agent processing failed",
            agent=self.name,
            error=str(error),
            state_keys=list(state.keys()),
        )

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent with error handling."""
        try:
            self.log_processing(state)
            result = await self.process(state)
            self.log_completion(result)
            return result
        except Exception as e:
            self.log_error(e, state)
            raise


class CoordinationAnalysisState:
    """Shared state across all coordination analysis agents."""

    def __init__(self) -> None:
        """Initialize the analysis state."""
        self.attack_sessions: list[dict[str, Any]] = []
        self.correlation_results: dict[str, Any] = {}
        self.enrichment_data: dict[str, Any] = {}
        self.coordination_confidence: float = 0.0
        self.analysis_plan: dict[str, Any] = {}
        self.tool_results: dict[str, Any] = {}
        self.final_assessment: dict[str, Any] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "attack_sessions": self.attack_sessions,
            "correlation_results": self.correlation_results,
            "enrichment_data": self.enrichment_data,
            "coordination_confidence": self.coordination_confidence,
            "analysis_plan": self.analysis_plan,
            "tool_results": self.tool_results,
            "final_assessment": self.final_assessment,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoordinationAnalysisState":
        """Create state from dictionary."""
        state = cls()
        state.attack_sessions = data.get("attack_sessions", [])
        state.correlation_results = data.get("correlation_results", {})
        state.enrichment_data = data.get("enrichment_data", {})
        state.coordination_confidence = data.get("coordination_confidence", 0.0)
        state.analysis_plan = data.get("analysis_plan", {})
        state.tool_results = data.get("tool_results", {})
        state.final_assessment = data.get("final_assessment", {})
        state.errors = data.get("errors", [])
        state.warnings = data.get("warnings", [])
        return state
