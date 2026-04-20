#!/usr/bin/env python3
"""Export embeddings from Supabase to local cache for backup and offline use."""

import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import os

load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.embedding_cache import save_embedding_to_cache, get_cache_stats

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def export_embeddings_to_cache():
    """Export all embeddings from Supabase to local cache."""
    print("=" * 60)
    print("📥 Exporting embeddings from Supabase to local cache...")
    print("=" * 60)

    try:
        # Get all documents from Supabase
        response = supabase.table("documents").select(
            "content, embedding, metadata"
        ).execute()

        documents = response.data if response.data else []

        if not documents:
            print("❌ No documents found in Supabase.")
            return

        print(f"📄 Found {len(documents)} documents in Supabase")

        # Save each embedding to cache
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            embedding = doc.get("embedding", [])

            if content and embedding:
                save_embedding_to_cache(content, embedding)

                if (i + 1) % 5 == 0:
                    print(f"   ✅ Cached {i + 1}/{len(documents)} embeddings")

        # Show final stats
        stats = get_cache_stats()
        print("\n" + "=" * 60)
        print(f"✅ Export complete!")
        print(f"   📦 Total cached embeddings: {stats['total_cached']}")
        print(f"   💾 Cache size: {stats['cache_size_mb']} MB")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error exporting embeddings: {e}")

if __name__ == "__main__":
    export_embeddings_to_cache()
