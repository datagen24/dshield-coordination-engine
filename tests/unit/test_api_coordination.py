"""Unit tests for coordination analysis endpoints."""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from services.api.routers.coordination import (
    AttackSession,
    CoordinationRequest,
    CoordinationResponse,
    analyze_coordination,
    bulk_analysis,
    get_analysis_results,
    process_coordination_analysis,
)


class TestAnalyzeCoordination:
    """Test coordination analysis endpoint."""

    def test_analyze_coordination_success(
        self, sample_coordination_request, mock_settings
    ):
        """Test successful coordination analysis."""
        background_tasks = Mock()
        current_user = "test-user"

        result = analyze_coordination(
            sample_coordination_request, background_tasks, current_user
        )

        assert isinstance(result, CoordinationResponse)
        assert result.status == "queued"

    def test_analyze_coordination_insufficient_sessions(self, mock_settings):
        """Test coordination analysis with insufficient sessions."""
        mock_settings.analysis_max_sessions = 1000
        request = CoordinationRequest(
            attack_sessions=[
                AttackSession(
                    source_ip="192.168.1.1",
                    timestamp="2025-07-28T10:00:00Z",
                    payload="test payload",
                )
            ],  # Only one session
            analysis_depth="standard",
        )

        background_tasks = Mock()
        current_user = "test-user"

        with pytest.raises(HTTPException) as exc_info:
            analyze_coordination(request, background_tasks, current_user)

        assert exc_info.value.status_code == 400
        assert "At least 2 attack sessions" in str(exc_info.value.detail)

    def test_analyze_coordination_too_many_sessions(self, mock_settings):
        """Test coordination analysis with too many sessions."""
        mock_settings.analysis_max_sessions = 2
        request = CoordinationRequest(
            attack_sessions=[
                AttackSession(
                    source_ip="192.168.1.1",
                    timestamp="2025-07-28T10:00:00Z",
                    payload="test payload 1",
                ),
                AttackSession(
                    source_ip="192.168.1.2",
                    timestamp="2025-07-28T10:05:00Z",
                    payload="test payload 2",
                ),
                AttackSession(
                    source_ip="192.168.1.3",
                    timestamp="2025-07-28T10:10:00Z",
                    payload="test payload 3",
                ),
            ],  # 3 sessions
            analysis_depth="standard",
        )

        background_tasks = Mock()
        current_user = "test-user"

        with pytest.raises(HTTPException) as exc_info:
            analyze_coordination(request, background_tasks, current_user)

        assert exc_info.value.status_code == 400
        assert "Maximum 2 sessions allowed" in str(exc_info.value.detail)


class TestGetAnalysisResults:
    """Test analysis results retrieval endpoint."""

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
    async def test_process_coordination_analysis_success(self, sample_attack_sessions):
        """Test successful background analysis processing."""
        analysis_id = "test-analysis-id"
        attack_sessions = [
            AttackSession(**session) for session in sample_attack_sessions
        ]
        analysis_depth = "standard"
        user = "test-user"

        # This should not raise an exception
        await process_coordination_analysis(
            analysis_id, attack_sessions, analysis_depth, user
        )
