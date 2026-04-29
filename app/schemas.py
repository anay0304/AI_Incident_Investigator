from enum import Enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SeverityEnum(str, Enum):
    """Severity levels for incidents"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AnalyzeRequest(BaseModel):
    """Request model for analyzing log text"""
    log_text: str = Field(..., min_length=1, description="Raw log text to analyze")


class IncidentSummary(BaseModel):
    """Brief summary of a similar past incident"""
    id: int = Field(..., description="ID of the similar incident")
    summary: str = Field(..., description="Brief summary of the incident")
    severity: SeverityEnum = Field(..., description="Severity level of the incident")


class IncidentCreate(BaseModel):
    """Model for creating a new incident (LLM output fields)"""
    summary: str = Field(..., min_length=1, description="Brief summary of the incident")
    severity: SeverityEnum = Field(..., description="Severity level of the incident")
    root_cause: str = Field(..., min_length=1, description="Root cause of the incident")
    affected_components: list[str] = Field(..., description="List of affected components")
    recommended_actions: list[str] = Field(..., description="Recommended actions to resolve")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence in the analysis (0.0 to 1.0)")

    @field_validator("affected_components", "recommended_actions")
    @classmethod
    def validate_non_empty_list(cls, v):
        if not v:
            raise ValueError("List cannot be empty")
        return v


class IncidentResponse(BaseModel):
    """Full incident response model with all fields"""
    id: int = Field(..., description="Unique identifier of the incident")
    log_text: str = Field(..., description="Original log text that was analyzed")
    summary: str = Field(..., description="Brief summary of the incident")
    severity: SeverityEnum = Field(..., description="Severity level of the incident")
    root_cause: str = Field(..., description="Root cause of the incident")
    affected_components: list[str] = Field(..., description="List of affected components")
    recommended_actions: list[str] = Field(..., description="Recommended actions to resolve")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence in the analysis")
    created_at: datetime = Field(..., description="Timestamp when the incident was created")
    similar_incidents: list[IncidentSummary] = Field(
        default_factory=list,
        max_length=3,
        description="Up to 3 similar past incidents"
    )