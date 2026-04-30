"""Unit tests for the IncidentAnalyzer service"""
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Incident
from app.services.analyzer import IncidentAnalyzer
from app.services.llm_client import MockClient, LLMClient
from app.schemas import SeverityEnum


# Create in-memory SQLite database for testing
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False}
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Set up and tear down test database"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def mock_client():
    """Provide a MockClient for tests"""
    return MockClient()


@pytest.fixture
def analyzer(mock_client):
    """Provide an IncidentAnalyzer with MockClient"""
    return IncidentAnalyzer(mock_client)


class TestIncidentAnalyzer:
    """Tests for IncidentAnalyzer service"""

    def test_analyze_returns_incident_response_with_id(self, analyzer, db_session):
        """Test: analyze() returns an IncidentResponse with a non-null integer id"""
        log_text = "2024-01-15 ERROR Database connection timeout after retries"
        
        result = analyzer.analyze(log_text, db_session)
        
        # Assert it's an IncidentResponse
        assert result is not None
        assert hasattr(result, 'id')
        
        # Assert id is a non-null integer
        assert result.id is not None
        assert isinstance(result.id, int)
        assert result.id > 0

    def test_analyze_persists_incident(self, analyzer, db_session):
        """Test: analyze() persists the incident so it can be retrieved from the DB"""
        log_text = "2024-01-15 ERROR Database connection timeout after retries"
        
        # Analyze the log text
        result = analyzer.analyze(log_text, db_session)
        incident_id = result.id
        
        # Retrieve the incident from the database
        retrieved = db_session.query(Incident).filter(Incident.id == incident_id).first()
        
        # Assert the incident was saved
        assert retrieved is not None
        assert retrieved.id == incident_id
        assert retrieved.summary == result.summary
        assert retrieved.severity == result.severity.value
        assert retrieved.log_text == log_text

    def test_llm_exception_converted_to_http_exception(self, db_session):
        """Test: LLM exception is converted to HTTPException(500)"""
        # Create a mock client that raises an exception
        class FailingClient(LLMClient):
            def analyze(self, log_text: str):
                raise RuntimeError("LLM service unavailable")
        
        analyzer = IncidentAnalyzer(FailingClient())
        
        # Assert that the exception is converted to HTTPException(500)
        with pytest.raises(HTTPException) as exc_info:
            analyzer.analyze("test log", db_session)
        
        assert exc_info.value.status_code == 500
        assert "LLM analysis failed" in exc_info.value.detail

    def test_invalid_llm_dict_raises_http_exception(self, db_session):
        """Test: Invalid LLM dict (bad severity) raises HTTPException(500)"""
        # Create a mock client that returns invalid data
        class InvalidClient(LLMClient):
            def analyze(self, log_text: str):
                return {
                    "summary": "Test incident",
                    "severity": "invalid_severity",  # Invalid severity
                    "root_cause": "Test cause",
                    "affected_components": ["comp1"],
                    "recommended_actions": ["action1"],
                    "confidence": 0.5
                }
        
        analyzer = IncidentAnalyzer(InvalidClient())
        
        # Assert that validation failure raises HTTPException(500)
        with pytest.raises(HTTPException) as exc_info:
            analyzer.analyze("test log", db_session)
        
        assert exc_info.value.status_code == 500
        assert "Invalid LLM response" in exc_info.value.detail

    def test_analyze_returns_correct_summary(self, analyzer, db_session):
        """Example test: verify the summary is correct"""
        log_text = "2024-01-15 ERROR Database connection timeout"
        
        result = analyzer.analyze(log_text, db_session)
        
        assert result.summary == "Database connection timeout after multiple retry attempts"
        assert result.severity == SeverityEnum.high

    def test_analyze_returns_correct_confidence(self, analyzer, db_session):
        """Example test: verify confidence is in valid range"""
        log_text = "2024-01-15 ERROR Database connection timeout"
        
        result = analyzer.analyze(log_text, db_session)
        
        assert 0.0 <= result.confidence <= 1.0
        assert result.confidence == 0.92

    def test_analyze_saves_log_text(self, analyzer, db_session):
        """Example test: verify original log text is saved"""
        log_text = "2024-01-15 ERROR Database connection timeout after retries"
        
        result = analyzer.analyze(log_text, db_session)
        
        assert result.log_text == log_text

    def test_analyze_handles_empty_confidence(self, db_session):
        """Example test: verify handling of edge case with zero confidence"""
        class ZeroConfidenceClient(LLMClient):
            def analyze(self, log_text: str):
                return {
                    "summary": "Test incident",
                    "severity": "low",
                    "root_cause": "Test cause",
                    "affected_components": ["comp1"],
                    "recommended_actions": ["action1"],
                    "confidence": 0.0
                }
        
        analyzer = IncidentAnalyzer(ZeroConfidenceClient())
        result = analyzer.analyze("test log", db_session)
        
        assert result.confidence == 0.0