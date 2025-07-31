"""Data models for LLM service.

This module defines the data structures used by the LLM service for
configuration, prompts, and analysis results.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration for LLM model settings.

    Defines the model parameters, inference settings, and performance
    configurations for local LLM inference.
    """

    model_name: str = Field(
        default="llama-3.1-8b-instruct",
        description="Ollama model name for inference",
        examples=["llama-3.1-8b-instruct", "mistral-7b-instruct"],
    )
    temperature: float = Field(
        default=0.1,
        description="Sampling temperature for generation",
        ge=0.0,
        le=2.0,
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens to generate",
        ge=1,
        le=8192,
    )
    top_p: float = Field(
        default=0.9,
        description="Top-p sampling parameter",
        ge=0.0,
        le=1.0,
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300,
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts on failure",
        ge=0,
        le=10,
    )

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model name format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Model name cannot be empty")
        return v.strip()


class CoordinationAnalysisPrompt(BaseModel):
    """Prompt structure for coordination analysis.

    Defines the input format and structure for LLM prompts used in
    coordination analysis tasks.
    """

    attack_sessions: list[dict[str, Any]] = Field(
        ...,
        description="List of attack session data for analysis",
    )
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis to perform",
        examples=["temporal", "behavioral", "infrastructure", "comprehensive"],
    )
    context: dict[str, Any] | None = Field(
        None,
        description="Additional context for analysis",
    )
    instructions: str | None = Field(
        None,
        description="Custom instructions for the analysis",
    )

    @field_validator("analysis_type")
    @classmethod
    def validate_analysis_type(cls, v: str) -> str:
        """Validate analysis type."""
        valid_types = ["temporal", "behavioral", "infrastructure", "comprehensive"]
        if v not in valid_types:
            raise ValueError(f"Analysis type must be one of: {valid_types}")
        return v


class LLMResponse(BaseModel):
    """Response from LLM inference.

    Contains the generated text, metadata, and performance information
    from LLM inference calls.
    """

    text: str = Field(
        ...,
        description="Generated text response from LLM",
    )
    model_used: str = Field(
        ...,
        description="Name of the model used for inference",
    )
    tokens_used: int | None = Field(
        None,
        description="Number of tokens used in the request",
    )
    inference_time: float | None = Field(
        None,
        description="Inference time in seconds",
    )
    confidence_score: float | None = Field(
        None,
        description="Confidence score from the model (0-1)",
        ge=0.0,
        le=1.0,
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Additional metadata from the inference",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the response",
    )


class CoordinationAnalysisResult(BaseModel):
    """Result of coordination analysis from LLM.

    Contains the structured analysis results including confidence scores,
    evidence breakdown, and reasoning.
    """

    coordination_confidence: float = Field(
        ...,
        description="Overall coordination confidence score (0-1)",
        ge=0.0,
        le=1.0,
    )
    evidence_breakdown: dict[str, float] = Field(
        ...,
        description="Breakdown of evidence scores by category",
        examples=[
            {
                "temporal_correlation": 0.8,
                "behavioral_similarity": 0.7,
                "infrastructure_clustering": 0.6,
                "geographic_proximity": 0.5,
                "payload_similarity": 0.9,
            }
        ],
    )
    reasoning: str = Field(
        ...,
        description="Detailed reasoning for the coordination assessment",
    )
    key_factors: list[str] = Field(
        ...,
        description="Key factors that influenced the assessment",
    )
    model_used: str = Field(
        ...,
        description="LLM model used for the analysis",
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the analysis",
    )

    @field_validator("evidence_breakdown")
    @classmethod
    def validate_evidence_scores(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate evidence scores are within valid range."""
        for key, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Evidence score for {key} must be between 0.0 and 1.0"
                )
        return v
