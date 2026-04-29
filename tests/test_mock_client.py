"""Property tests for Mock LLM client"""
import pytest
from hypothesis import given, settings, strategies as st

from app.services.llm_client import MockClient
from app.schemas import IncidentCreate
from pydantic import ValidationError


class TestMockClient:
    """Tests for MockClient"""

    @given(st.text(min_size=1))
    @settings(max_examples=50)
    def test_mock_client_always_returns_valid_data(self, log_text):
        """Property 6: Mock Client Always Returns Valid Data"""
        client = MockClient()
        result = client.analyze(log_text)
        
        # Should return a dictionary
        assert isinstance(result, dict)
        
        # Should have all required fields
        required_fields = [
            "summary",
            "severity",
            "root_cause",
            "affected_components",
            "recommended_actions",
            "confidence"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        # Should pass IncidentCreate validation without errors
        try:
            incident = IncidentCreate(**result)
        except ValidationError as e:
            pytest.fail(f"MockClient returned invalid data: {e}")
        
        # Verify the data is meaningful
        assert incident.summary, "Summary should not be empty"
        assert incident.root_cause, "Root cause should not be empty"
        assert incident.affected_components, "Affected components should not be empty"
        assert incident.recommended_actions, "Recommended actions should not be empty"
        assert 0.0 <= incident.confidence <= 1.0, "Confidence should be between 0 and 1"

    def test_mock_client_determinism(self):
        """Assert determinism: same input always produces same output"""
        client = MockClient()
        log_text = "Any log text will produce the same result"
        
        # Call analyze multiple times with the same input
        result1 = client.analyze(log_text)
        result2 = client.analyze(log_text)
        result3 = client.analyze(log_text)
        
        # All results should be identical
        assert result1 == result2 == result3, "MockClient should return deterministic results"

    def test_mock_client_returns_expected_values(self):
        """Example test: verify specific expected values"""
        client = MockClient()
        result = client.analyze("test log")
        
        # Check specific expected values
        assert result["summary"] == "Database connection timeout after multiple retry attempts"
        assert result["severity"] == "high"
        assert result["confidence"] == 0.92
        assert "payment-service" in result["affected_components"]
        assert "postgresql-primary" in result["affected_components"]

    def test_mock_client_returns_valid_severity(self):
        """Example test: severity is a valid enum value"""
        client = MockClient()
        result = client.analyze("test log")
        
        valid_severities = ["low", "medium", "high", "critical"]
        assert result["severity"] in valid_severities, f"Invalid severity: {result['severity']}"

    def test_mock_client_returns_valid_confidence(self):
        """Example test: confidence is in valid range"""
        client = MockClient()
        result = client.analyze("test log")
        
        assert 0.0 <= result["confidence"] <= 1.0, f"Invalid confidence: {result['confidence']}"

    def test_mock_client_returns_non_empty_lists(self):
        """Example test: lists are not empty"""
        client = MockClient()
        result = client.analyze("test log")
        
        assert len(result["affected_components"]) > 0, "Affected components should not be empty"
        assert len(result["recommended_actions"]) > 0, "Recommended actions should not be empty"