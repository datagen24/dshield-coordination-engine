"""State management for coordination analysis workflow.

This module defines the shared state structure used across all agents
in the coordination analysis workflow.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CoordinationAnalysisState(BaseModel):
    """Shared state across all agents in coordination analysis workflow.

    This state object is passed between agents and contains all the
    data needed for coordination analysis including input data, intermediate
    results, and final assessment.
    """

    # Input data
    attack_sessions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of attack session data to analyze",
    )
    analysis_depth: str = Field(
        default="standard",
        description="Analysis depth level (minimal, standard, deep)",
    )
    user_id: str | None = Field(
        None,
        description="User identifier for logging and tracking",
    )

    # Analysis plan and routing
    analysis_plan: dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis plan and routing decisions",
    )
    needs_deep_analysis: bool = Field(
        default=False,
        description="Whether deep analysis is required",
    )

    # Intermediate results
    correlation_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Temporal and behavioral correlation results",
    )
    enrichment_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Enriched data from external tools",
    )
    tool_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from external tool integrations",
    )

    # Final assessment
    coordination_confidence: float = Field(
        default=0.0,
        description="Overall coordination confidence score (0-1)",
        ge=0.0,
        le=1.0,
    )
    evidence_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of evidence scores by category",
    )
    final_assessment: dict[str, Any] = Field(
        default_factory=dict,
        description="Final assessment and reasoning",
    )

    # Metadata
    workflow_start_time: datetime | None = Field(
        None,
        description="When the workflow started",
    )
    workflow_end_time: datetime | None = Field(
        None,
        description="When the workflow completed",
    )
    processing_steps: list[str] = Field(
        default_factory=list,
        description="List of processing steps completed",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of errors encountered during processing",
    )

    def add_processing_step(self, step: str) -> None:
        """Add a processing step to the tracking list.

        Args:
            step: Name of the processing step
        """
        self.processing_steps.append(f"{step}: {datetime.utcnow().isoformat()}")

    def add_error(self, error: str) -> None:
        """Add an error to the error list.

        Args:
            error: Error message
        """
        self.errors.append(f"{error}: {datetime.utcnow().isoformat()}")

    def is_complete(self) -> bool:
        """Check if the analysis is complete.

        Returns:
            True if analysis is complete, False otherwise
        """
        return (
            self.coordination_confidence > 0.0
            and self.final_assessment
            and self.workflow_end_time is not None
        )

    def get_processing_time(self) -> float | None:
        """Get the total processing time in seconds.

        Returns:
            Processing time in seconds, or None if not complete
        """
        if self.workflow_start_time and self.workflow_end_time:
            return (self.workflow_end_time - self.workflow_start_time).total_seconds()
        return None

    def to_result_dict(self) -> dict[str, Any]:
        """Convert state to result dictionary for API response.

        Returns:
            Dictionary representation of analysis results
        """
        return {
            "coordination_confidence": self.coordination_confidence,
            "evidence_breakdown": self.evidence_breakdown,
            "final_assessment": self.final_assessment,
            "processing_steps": self.processing_steps,
            "processing_time": self.get_processing_time(),
            "errors": self.errors,
            "analysis_depth": self.analysis_depth,
            "session_count": len(self.attack_sessions),
        }
