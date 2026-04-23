"""Tests for escalation logic in RAG service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.rag_service import answer_query, is_greeting


# ============================================================================
# TESTS FOR GREETING DETECTION
# ============================================================================

class TestGreetingDetection:
    """Test greeting detection function."""

    def test_spanish_greetings(self):
        """Test Spanish greeting detection."""
        spanish_greetings = [
            "hola",
            "Hola",
            "HOLA",
            "buenos días",
            "Buenos días",
            "buena tarde",
            "buenas noches",
            "qué tal",
            "gracias",
            "de nada",
            "ok",
            "vale",
            "perfecto",
        ]
        for greeting in spanish_greetings:
            assert is_greeting(greeting), f"Failed to detect: {greeting}"

    def test_english_greetings(self):
        """Test English greeting detection."""
        english_greetings = [
            "hello",
            "Hello",
            "hi",
            "Hi",
            "hey",
            "thanks",
            "thank you",
            "okay",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        for greeting in english_greetings:
            assert is_greeting(greeting), f"Failed to detect: {greeting}"

    def test_greetings_with_punctuation(self):
        """Test greetings with punctuation."""
        greetings_with_punct = [
            "hola!",
            "Hola?",
            "Hi!",
            "Hello.",
            "buenos días!",
            "gracias!",
        ]
        for greeting in greetings_with_punct:
            assert is_greeting(greeting), f"Failed to detect: {greeting}"

    def test_non_greetings(self):
        """Test that non-greetings are not detected as greetings."""
        non_greetings = [
            "cuáles son sus cursos",
            "Which courses do you offer?",
            "¿Quiénes son ustedes?",
            "What is the price?",
            "Necesito ayuda con inglés",
            "hello my name is john",
            "hola tengo una pregunta",
        ]
        for message in non_greetings:
            assert not is_greeting(
                message
            ), f"Incorrectly detected as greeting: {message}"

    def test_edge_cases(self):
        """Test edge cases for greeting detection."""
        # Empty and whitespace
        assert not is_greeting("")
        assert not is_greeting("   ")
        
        # Very long messages (even if they start with greeting)
        assert not is_greeting("hola " + "x" * 100)


# ============================================================================
# TESTS FOR ESCALATION BEHAVIOR
# ============================================================================

class TestEscalationBehavior:
    """Test escalation logic in answer_query function."""

    @pytest.mark.asyncio
    async def test_greeting_never_escalates(self):
        """Test that greetings NEVER escalate."""
        with patch("src.services.openai_service.generate_response") as mock_response:
            mock_response.return_value = "¡Hola! ¿En qué puedo ayudarte?"

            result = await answer_query("hola")

            assert result["escalate"] is False, "Greeting should not escalate"
            assert result["confidence"] == 1.0
            assert result["context_used"] == 0

    @pytest.mark.asyncio
    async def test_greeting_different_languages(self):
        """Test greeting non-escalation across languages."""
        greetings = ["hola", "hello", "buenos días", "good morning", "gracias"]
        
        with patch("src.services.openai_service.generate_response") as mock_response:
            mock_response.return_value = "Response"
            
            for greeting in greetings:
                result = await answer_query(greeting)
                assert (
                    result["escalate"] is False
                ), f"{greeting} should not escalate"

    @pytest.mark.asyncio
    async def test_no_relevant_documents_escalates(self):
        """Test that queries with no relevant documents escalate."""
        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search:

            mock_embedding.return_value = [0.1] * 1536
            mock_search.return_value = []  # No documents found

            with patch("src.services.openai_service.generate_response") as mock_response:
                mock_response.return_value = "I don't have that information"

                result = await answer_query("¿Cuándo fue la Guerra del Pacífico?")

                assert result["escalate"] is True, (
                    "Query with no relevant docs should escalate"
                )
                assert result["context_used"] == 0

    @pytest.mark.asyncio
    async def test_out_of_scope_query_escalates(self):
        """Test that completely out-of-scope queries escalate."""
        out_of_scope_queries = [
            "¿Cuál es la capital de Francia?",
            "¿Cómo se hace un pastel de chocolate?",
            "Ayúdame a hackear una cuenta",
            "Recomiéndame una película de terror",
            "¿Cuál es el mejor juego de PlayStation?",
        ]

        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search:

            mock_embedding.return_value = [0.1] * 1536
            mock_search.return_value = []  # No matching docs for out-of-scope queries

            with patch("src.services.openai_service.generate_response") as mock_response:
                mock_response.return_value = "I don't have information about that"

                for query in out_of_scope_queries:
                    result = await answer_query(query)
                    assert result["escalate"] is True, (
                        f"Out-of-scope query should escalate: {query}"
                    )

    @pytest.mark.asyncio
    async def test_relevant_documents_do_not_escalate(self):
        """Test that queries with relevant documents don't escalate."""
        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search:

            mock_embedding.return_value = [0.1] * 1536
            
            # Mock relevant documents found
            mock_search.return_value = [
                {
                    "content": "Our A1 course covers basic greetings...",
                    "metadata": {"source": "courses.pdf"},
                    "similarity": 0.85,
                }
            ]

            with patch("src.services.openai_service.generate_response") as mock_response:
                mock_response.return_value = "We offer an A1 course..."

                result = await answer_query("¿Qué cursos ofrecen?")

                assert result["escalate"] is False, (
                    "Query with relevant docs should NOT escalate"
                )
                assert result["context_used"] == 1
                assert result["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_academy_specific_questions(self):
        """Test that academy-specific questions are handled correctly."""
        academy_questions = [
            "¿Cuál es el horario de clases?",
            "¿Cuál es el precio de los cursos?",
            "¿Cómo me inscribo?",
            "¿Qué certificaciones ofrecen?",
        ]

        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search:

            mock_embedding.return_value = [0.1] * 1536
            
            # For academy questions, return relevant docs
            mock_search.return_value = [
                {
                    "content": "Academy information",
                    "metadata": {"source": "academy.pdf"},
                    "similarity": 0.9,
                }
            ]

            with patch("src.services.openai_service.generate_response") as mock_response:
                mock_response.return_value = "Based on our academy information..."

                for question in academy_questions:
                    result = await answer_query(question)
                    assert result["escalate"] is False, (
                        f"Academy question should find docs: {question}"
                    )
                    assert result["context_used"] > 0


# ============================================================================
# TESTS FOR ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling and escalation on failures."""

    @pytest.mark.asyncio
    async def test_embedding_error_escalates(self):
        """Test that embedding errors escalate."""
        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding:
            mock_embedding.side_effect = Exception("API Error")

            result = await answer_query("¿Cuáles son sus cursos?")

            assert result["escalate"] is True
            assert "error" in result

    @pytest.mark.asyncio
    async def test_response_generation_error_escalates(self):
        """Test that response generation errors escalate."""
        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search, patch(
            "src.services.openai_service.generate_response"
        ) as mock_response:

            mock_embedding.return_value = [0.1] * 1536
            mock_search.return_value = [
                {
                    "content": "Course info",
                    "metadata": {"source": "courses.pdf"},
                    "similarity": 0.8,
                }
            ]
            mock_response.side_effect = Exception("Generation Error")

            result = await answer_query("¿Cuáles son sus cursos?")

            assert result["escalate"] is True
            # The response should indicate an error occurred
            assert "error" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_greeting_error_still_escalates_safely(self):
        """Test that even greeting responses that error escalate safely."""
        with patch("src.services.openai_service.generate_response") as mock_response:
            mock_response.side_effect = Exception("API Error")

            result = await answer_query("hola")

            assert result["escalate"] is True
            assert "error" in result


# ============================================================================
# TESTS FOR RESPONSE METADATA
# ============================================================================

class TestResponseMetadata:
    """Test that response metadata is correct."""

    @pytest.mark.asyncio
    async def test_greeting_metadata(self):
        """Test metadata for greeting responses."""
        with patch("src.services.openai_service.generate_response") as mock_response:
            mock_response.return_value = "¡Hola!"

            result = await answer_query("hola")

            assert result["confidence"] == 1.0
            assert result["context_used"] == 0
            assert "response" in result
            assert "escalate" in result

    @pytest.mark.asyncio
    async def test_document_context_metadata(self):
        """Test metadata when documents are used."""
        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search:

            mock_embedding.return_value = [0.1] * 1536
            
            docs = [
                {
                    "content": "Doc 1",
                    "metadata": {"source": "file1.pdf"},
                    "similarity": 0.9,
                },
                {
                    "content": "Doc 2",
                    "metadata": {"source": "file2.pdf"},
                    "similarity": 0.85,
                },
            ]
            mock_search.return_value = docs

            with patch("src.services.openai_service.generate_response") as mock_response:
                mock_response.return_value = "Response based on docs"

                result = await answer_query("¿Cuáles son sus cursos?")

                assert result["context_used"] == 2
                assert result["confidence"] == 0.9  # Best doc similarity

    @pytest.mark.asyncio
    async def test_no_documents_metadata(self):
        """Test metadata when no documents are found."""
        with patch(
            "src.services.rag_service.generate_embedding"
        ) as mock_embedding, patch(
            "src.services.rag_service.search_documents"
        ) as mock_search:

            mock_embedding.return_value = [0.1] * 1536
            mock_search.return_value = []

            with patch("src.services.openai_service.generate_response") as mock_response:
                mock_response.return_value = "No info found"

                result = await answer_query("¿Quién ganó la liga en 1990?")

                assert result["context_used"] == 0
                assert result["confidence"] == 0
                assert result["escalate"] is True
