"""LLM client abstraction and implementations"""
import os
from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def analyze(self, log_text: str) -> dict[str, Any]:
        """
        Analyze log text and return structured incident data
        
        Args:
            log_text: Raw log text to analyze
            
        Returns:
            Dictionary with incident fields: summary, severity, root_cause, 
            affected_components, recommended_actions, confidence
        """
        pass


class MockClient(LLMClient):
    """Mock LLM client that returns hardcoded realistic incidents"""

    def analyze(self, log_text: str) -> dict[str, Any]:
        """
        Return a realistic hardcoded incident based on log content
        
        Args:
            log_text: Raw log text (not used, returns database timeout scenario)
            
        Returns:
            Hardcoded incident dict for database connection timeout
        """
        # Hardcoded realistic incident for database connection timeout scenario
        return {
            "summary": "Database connection timeout after multiple retry attempts",
            "severity": "high",
            "root_cause": "PostgreSQL connection pool exhausted due to unclosed connections in the payment service. The service was holding connections longer than expected due to a long-running transaction that was not properly committed or rolled back.",
            "affected_components": [
                "payment-service",
                "postgresql-primary",
                "connection-pool",
                "payment-api-endpoint"
            ],
            "recommended_actions": [
                "Immediately restart the payment-service to release held connections",
                "Increase PostgreSQL max_connections from 100 to 200 temporarily",
                "Add connection timeout of 30 seconds to prevent long-running queries",
                "Implement proper connection pooling with proper cleanup in finally blocks",
                "Add monitoring alerts for connection pool utilization above 80%"
            ],
            "confidence": 0.92
        }


def get_llm_client() -> LLMClient:
    """
    Factory function to get the appropriate LLM client based on LLM_MODE
    
    Returns:
        LLMClient instance based on LLM_MODE environment variable
        
    Raises:
        ValueError: If LLM_MODE is set to an unsupported value
    """
    llm_mode = os.getenv("LLM_MODE", "mock").lower()
    
    if llm_mode == "mock":
        return MockClient()
    elif llm_mode == "bedrock":
        # Import here to avoid requiring boto3 when using mock
        from app.services.bedrock_client import BedrockClient
        return BedrockClient()
    else:
        raise ValueError(
            f"Unsupported LLM_MODE: {llm_mode}. "
            "Supported modes: 'mock', 'bedrock'"
        )