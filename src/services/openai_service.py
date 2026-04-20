"""OpenAI API interactions."""

from openai import OpenAI
from src.config import Config
from src.services.embedding_cache import get_cached_embedding, save_embedding_to_cache
from src.services.metrics_service import metrics

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text using OpenAI with local cache."""
    # Check cache first
    cached = get_cached_embedding(text)
    if cached:
        print(f"Using cached embedding (saved API cost)")
        metrics.record_cache_hit(text)
        return cached

    # Generate if not cached
    response = client.embeddings.create(
        model=Config.OPENAI_EMBEDDING_MODEL,
        input=text,
        dimensions=1536
    )
    embedding = response.data[0].embedding

    # Save to cache for future use
    save_embedding_to_cache(text, embedding)
    metrics.record_cache_miss(text)
    return embedding

async def generate_response(
    system_prompt: str,
    user_message: str,
    context: str = None
) -> str:
    """Generate response using OpenAI Responses API."""
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    if context:
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {user_message}"
        })
    else:
        messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=messages,
        temperature=Config.OPENAI_TEMPERATURE,
        max_tokens=500
    )

    output = response.choices[0].message.content
    full_input = "\n".join(m["content"] for m in messages)
    metrics.record_chat_cost(full_input, output)
    return output

def count_tokens(text: str) -> int:
    """Estimate token count (simplified)."""
    return len(text.split()) // 4
