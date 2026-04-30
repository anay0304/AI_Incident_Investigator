"""Incident Analyzer Service"""
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas import IncidentCreate, IncidentResponse, IncidentSummary, SeverityEnum
from app.services.llm_client import LLMClient


class IncidentAnalyzer:
    """Service for analyzing log text and creating incident records"""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the analyzer with an LLM client
        
        Args:
            llm_client: LLM client for analyzing log text
        """
        self.llm_client = llm_client
        # SimilarityService will be wired in Task 7 (stub for now)
        self._similarity_service = None
    
    def analyze(self, log_text: str, db: Session) -> IncidentResponse:
        """
        Analyze log text and create an incident record
        
        Args:
            log_text: Raw log text to analyze
            db: Database session for persistence
            
        Returns:
            IncidentResponse with full incident details
            
        Raises:
            HTTPException(500): If LLM analysis fails or validation fails
        """
        try:
            # Call the LLM client to analyze the log text
            raw_result = self.llm_client.analyze(log_text)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"LLM analysis failed: {str(e)}"
            )
        
        try:
            # Validate the returned data against our schema
            incident_data = IncidentCreate(**raw_result)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid LLM response: {str(e)}"
            )
        
        try:
            # Create the database record
            from app.models import Incident
            
            db_incident = Incident(
                summary=incident_data.summary,
                severity=incident_data.severity.value,
                root_cause=incident_data.root_cause,
                affected_component=", ".join(incident_data.affected_components),
                evidence=json.dumps(incident_data.affected_components),
                recommended_steps=json.dumps(incident_data.recommended_actions),
                confidence=incident_data.confidence,
                log_text=log_text
            )
            
            db.add(db_incident)
            db.commit()
            db.refresh(db_incident)
            
            # Stub: similar incidents will be added in Task 7
            similar_incidents: list[IncidentSummary] = []
            
            # Build and return the response
            return IncidentResponse(
                id=db_incident.id,
                log_text=db_incident.log_text,
                summary=db_incident.summary,
                severity=SeverityEnum(db_incident.severity),
                root_cause=db_incident.root_cause,
                affected_components=json.loads(db_incident.evidence),
                recommended_actions=json.loads(db_incident.recommended_steps),
                confidence=db_incident.confidence,
                created_at=db_incident.created_at,
                similar_incidents=similar_incidents
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Wrap any other errors as HTTP 500
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save incident: {str(e)}"
            )