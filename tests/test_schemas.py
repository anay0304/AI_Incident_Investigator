"""Property tests for schema validation"""
import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from app.schemas import (
    AnalyzeRequest,
    IncidentResponse,
    IncidentCreate,
    SeverityEnum,
)
from pydantic import ValidationError


class TestAnalyzeRequestSchema:
    """Tests for AnalyzeRequest schema validation"""

    @given(st.text())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
    def test_request_validation_rejects_whitespace_only_strings(self, text):
        """Property 1: Request Validation Rejects Invalid Inputs"""
        # Filter to whitespace-only strings
        assume(text.strip() == "")
        
        with pytest.raises(ValidationError):
            AnalyzeRequest(log_text=text)

    def test_valid_log_text_passes(self):
        """Example test: valid log text passes validation"""
        valid_log = "2024-01-15 10:30:45 ERROR Connection failed to database"
        request = AnalyzeRequest(log_text=valid_log)
        assert request.log_text == valid_log

    def test_whitespace_only_string_rejected(self):
        """Example test: specific invalid input produces correct error"""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(log_text="   ")
        assert "log_text" in str(exc_info.value)

    def test_empty_string_rejected(self):
        """Example test: empty string is rejected"""
        with pytest.raises(ValidationError):
            AnalyzeRequest(log_text="")


class TestIncidentResponseSchema:
    """Tests for IncidentResponse schema validation"""

    @given(st.floats())
    @settings(max_examples=50)
    def test_confidence_outside_valid_range_rejected(self, confidence):
        """Property 2a: IncidentResponse rejects confidence outside [0.0, 1.0]"""
        # Filter to values outside the valid range
        assume(confidence < 0.0 or confidence > 1.0)
        
        # Create valid data for other fields
        valid_data = {
            "id": 1,
            "log_text": "Sample log text",
            "summary": "Test incident",
            "severity": SeverityEnum.medium,
            "root_cause": "Test cause",
            "affected_components": ["component1"],
            "recommended_actions": ["action1"],
            "confidence": confidence,
            "created_at": "2024-01-15T10:00:00",
        }
        
        with pytest.raises(ValidationError):
            IncidentResponse(**valid_data)

    @given(st.text())
    @settings(max_examples=50)
    def test_invalid_severity_strings_rejected(self, text):
        """Property 2b: IncidentResponse rejects invalid severity strings"""
        # Filter to invalid severity values (not in enum)
        assume(text.lower() not in ["low", "medium", "high", "critical"])
        
        valid_data = {
            "id": 1,
            "log_text": "Sample log text",
            "summary": "Test incident",
            "severity": text,  # Invalid severity
            "root_cause": "Test cause",
            "affected_components": ["component1"],
            "recommended_actions": ["action1"],
            "confidence": 0.5,
            "created_at": "2024-01-15T10:00:00",
        }
        
        with pytest.raises(ValidationError):
            IncidentResponse(**valid_data)

    def test_valid_confidence_values_pass(self):
        """Example test: valid confidence values pass"""
        valid_confidences = [0.0, 0.5, 1.0, 0.75]
        
        for confidence in valid_confidences:
            response = IncidentResponse(
                id=1,
                log_text="Sample log",
                summary="Test",
                severity=SeverityEnum.low,
                root_cause="Cause",
                affected_components=["comp1"],
                recommended_actions=["action1"],
                confidence=confidence,
                created_at="2024-01-15T10:00:00",
            )
            assert response.confidence == confidence

    def test_valid_severity_values_pass(self):
        """Example test: valid severity values pass"""
        for severity in SeverityEnum:
            response = IncidentResponse(
                id=1,
                log_text="Sample log",
                summary="Test",
                severity=severity,
                root_cause="Cause",
                affected_components=["comp1"],
                recommended_actions=["action1"],
                confidence=0.5,
                created_at="2024-01-15T10:00:00",
            )
            assert response.severity == severity

    def test_confidence_below_zero_rejected(self):
        """Example test: specific invalid input - confidence below 0"""
        with pytest.raises(ValidationError) as exc_info:
            IncidentResponse(
                id=1,
                log_text="Sample log",
                summary="Test",
                severity=SeverityEnum.low,
                root_cause="Cause",
                affected_components=["comp1"],
                recommended_actions=["action1"],
                confidence=-0.1,
                created_at="2024-01-15T10:00:00",
            )
        assert "confidence" in str(exc_info.value)

    def test_confidence_above_one_rejected(self):
        """Example test: specific invalid input - confidence above 1"""
        with pytest.raises(ValidationError) as exc_info:
            IncidentResponse(
                id=1,
                log_text="Sample log",
                summary="Test",
                severity=SeverityEnum.low,
                root_cause="Cause",
                affected_components=["comp1"],
                recommended_actions=["action1"],
                confidence=1.5,
                created_at="2024-01-15T10:00:00",
            )
        assert "confidence" in str(exc_info.value)

    def test_invalid_severity_string_rejected(self):
        """Example test: specific invalid severity string"""
        with pytest.raises(ValidationError) as exc_info:
            IncidentResponse(
                id=1,
                log_text="Sample log",
                summary="Test",
                severity="invalid_severity",
                root_cause="Cause",
                affected_components=["comp1"],
                recommended_actions=["action1"],
                confidence=0.5,
                created_at="2024-01-15T10:00:00",
            )
        assert "severity" in str(exc_info.value)


class TestIncidentCreateSchema:
    """Tests for IncidentCreate schema validation"""

    def test_valid_incident_create_passes(self):
        """Example test: valid IncidentCreate passes"""
        incident = IncidentCreate(
            summary="Test summary",
            severity=SeverityEnum.high,
            root_cause="Root cause",
            affected_components=["comp1", "comp2"],
            recommended_actions=["action1", "action2"],
            confidence=0.85,
        )
        assert incident.summary == "Test summary"
        assert incident.confidence == 0.85

    def test_empty_list_rejected(self):
        """Example test: empty list for affected_components is rejected"""
        with pytest.raises(ValidationError):
            IncidentCreate(
                summary="Test",
                severity=SeverityEnum.medium,
                root_cause="Cause",
                affected_components=[],
                recommended_actions=["action1"],
                confidence=0.5,
            )