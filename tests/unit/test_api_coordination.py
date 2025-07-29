"""Unit tests for coordination analysis endpoints."""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch

from services.api.routers.coordination import (
    analyze_coordination,
    get_analysis_results,
    bulk_analysis,
    process_coordination_analysis
)
from services.api.routers.coordination import (
    AttackSession,
    CoordinationRequest,
    CoordinationResponse
)


class TestAttackSession:
    """Test AttackSession model."""

    @pytest.mark.unit
    def test_attack_session_valid(self):
        """Test valid attack session creation."""
        session = AttackSession(
            source_ip="192.168.1.1",
            timestamp="2025-01-28T10:00:00Z",
            payload="test payload"
        )
        assert session.source_ip == "192.168.1.1"
        assert session.payload == "test payload"

    @pytest.mark.unit
    def test_attack_session_with_optional_fields(self):
        """Test attack session with optional fields."""
        session = AttackSession(
            source_ip="192.168.1.1",
            timestamp="2025-01-28T10:00:00Z",
            payload="test payload",
            target_port=22,
            protocol="ssh"
        )
        assert session.target_port == 22
        assert session.protocol == "ssh"


class TestCoordinationRequest:
    """Test CoordinationRequest model."""

    @pytest.mark.unit
    def test_coordination_request_valid(self, sample_attack_sessions):
        """Test valid coordination request creation."""
        request = CoordinationRequest(
            attack_sessions=sample_attack_sessions,
            analysis_depth="standard"
        )
        assert len(request.attack_sessions) == 3
        assert request.analysis_depth == "standard"

    @pytest.mark.unit
    def test_coordination_request_with_callback(self, sample_attack_sessions):
        """Test coordination request with callback URL."""
        request = CoordinationRequest(
            attack_sessions=sample_attack_sessions,
            analysis_depth="deep",
            callback_url="http://example.com/callback"
        )
        assert request.callback_url == "http://example.com/callback"


class TestAnalyzeCoordination:
    """Test coordination analysis endpoint."""

    @pytest.mark.unit
    @patch("services.api.routers.coordination.process_coordination_analysis")
    def test_analyze_coordination_success(
        self, mock_process, sample_coordination_request, mock_settings
    ):
        """Test successful coordination analysis request."""
        mock_settings.analysis_max_sessions = 1000
        background_tasks = Mock()
        current_user = "test-user"
        
        result = analyze_coordination(
            sample_coordination_request,
            background_tasks,
            current_user
        )
        
        assert isinstance(result, CoordinationResponse)
        assert result.status == "queued"
        assert result.analysis_id is not None
        background_tasks.add_task.assert_called_once()

    @pytest.mark.unit
    def test_analyze_coordination_insufficient_sessions(self, mock_settings):
        """Test coordination analysis with insufficient sessions."""
        mock_settings.analysis_max_sessions = 1000
        request = CoordinationRequest(
            attack_sessions=[sample_attack_sessions[0]],  # Only one session
            analysis_depth="standard"
        )
        background_tasks = Mock()
        current_user = "test-user"
        
        with pytest.raises(HTTPException) as exc_info:
            analyze_coordination(request, background_tasks, current_user)
        
        assert exc_info.value.status_code == 400
        assert "At least 2 attack sessions" in str(exc_info.value.detail)

    @pytest.mark.unit
    def test_analyze_coordination_too_many_sessions(self, mock_settings):
        """Test coordination analysis with too many sessions."""
        mock_settings.analysis_max_sessions = 2
        request = CoordinationRequest(
            attack_sessions=sample_attack_sessions,  # 3 sessions
            analysis_depth="standard"
        )
        background_tasks = Mock()
        current_user = "test-user"
        
        with pytest.raises(HTTPException) as exc_info:
            analyze_coordination(request, background_tasks, current_user)
        
        assert exc_info.value.status_code == 400
        assert "Maximum 2 sessions allowed" in str(exc_info.value.detail)


class TestGetAnalysisResults:
    """Test analysis results retrieval."""

    @pytest.mark.unit
    def test_get_analysis_results_success(self):
        """Test successful analysis results retrieval."""
        analysis_id = "test-analysis-id"
        current_user = "test-user"
        
        result = get_analysis_results(analysis_id, current_user)
        
        assert isinstance(result, CoordinationResponse)
        assert result.analysis_id == analysis_id
        assert result.status == "completed"
        assert result.coordination_confidence == 0.75
        assert result.evidence is not None
        assert result.enrichment_applied is True


class TestBulkAnalysis:
    """Test bulk analysis endpoint."""

    @pytest.mark.unit
    def test_bulk_analysis_success(self, sample_attack_sessions):
        """Test successful bulk analysis."""
        session_batches = [sample_attack_sessions]
        current_user = "test-user"
        
        result = bulk_analysis(session_batches, current_user)
        
        assert "analysis_ids" in result
        assert "status" in result
        assert result["status"] == "queued"
        assert len(result["analysis_ids"]) == 1


class TestProcessCoordinationAnalysis:
    """Test background coordination analysis processing."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_coordination_analysis_success(self, sample_attack_sessions):
        """Test successful background analysis processing."""
        analysis_id = "test-analysis-id"
        analysis_depth = "standard"
        user = "test-user"
        
        # This should not raise an exception
        await process_coordination_analysis(
            analysis_id,
            sample_attack_sessions,
            analysis_depth,
            user
        ) 