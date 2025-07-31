"""LLM client for local model inference via Ollama.

This module provides the client interface for communicating with Ollama
for local LLM inference, optimized for cybersecurity coordination analysis.
"""

import json
import time
from typing import Any

import httpx
import structlog
from pydantic import ValidationError

from .models import (
    CoordinationAnalysisResult,
    LLMResponse,
    ModelConfig,
)
from .prompts import (
    create_confidence_prompt,
    create_coordination_prompt,
    create_synthesis_prompt,
)

logger = structlog.get_logger(__name__)


class LLMClient:
    """Client for local LLM inference via Ollama.

    Provides methods for generating text using local models through Ollama,
    with specialized support for cybersecurity coordination analysis.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_config: ModelConfig | None = None,
    ):
        """Initialize the LLM client.

        Args:
            base_url: Ollama API base URL
            default_config: Default model configuration
        """
        self.base_url = base_url.rstrip("/")
        self.default_config = default_config or ModelConfig()
        self.client = httpx.AsyncClient(timeout=30.0)

        logger.info(
            "LLM client initialized",
            base_url=self.base_url,
            default_model=self.default_config.model_name,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("LLM client closed")

    async def health_check(self) -> bool:
        """Check if Ollama is available and healthy.

        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

    async def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of available model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error("Failed to list models", error=str(e))
            return []

    async def generate(
        self, prompt: str, config: ModelConfig | None = None, **kwargs
    ) -> LLMResponse:
        """Generate text using the specified model.

        Args:
            prompt: Input prompt for generation
            config: Model configuration (uses default if not provided)
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            httpx.HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        config = config or self.default_config

        # Prepare request payload
        payload = {
            "model": config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
            },
        }

        # Add any additional parameters
        payload["options"].update(kwargs)

        start_time = time.time()

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=config.timeout,
            )
            response.raise_for_status()

            data = response.json()
            inference_time = time.time() - start_time

            return LLMResponse(
                text=data.get("response", ""),
                model_used=config.model_name,
                tokens_used=data.get("eval_count"),
                inference_time=inference_time,
                metadata={
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                    "eval_duration": data.get("eval_duration"),
                },
            )

        except httpx.HTTPError as e:
            logger.error(
                "LLM generation failed",
                error=str(e),
                model=config.model_name,
                status_code=getattr(e.response, "status_code", None),
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during generation",
                error=str(e),
                model=config.model_name,
            )
            raise

    async def analyze_coordination(
        self,
        sessions: list[dict[str, Any]],
        analysis_type: str = "comprehensive",
        context: dict[str, Any] | None = None,
        instructions: str | None = None,
        config: ModelConfig | None = None,
    ) -> CoordinationAnalysisResult:
        """Analyze attack sessions for coordination patterns.

        Args:
            sessions: List of attack session data
            analysis_type: Type of analysis to perform
            context: Additional context for analysis
            instructions: Custom instructions
            config: Model configuration

        Returns:
            CoordinationAnalysisResult with analysis results
        """
        logger.info(
            "Starting coordination analysis",
            session_count=len(sessions),
            analysis_type=analysis_type,
        )

        # Create the prompt
        prompt = create_coordination_prompt(
            sessions=sessions,
            analysis_type=analysis_type,
            context=context,
            instructions=instructions,
        )

        # Generate response
        response = await self.generate(prompt, config=config)

        # Parse the response
        try:
            # Try to extract JSON from the response
            json_start = response.text.find("{")
            json_end = response.text.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_text = response.text[json_start:json_end]
                data = json.loads(json_text)

                # Validate and return result
                return CoordinationAnalysisResult(
                    coordination_confidence=data.get("coordination_confidence", 0.0),
                    evidence_breakdown=data.get("evidence_breakdown", {}),
                    reasoning=data.get("reasoning", ""),
                    key_factors=data.get("key_factors", []),
                    model_used=response.model_used,
                )
            else:
                # Fallback: parse unstructured response
                return self._parse_unstructured_response(
                    response.text, response.model_used
                )

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(
                "Failed to parse structured response, using fallback",
                error=str(e),
                response_text=response.text[:200],
            )
            return self._parse_unstructured_response(response.text, response.model_used)

    async def score_confidence(
        self,
        evidence_scores: dict[str, float],
        config: ModelConfig | None = None,
    ) -> float:
        """Score coordination confidence based on evidence.

        Args:
            evidence_scores: Dictionary of evidence scores
            config: Model configuration

        Returns:
            Overall coordination confidence score (0-1)
        """
        prompt = create_confidence_prompt(evidence_scores)
        response = await self.generate(prompt, config=config)

        try:
            # Try to extract confidence score from response
            lines = response.text.split("\n")
            for line in lines:
                if "confidence" in line.lower() and ":" in line:
                    try:
                        score_text = line.split(":")[-1].strip()
                        score = float(score_text)
                        return max(0.0, min(1.0, score))
                    except (ValueError, IndexError):
                        continue

            # Fallback: estimate from evidence scores
            return self._estimate_confidence(evidence_scores)

        except Exception as e:
            logger.warning(
                "Failed to parse confidence score, using estimation",
                error=str(e),
            )
            return self._estimate_confidence(evidence_scores)

    async def synthesize_evidence(
        self,
        temporal_analysis: str,
        behavioral_analysis: str,
        infrastructure_analysis: str,
        config: ModelConfig | None = None,
    ) -> CoordinationAnalysisResult:
        """Synthesize evidence from multiple analyses.

        Args:
            temporal_analysis: Results from temporal analysis
            behavioral_analysis: Results from behavioral analysis
            infrastructure_analysis: Results from infrastructure analysis
            config: Model configuration

        Returns:
            CoordinationAnalysisResult with synthesized assessment
        """
        prompt = create_synthesis_prompt(
            temporal_analysis=temporal_analysis,
            behavioral_analysis=behavioral_analysis,
            infrastructure_analysis=infrastructure_analysis,
        )

        response = await self.generate(prompt, config=config)

        try:
            # Try to extract JSON from response
            json_start = response.text.find("{")
            json_end = response.text.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_text = response.text[json_start:json_end]
                data = json.loads(json_text)

                return CoordinationAnalysisResult(
                    coordination_confidence=data.get("coordination_confidence", 0.0),
                    evidence_breakdown=data.get("evidence_breakdown", {}),
                    reasoning=data.get("reasoning", ""),
                    key_factors=data.get("key_factors", []),
                    model_used=response.model_used,
                )
            else:
                return self._parse_unstructured_response(
                    response.text, response.model_used
                )

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(
                "Failed to parse synthesis response, using fallback",
                error=str(e),
            )
            return self._parse_unstructured_response(response.text, response.model_used)

    def _parse_unstructured_response(
        self, text: str, model_used: str
    ) -> CoordinationAnalysisResult:
        """Parse unstructured LLM response into structured result.

        Args:
            text: Raw LLM response text
            model_used: Name of the model used

        Returns:
            CoordinationAnalysisResult with parsed data
        """
        # Extract confidence score if present
        confidence = 0.5  # Default neutral score

        # Look for confidence indicators in text
        text_lower = text.lower()
        if "high confidence" in text_lower or "strong coordination" in text_lower:
            confidence = 0.8
        elif "moderate confidence" in text_lower or "likely coordinated" in text_lower:
            confidence = 0.6
        elif "low confidence" in text_lower or "possibly coincidental" in text_lower:
            confidence = 0.3
        elif "no coordination" in text_lower or "coincidental" in text_lower:
            confidence = 0.1

        # Extract key factors
        key_factors = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                factor = line[1:].strip()
                if factor:
                    key_factors.append(factor)

        return CoordinationAnalysisResult(
            coordination_confidence=confidence,
            evidence_breakdown={
                "temporal_correlation": confidence * 0.8,
                "behavioral_similarity": confidence * 0.7,
                "infrastructure_clustering": confidence * 0.6,
                "geographic_proximity": confidence * 0.5,
                "payload_similarity": confidence * 0.9,
            },
            reasoning=text[:1000],  # Truncate if too long
            key_factors=key_factors[:5],  # Limit to 5 factors
            model_used=model_used,
        )

    def _estimate_confidence(self, evidence_scores: dict[str, float]) -> float:
        """Estimate confidence from evidence scores.

        Args:
            evidence_scores: Dictionary of evidence scores

        Returns:
            Estimated confidence score (0-1)
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
