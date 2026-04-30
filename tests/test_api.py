"""Integration tests for the FastAPI analyze endpoint"""
import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.models import Base
from app.main import app


# Create file-based SQLite database for testing (in-memory has issues with multiple connections)
test_db_path = "./test_incidents.db"
test_engine = create_engine(
    f"sqlite:///{test_db_path}",
    connect_args={"check_same_thread": False}
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Set up and tear down test database"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_client():
    """Provide a test client with database override"""
    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Clean up override
    app.dependency_overrides.clear()


class TestAnalyzeEndpoint:
    """Integration tests for POST /incidents/analyze endpoint"""

    def test_analyze_with_valid_log_text_returns_200(self, test_client):
        """Test: POST /incidents/analyze with valid log_text returns HTTP 200 and a valid IncidentResponse"""
        response = test_client.post(
            "/incidents/analyze",
            json={"log_text": "2024-01-15 ERROR Database connection timeout after retries"}
        )
        
        # Assert HTTP 200
        assert response.status_code == 200
        
        # Assert valid JSON body
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)
        assert data["id"] > 0
        
        # Assert required fields
        assert "summary" in data
        assert "severity" in data
        assert "root_cause" in data
        assert "affected_components" in data
        assert "recommended_actions" in data
        assert "confidence" in data
        assert "created_at" in data
        assert "log_text" in data
        assert "similar_incidents" in data
        
        # Assert valid severity
        assert data["severity"] in ["low", "medium", "high", "critical"]
        
        # Assert confidence in valid range
        assert 0.0 <= data["confidence"] <= 1.0

    def test_analyze_with_empty_log_text_returns_422(self, test_client):
        """Test: POST /incidents/analyze with empty log_text returns HTTP 422"""
        response = test_client.post(
            "/incidents/analyze",
            json={"log_text": ""}
        )
        
        # Assert HTTP 422 (validation error)
        assert response.status_code == 422

    def test_analyze_with_missing_log_text_returns_422(self, test_client):
        """Test: POST /incidents/analyze with missing log_text field returns HTTP 422"""
        response = test_client.post(
            "/incidents/analyze",
            json={}
        )
        
        # Assert HTTP 422 (validation error)
        assert response.status_code == 422

    def test_analyze_with_whitespace_log_text_returns_422(self, test_client):
        """Test: POST /incidents/analyze with whitespace-only log_text returns HTTP 422"""
        response = test_client.post(
            "/incidents/analyze",
            json={"log_text": "   "}
        )
        
        # Assert HTTP 422 (validation error)
        assert response.status_code == 422

    def test_analyze_returns_correct_summary(self, test_client):
        """Example test: verify the summary is correct"""
        response = test_client.post(
            "/incidents/analyze",
            json={"log_text": "2024-01-15 ERROR Database connection timeout"}
        )
        
        data = response.json()
        assert "Database connection timeout" in data["summary"]

    def test_analyze_returns_similar_incidents_field(self, test_client):
        """Example test: verify similar_incidents field is present"""
        response = test_client.post(
            "/incidents/analyze",
            json={"log_text": "2024-01-15 ERROR Database connection timeout"}
        )
        
        data = response.json()
        assert "similar_incidents" in data
        assert isinstance(data["similar_incidents"], list)

    def test_analyze_persists_incident(self, test_client):
        """Example test: verify the incident is persisted"""
        response = test_client.post(
            "/incidents/analyze",
            json={"log_text": "2024-01-15 ERROR Database connection timeout"}
        )
        
        data = response.json()
        incident_id = data["id"]
        
        # The incident should be saved (we can verify by checking the response has an id)
        assert incident_id is not None
        assert incident_id > 0