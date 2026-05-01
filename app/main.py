"""FastAPI application for AI Incident Investigator"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.models import Base, Incident
from app.schemas import AnalyzeRequest, IncidentResponse, IncidentSummary, SeverityEnum
from app.services.llm_client import get_llm_client
from app.services.analyzer import IncidentAnalyzer


# Initialize LLM client and analyzer at module level
llm_client = get_llm_client()
analyzer = IncidentAnalyzer(llm_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize database on startup"""
    # Create all database tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown (if needed)
    pass


# Create FastAPI application
app = FastAPI(
    title="AI Incident Investigator",
    description="API for analyzing log text and generating structured incident reports using LLM",
    version="1.0.0",
    lifespan=lifespan
)


@app.post(
    "/incidents/analyze",
    response_model=IncidentResponse,
    summary="Analyze log text",
    description="Accept raw log text, analyze it with an LLM, and return a structured incident report"
)
def analyze_incident(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
) -> IncidentResponse:
    """
    Analyze log text and create an incident record
    
    Args:
        request: AnalyzeRequest containing the log text
        db: Database session
        
    Returns:
        IncidentResponse with full incident details
    """
    return analyzer.analyze(request.log_text, db)


@app.get(
    "/incidents",
    response_model=list[IncidentResponse],
    summary="List all incidents",
    description="Get all incidents ordered by creation date (newest first)"
)
def list_incidents(
    db: Session = Depends(get_db)
) -> list[IncidentResponse]:
    """
    List all incidents
    
    Args:
        db: Database session
        
    Returns:
        List of IncidentResponse objects
    """
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    
    return [
        IncidentResponse(
            id=incident.id,
            log_text=incident.log_text,
            summary=incident.summary,
            severity=SeverityEnum(incident.severity),
            root_cause=incident.root_cause,
            affected_components=json.loads(incident.evidence),
            recommended_actions=json.loads(incident.recommended_steps),
            confidence=incident.confidence,
            created_at=incident.created_at,
            similar_incidents=[]
        )
        for incident in incidents
    ]


@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident by ID",
    description="Get a specific incident by its ID"
)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db)
) -> IncidentResponse:
    """
    Get an incident by ID
    
    Args:
        incident_id: ID of the incident to retrieve
        db: Database session
        
    Returns:
        IncidentResponse with full incident details
        
    Raises:
        HTTPException(404): If incident not found
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found"
        )
    
    return IncidentResponse(
        id=incident.id,
        log_text=incident.log_text,
        summary=incident.summary,
        severity=SeverityEnum(incident.severity),
        root_cause=incident.root_cause,
        affected_components=json.loads(incident.evidence),
        recommended_actions=json.loads(incident.recommended_steps),
        confidence=incident.confidence,
        created_at=incident.created_at,
        similar_incidents=[]
    )


@app.get(
    "/health",
    summary="Health check",
    description="Check if the API is running"
)
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get(
    "/",
    summary="Root endpoint",
    description="API information"
)
def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Incident Investigator API",
        "version": "1.0.0",
        "description": "API for analyzing log text and generating structured incident reports"
    }