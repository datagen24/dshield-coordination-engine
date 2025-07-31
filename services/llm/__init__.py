"""LLM Service for DShield Coordination Engine.

This module provides LLM integration for coordination analysis, including
local model inference via Ollama and prompt engineering for cybersecurity
pattern analysis.

The LLM service supports:
- Local model inference (Llama 3.1, Mistral 7B)
- Cybersecurity-specific prompt engineering
- Coordination analysis reasoning
- Confidence scoring assistance
"""

__version__ = "0.1.0"
__author__ = "DShield Team"
__email__ = "team@dshield.org"

from .client import LLMClient
from .models import CoordinationAnalysisPrompt, ModelConfig
from .prompts import COORDINATION_ANALYSIS_PROMPT

__all__ = [
    "LLMClient",
    "CoordinationAnalysisPrompt",
    "ModelConfig",
    "COORDINATION_ANALYSIS_PROMPT",
]
