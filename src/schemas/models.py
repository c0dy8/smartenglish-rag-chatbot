"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=2000, description="User query")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Assistant response")
    escalate: bool = Field(default=False, description="Whether to escalate to human")
    confidence: float = Field(default=0.0, description="Confidence score (0-1)")
    context_used: int = Field(default=0, description="Number of documents used")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    documents_loaded: int = Field(default=0, description="Total documents in database")
    environment: str = Field(..., description="Current environment")

class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_queries: int = Field(default=0, description="Total queries processed")
    escalation_rate: float = Field(default=0.0, description="Percentage escalated")
    avg_confidence: float = Field(default=0.0, description="Average confidence")
    total_cost_usd: float = Field(default=0.0, description="Total API cost in USD")
