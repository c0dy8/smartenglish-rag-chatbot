"""Tests for chat endpoint."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_request():
    """Test chat endpoint with valid request."""
    payload = {
        "message": "What are your schedule options?",
        "user_id": "test_user_1"
    }
    response = client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "escalate" in data
    assert "confidence" in data

def test_chat_empty_message():
    """Test chat with empty message."""
    payload = {"message": ""}
    response = client.post("/api/v1/chat", json=payload)

    assert response.status_code == 422  # Validation error

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
