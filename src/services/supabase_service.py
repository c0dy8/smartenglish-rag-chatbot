"""Supabase database interactions."""

from supabase import create_client
from src.config import Config

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)

async def search_documents(
    embedding: list[float],
    top_k: int = 5,
    threshold: float = 0.7
) -> list[dict]:
    """Search documents by vector similarity."""
    try:
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": embedding,
                "match_count": top_k,
                "similarity_threshold": threshold
            }
        ).execute()

        return response.data if response.data else []

    except Exception as e:
        print(f"Error searching documents: {e}")
        return []

async def get_document_count() -> int:
    """Get total number of documents in database."""
    try:
        response = supabase.table("documents").select(
            "id", count="exact"
        ).execute()

        return response.count

    except Exception as e:
        print(f"Error getting document count: {e}")
        return 0

async def insert_document(
    content: str,
    embedding: list[float],
    metadata: dict = None
) -> bool:
    """Insert single document with embedding."""
    try:
        supabase.table("documents").insert({
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {}
        }).execute()

        return True

    except Exception as e:
        print(f"Error inserting document: {e}")
        return False

async def get_all_documents() -> list[dict]:
    """Get all documents from database (for caching/backup)."""
    try:
        response = supabase.table("documents").select(
            "content, embedding, metadata"
        ).execute()

        return response.data if response.data else []

    except Exception as e:
        print(f"Error retrieving all documents: {e}")
        return []
