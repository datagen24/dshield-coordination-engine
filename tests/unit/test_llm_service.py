"""Unit tests for LLM service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.llm import LLMClient
from services.llm.models import CoordinationAnalysisResult, ModelConfig
from services.llm.prompts import create_coordination_prompt


class TestModelConfig:
    """Test ModelConfig class."""

    def test_model_config_defaults(self):
        """Test ModelConfig default values."""
        config = ModelConfig()
        assert config.model_name == "llama-3.1-8b-instruct"
        assert config.temperature == 0.1
        assert config.max_tokens == 2048
        assert config.top_p == 0.9
        assert config.timeout == 30
        assert config.retry_attempts == 3

    def test_model_config_validation(self):
        """Test ModelConfig validation."""
        # Valid config
        config = ModelConfig(
            model_name="test-model",
            temperature=0.5,
            max_tokens=1024,
        )
        assert config.model_name == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 1024

        # Invalid model name
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            ModelConfig(model_name="")

        # Invalid temperature
        with pytest.raises(ValueError):
            ModelConfig(temperature=3.0)  # Above max

        # Invalid max_tokens
        with pytest.raises(ValueError):
            ModelConfig(max_tokens=0)  # Below min


class TestLLMClient:
    """Test LLMClient class."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        with patch("services.llm.client.httpx.AsyncClient") as mock_client:
            # Create async mock for the client
            async_mock = AsyncMock()
            mock_client.return_value = async_mock
            client = LLMClient(base_url="http://localhost:11434")
            yield client

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_llm_client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Set up the async mock properly
        mock_llm_client.client.get = AsyncMock(return_value=mock_response)

        result = await mock_llm_client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_llm_client):
        """Test failed health check."""
        mock_llm_client.client.get.side_effect = Exception("Connection failed")

        result = await mock_llm_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_list_models_success(self, mock_llm_client):
        """Test successful model listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama-3.1-8b-instruct"},
                {"name": "mistral-7b-instruct"},
            ]
        }
        # Set up the async mock properly
        mock_llm_client.client.get = AsyncMock(return_value=mock_response)

        result = await mock_llm_client.list_models()
        assert result == ["llama-3.1-8b-instruct", "mistral-7b-instruct"]

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_llm_client):
        """Test successful text generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated text response",
            "eval_count": 100,
            "prompt_eval_count": 50,
            "eval_duration": 1.5,
        }
        # Set up the async mock properly
        mock_llm_client.client.post = AsyncMock(return_value=mock_response)

        result = await mock_llm_client.generate("Test prompt")

        assert result.text == "Generated text response"
        assert result.model_used == "llama-3.1-8b-instruct"
        assert result.tokens_used == 100
        assert result.inference_time is not None

    @pytest.mark.asyncio
    async def test_analyze_coordination_success(self, mock_llm_client):
        """Test successful coordination analysis."""
        # Mock the generate method
        mock_response = MagicMock()
        mock_response.text = """
        {
            "coordination_confidence": 0.75,
            "evidence_breakdown": {
                "temporal_correlation": 0.8,
                "behavioral_similarity": 0.7,
                "infrastructure_clustering": 0.6,
                "geographic_proximity": 0.5,
                "payload_similarity": 0.9
            },
            "reasoning": "Strong evidence of coordination",
            "key_factors": ["temporal_sync", "similar_payloads"],
            "assessment": "coordinated"
        }
        """
        mock_response.model_used = "llama-3.1-8b-instruct"

        with patch.object(mock_llm_client, "generate", return_value=mock_response):
            sessions = [
                {
                    "source_ip": "192.168.1.1",
                    "timestamp": "2025-07-28T10:00:00Z",
                    "payload": "GET /admin HTTP/1.1",
                }
            ]

            result = await mock_llm_client.analyze_coordination(sessions)

            assert isinstance(result, CoordinationAnalysisResult)
            assert result.coordination_confidence == 0.75
            assert result.evidence_breakdown["temporal_correlation"] == 0.8
            assert result.reasoning == "Strong evidence of coordination"
            assert result.key_factors == ["temporal_sync", "similar_payloads"]

    @pytest.mark.asyncio
    async def test_analyze_coordination_fallback(self, mock_llm_client):
        """Test coordination analysis with fallback parsing."""
        # Mock the generate method to return unstructured text
        mock_response = MagicMock()
        mock_response.text = (
            "This appears to be coordinated activity with high confidence."
        )
        mock_response.model_used = "llama-3.1-8b-instruct"

        with patch.object(mock_llm_client, "generate", return_value=mock_response):
            sessions = [
                {
                    "source_ip": "192.168.1.1",
                    "timestamp": "2025-07-28T10:00:00Z",
                    "payload": "GET /admin HTTP/1.1",
                }
            ]

            result = await mock_llm_client.analyze_coordination(sessions)

            assert isinstance(result, CoordinationAnalysisResult)
            assert result.coordination_confidence > 0.0
            assert result.model_used == "llama-3.1-8b-instruct"


class TestPrompts:
    """Test prompt generation functions."""

    def test_create_coordination_prompt(self):
        """Test coordination prompt creation."""
        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        prompt = create_coordination_prompt(
            sessions=sessions,
            analysis_type="comprehensive",
            context={"test": "value"},
            instructions="Test instructions",
        )

        assert "Session 1:" in prompt
        assert "192.168.1.1" in prompt
        assert "Test instructions" in prompt
        # The analysis_type is used internally but not directly in the prompt text
        assert "cybersecurity analyst" in prompt

    def test_format_attack_sessions(self):
        """Test attack session formatting."""
        from services.llm.prompts import format_attack_sessions

        sessions = [
            {
                "source_ip": "192.168.1.1",
                "timestamp": "2025-07-28T10:00:00Z",
                "target_port": 80,
                "protocol": "HTTP",
                "payload": "GET /admin HTTP/1.1",
            }
        ]

        formatted = format_attack_sessions(sessions)

        assert "Session 1:" in formatted
        assert "192.168.1.1" in formatted
        assert "80" in formatted
        assert "HTTP" in formatted
        assert "GET /admin HTTP/1.1" in formatted


class TestCoordinationAnalysisResult:
    """Test CoordinationAnalysisResult class."""

    def test_coordination_analysis_result_validation(self):
        """Test CoordinationAnalysisResult validation."""
        # Valid result
        result = CoordinationAnalysisResult(
            coordination_confidence=0.75,
            evidence_breakdown={
                "temporal_correlation": 0.8,
                "behavioral_similarity": 0.7,
            },
            reasoning="Test reasoning",
            key_factors=["factor1", "factor2"],
            model_used="test-model",
        )

        assert result.coordination_confidence == 0.75
        assert result.evidence_breakdown["temporal_correlation"] == 0.8

        # Invalid confidence score
        with pytest.raises(ValueError):
            CoordinationAnalysisResult(
                coordination_confidence=1.5,  # Above max
                evidence_breakdown={},
                reasoning="Test",
                key_factors=[],
                model_used="test",
            )

        # Invalid evidence scores
        with pytest.raises(ValueError):
            CoordinationAnalysisResult(
                coordination_confidence=0.5,
                evidence_breakdown={"test": 1.5},  # Above max
                reasoning="Test",
                key_factors=[],
                model_used="test",
            )
