"""Tests for RAG pipeline."""

import pytest
from src.services.openai_service import generate_embedding, count_tokens

@pytest.mark.asyncio
async def test_generate_embedding():
    """Test embedding generation."""
    text = "What are the course prices?"
    embedding = generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)

def test_count_tokens():
    """Test token counting."""
    text = "This is a test sentence"
    tokens = count_tokens(text)

    assert isinstance(tokens, int)
    assert tokens > 0
