"""Property tests for database persistence"""
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Incident
from app.schemas import IncidentCreate, SeverityEnum


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


class TestIncidentPersistence:
    """Tests for Incident database persistence"""

    def test_incident_persistence_round_trip(self):
        """Property 3: Incident Persistence Round-Trip"""
        # Create incident data
        incident_data = IncidentCreate(
            summary="Database connection timeout after multiple retry attempts",
            severity=SeverityEnum.high,
            root_cause="PostgreSQL connection pool exhausted due to unclosed connections",
            affected_components=["payment-service", "postgresql-primary", "connection-pool"],
            recommended_actions=["Restart service", "Increase pool size"],
            confidence=0.92
        )
        
        # Save to database
        db = TestSession()
        try:
            db_incident = Incident(
                summary=incident_data.summary,
                severity=incident_data.severity.value,
                root_cause=incident_data.root_cause,
                affected_component=", ".join(incident_data.affected_components),
                evidence=json.dumps(incident_data.affected_components),
                recommended_steps=json.dumps(incident_data.recommended_actions),
                confidence=incident_data.confidence,
                log_text="test log text for persistence test"
            )
            db.add(db_incident)
            db.commit()
            db.refresh(db_incident)
            
            # Retrieve by id
            retrieved = db.query(Incident).filter(Incident.id == db_incident.id).first()
            
            # Assert all fields match
            assert retrieved is not None, "Incident should be retrievable by id"
            assert retrieved.summary == incident_data.summary
            assert retrieved.severity == incident_data.severity.value
            assert retrieved.root_cause == incident_data.root_cause
            assert retrieved.confidence == incident_data.confidence
        finally:
            db.close()

    def test_all_ids_are_distinct(self):
        """Assert all id values across N saved incidents are distinct positive integers"""
        db = TestSession()
        try:
            # Create multiple incidents
            incidents_data = [
                IncidentCreate(
                    summary=f"Test incident {i}",
                    severity=SeverityEnum.medium,
                    root_cause="Test cause",
                    affected_components=["component1"],
                    recommended_actions=["action1"],
                    confidence=0.5
                )
                for i in range(3)
            ]
            
            saved_ids = []
            for incident_data in incidents_data:
                db_incident = Incident(
                    summary=incident_data.summary,
                    severity=incident_data.severity.value,
                    root_cause=incident_data.root_cause,
                    affected_component=", ".join(incident_data.affected_components),
                    evidence=json.dumps(incident_data.affected_components),
                    recommended_steps=json.dumps(incident_data.recommended_actions),
                    confidence=incident_data.confidence,
                    log_text="test log"
                )
                db.add(db_incident)
                db.commit()
                db.refresh(db_incident)
                saved_ids.append(db_incident.id)
            
            # Assert all ids are distinct
            assert len(saved_ids) == len(set(saved_ids)), "All ids should be distinct"
            
            # Assert all ids are positive integers
            for id_value in saved_ids:
                assert isinstance(id_value, int), "Id should be an integer"
                assert id_value > 0, "Id should be a positive integer"
        finally:
            db.close()

    def test_persistence_round_trip_specific(self):
        """Example test: specific incident data round-trip"""
        incident_data = IncidentCreate(
            summary="Database connection timeout",
            severity=SeverityEnum.high,
            root_cause="Connection pool exhausted",
            affected_components=["payment-service", "database"],
            recommended_actions=["Restart service", "Increase pool size"],
            confidence=0.85
        )
        
        db = TestSession()
        try:
            # Save
            db_incident = Incident(
                summary=incident_data.summary,
                severity=incident_data.severity.value,
                root_cause=incident_data.root_cause,
                affected_component=", ".join(incident_data.affected_components),
                evidence=json.dumps(incident_data.affected_components),
                recommended_steps=json.dumps(incident_data.recommended_actions),
                confidence=incident_data.confidence,
                log_text="test log"
            )
            db.add(db_incident)
            db.commit()
            db.refresh(db_incident)
            
            original_id = db_incident.id
            
            # Retrieve
            retrieved = db.query(Incident).filter(Incident.id == original_id).first()
            
            # Verify
            assert retrieved is not None
            assert retrieved.summary == "Database connection timeout"
            assert retrieved.severity == "high"
            assert retrieved.confidence == 0.85
        finally:
            db.close()

    def test_multiple_incidents_have_unique_ids(self):
        """Example test: multiple incidents get unique ids"""
        db = TestSession()
        try:
            ids = []
            for i in range(5):
                incident = Incident(
                    summary=f"Test incident {i}",
                    severity="low",
                    root_cause="Test cause",
                    affected_component="test",
                    evidence=json.dumps(["test"]),
                    recommended_steps=json.dumps(["test"]),
                    confidence=0.5,
                    log_text="test"
                )
                db.add(incident)
                db.commit()
                db.refresh(incident)
                ids.append(incident.id)
            
            # All ids should be unique
            assert len(set(ids)) == 5
        finally:
            db.close()

    def test_persistence_with_different_severity_levels(self):
        """Example test: incidents with different severity levels"""
        db = TestSession()
        try:
            for severity in SeverityEnum:
                incident = Incident(
                    summary=f"Test {severity.value} incident",
                    severity=severity.value,
                    root_cause="Test cause",
                    affected_component="test",
                    evidence=json.dumps(["test"]),
                    recommended_steps=json.dumps(["test"]),
                    confidence=0.5,
                    log_text="test"
                )
                db.add(incident)
            
            db.commit()
            
            # Verify all were saved
            count = db.query(Incident).count()
            assert count == 4, "Should have 4 incidents with different severities"
        finally:
            db.close()