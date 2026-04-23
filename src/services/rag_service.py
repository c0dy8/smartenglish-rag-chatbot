"""RAG (Retrieval Augmented Generation) service."""

from src.services.openai_service import generate_embedding
from src.services.supabase_service import search_documents
from src.config import Config

# List of greeting and courtesy messages that don't need context search
GREETINGS = {
    # Spanish
    "hola", "holas", "buenos días", "buen día", "buenos tardes", "buena tarde",
    "buenas noches", "buena noche", "buenos días", "qué tal", "qué onda", "hey",
    "hi", "hello", "gracias", "muchas gracias", "de nada", "ok", "vale",
    "claro", "seguro", "entendido", "perfecto", "genial",
    # English
    "hello", "hi", "hey", "thanks", "thank you", "okay", "ok", "sure", "great",
    "perfect", "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how are you?", "what's up", "howdy"
}

def is_greeting(message: str) -> bool:
    """
    Check if the message is only a greeting or courtesy phrase.
    Returns True if the message should be treated as a greeting.
    """
    # Normalize the message: lowercase and strip
    normalized = message.strip().lower()
    
    # Check if the entire message (or very short variations) is a greeting
    if normalized in GREETINGS:
        return True
    
    # Check for common greeting patterns with minimal extra text
    if len(normalized) < 30:  # Very short messages are likely greetings
        # Remove common punctuation
        cleaned = normalized.replace("?", "").replace("!", "").replace(".", "").strip()
        if cleaned in GREETINGS:
            return True
    
    return False

SYSTEM_PROMPT = """You are a helpful customer support assistant for SmartEnglish PRO,
a Colombian language academy. Your role is to answer questions about courses,
schedules, prices, levels, certifications, and enrollment processes.

LANGUAGE:
- Always reply in the same language as the user (Spanish or English).
- Default to Spanish if the user writes in Spanish.

CORE BEHAVIOR:
- Be friendly, clear, and helpful.
- Keep responses concise but informative.
- Never sound robotic or overly formal.

IMPORTANT RULES:
1. Answer ONLY based on the provided context from our documents.
2. If the question is outside the scope of our documents, politely inform the user
   and offer to escalate to a human agent.
3. Always provide accurate, specific information (schedules, prices, policies).
4. If uncertain, acknowledge the limitation and suggest human assistance.
5. NEVER hallucinate or invent information.

GREETING HANDLING (VERY IMPORTANT):
6. If the user message is ONLY a greeting or courtesy message 
   (e.g. "hola", "buenos días", "hello", "gracias", "ok"):
   - Respond with a warm greeting.
   - Ask how you can help.
   - DO NOT say you lack information.
   - DO NOT escalate.
   - SET "escalate" to false.

   Example:
   User: "hola"
   Response: "¡Hola! 😊 Bienvenido a SmartEnglish PRO. ¿En qué puedo ayudarte hoy?"

ESCALATION LOGIC:
7. Only escalate when:
   - The user asks something clearly outside academy topics
   - The answer is not in the provided context
   - The user explicitly asks for a human

8. When escalating:
   - Be polite and transparent
   - Do NOT overuse escalation

ESCALATION PHRASES:
- "No tengo esa información en este momento. Déjame conectarte con nuestro equipo..."
- "Esa consulta está fuera de mi alcance. Te voy a escalar con un asesor humano..."

EXAMPLES:

- Greeting:
  "¡Hola! 😊 ¿En qué puedo ayudarte hoy?"

- Schedule inquiry:
  "Nuestros cursos se dictan de lunes a viernes en tres horarios:
   6:00-8:00 AM, 12:00-2:00 PM, y 6:00-8:00 PM. 
   También tenemos clases intensivas los sábados de 8:00 AM a 12:00 PM."

- Level inquiry:
  "Ofrecemos niveles A1, A2, B1, B2 y C1 siguiendo el marco CEFR..."

- Out of scope:
  "No tengo esa información en este momento. Déjame conectarte con nuestro equipo..."


"""

async def answer_query(user_query: str) -> dict:
    """
    Process user query through RAG pipeline.
    Returns response and metadata.
    """
    # Check if this is just a greeting - if so, don't escalate
    if is_greeting(user_query):
        try:
            from src.services.openai_service import generate_response
            
            response_text = await generate_response(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_query,
                context=None  # No context needed for greetings
            )
            
            return {
                "response": response_text,
                "escalate": False,  # Never escalate greetings
                "context_used": 0,
                "confidence": 1.0  # Greeting confidence is always high
            }
        except Exception as e:
            response_text = "Sorry, I encountered an error generating a response."
            return {
                "response": response_text,
                "escalate": True,
                "error": str(e),
                "context_used": 0,
                "confidence": 0
            }

    # For non-greeting queries, proceed with RAG pipeline
    # Generate embedding for user query
    try:
        query_embedding = generate_embedding(user_query)
    except Exception as e:
        return {
            "response": "Sorry, I encountered an error processing your query. Please try again.",
            "escalate": True,
            "error": str(e),
            "context_used": 0,
            "confidence": 0
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
