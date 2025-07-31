"""Workflow Service for DShield Coordination Engine.

This module provides LangGraph workflow orchestration for coordination analysis,
including multi-agent processing and state management.

The workflow service supports:
- LangGraph workflow orchestration
- Multi-agent coordination analysis
- State management and persistence
- Tool integration and coordination
- Error handling and recovery
"""

__version__ = "0.1.0"
__author__ = "DShield Team"
__email__ = "team@dshield.org"

from .agents import (
    ConfidenceScorerAgent,
    ElasticsearchEnricherAgent,
    OrchestratorAgent,
    PatternAnalyzerAgent,
    ToolCoordinatorAgent,
)
from .graph import create_coordination_analysis_workflow
from .state import CoordinationAnalysisState

__all__ = [
    "OrchestratorAgent",
    "PatternAnalyzerAgent",
    "ToolCoordinatorAgent",
    "ConfidenceScorerAgent",
    "ElasticsearchEnricherAgent",
    "create_coordination_analysis_workflow",
    "CoordinationAnalysisState",
]
