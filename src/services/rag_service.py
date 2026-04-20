"""RAG (Retrieval Augmented Generation) service."""

from src.services.openai_service import generate_embedding
from src.services.supabase_service import search_documents
from src.config import Config

SYSTEM_PROMPT = """You are a helpful customer support assistant for SmartEnglish PRO,
a Colombian language academy. Your role is to answer questions about courses,
schedules, prices, levels, certifications, and enrollment processes.

IMPORTANT RULES:
1. Answer ONLY based on the provided context from our documents
2. If the question is outside the scope of our documents, politely inform the user
   and offer to escalate to a human agent
3. Maintain a professional, friendly, and respectful tone
4. Always provide accurate, specific information (schedules, prices, policies)
5. If uncertain, acknowledge the limitation and suggest human assistance

ESCALATION PHRASES:
- "I don't have information about that. Let me connect you with our team..."
- "That's outside my scope. I'll escalate this to our specialists..."

Example responses:
- Schedule inquiry: "Our courses run Monday to Friday with three time slots:
  6:00-8:00 AM, 12:00-2:00 PM, and 6:00-8:00 PM. Saturday intensive classes
  are from 8:00 AM to 12:00 PM."
- Level inquiry: "We offer levels A1, A2, B1, B2, and C1 following the CEFR framework..."
- Out of scope: "I specialize in course information. For technical support,
  I'll connect you with our team."
"""

async def answer_query(user_query: str) -> dict:
    """
    Process user query through RAG pipeline.
    Returns response and metadata.
    """
    # Generate embedding for user query
    try:
        query_embedding = generate_embedding(user_query)
    except Exception as e:
        return {
            "response": "Sorry, I encountered an error processing your query. Please try again.",
            "escalate": True,
            "error": str(e)
        }

    # Search relevant documents
    relevant_docs = await search_documents(
        embedding=query_embedding,
        top_k=Config.RAG_TOP_K,
        threshold=Config.RAG_SIMILARITY_THRESHOLD
    )

    # Build context from retrieved documents
    if not relevant_docs:
        context = "No relevant information found in knowledge base."
        should_escalate = True
    else:
        context = "\n\n".join([
            f"[{doc['metadata'].get('source', 'Unknown')}]\n{doc['content']}"
            for doc in relevant_docs
        ])
        should_escalate = False

    # Generate response using OpenAI
    try:
        from src.services.openai_service import generate_response

        response_text = await generate_response(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_query,
            context=context if not should_escalate else None
        )

    except Exception as e:
        response_text = "Sorry, I encountered an error generating a response."
        should_escalate = True

    return {
        "response": response_text,
        "escalate": should_escalate,
        "context_used": len(relevant_docs),
        "confidence": relevant_docs[0].get("similarity", 0) if relevant_docs else 0
    }
