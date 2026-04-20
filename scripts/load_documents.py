#!/usr/bin/env python3
"""
Load documents from PDFs, chunk them, generate embeddings, and insert into Supabase.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI
from supabase import create_client
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

PDF_DIR = Path(__file__).parent.parent / "data" / "documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def extract_text_from_pdfs():
    """Extract text from all PDFs in data/documents/."""
    documents = []
    pdf_files = list(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in the project directory.")
        return []

    print(f"Found {len(pdf_files)} PDF(s): {[f.name for f in pdf_files]}")

    for pdf_path in pdf_files:
        print(f"\nReading {pdf_path.name}...")
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page_num, page in enumerate(reader.pages):
                text += page.extract_text()

            documents.append({
                "filename": pdf_path.name,
                "text": text
            })
            print(f"Extracted {len(text)} characters from {pdf_path.name}")
        except Exception as e:
            print(f"Error reading {pdf_path.name}: {e}")

    return documents

def chunk_documents(documents):
    """Split documents into chunks with overlap."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = []
    for doc in documents:
        print(f"\nChunking {doc['filename']}...")
        doc_chunks = splitter.split_text(doc["text"])

        for i, chunk in enumerate(doc_chunks):
            chunks.append({
                "content": chunk,
                "metadata": {
                    "source": doc["filename"],
                    "chunk_index": i,
                    "total_chunks": len(doc_chunks)
                }
            })

        print(f"Created {len(doc_chunks)} chunks")

    return chunks

def generate_embeddings(chunks):
    """Generate embeddings using OpenAI API."""
    print(f"\nGenerating embeddings for {len(chunks)} chunks...")

    embeddings_data = []
    for i, chunk in enumerate(chunks):
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk["content"],
                dimensions=1536
            )

            embedding = response.data[0].embedding
            embeddings_data.append({
                "content": chunk["content"],
                "embedding": embedding,
                "metadata": chunk["metadata"]
            })

            if (i + 1) % 10 == 0:
                print(f"Generated {i + 1}/{len(chunks)} embeddings")

        except Exception as e:
            print(f"Error generating embedding for chunk {i}: {e}")

    print(f"Total embeddings generated: {len(embeddings_data)}")
    return embeddings_data

def insert_into_supabase(embeddings_data):
    """Insert embeddings into Supabase documents table."""
    print(f"\nInserting {len(embeddings_data)} documents into Supabase...")

    try:
        for i, data in enumerate(embeddings_data):
            response = supabase_client.table("documents").insert({
                "content": data["content"],
                "embedding": data["embedding"],
                "metadata": data["metadata"]
            }).execute()

            if (i + 1) % 10 == 0:
                print(f"Inserted {i + 1}/{len(embeddings_data)} documents")

        print(f"All documents inserted successfully!")
        return True

    except Exception as e:
        print(f"Error inserting into Supabase: {e}")
        return False

def main():
    """Main pipeline: extract → chunk → embed → insert."""
    print("=" * 60)
    print("Starting RAG Document Loading Pipeline")
    print("=" * 60)

    documents = extract_text_from_pdfs()
    if not documents:
        return

    chunks = chunk_documents(documents)
    if not chunks:
        print("No chunks created.")
        return

    embeddings_data = generate_embeddings(chunks)
    if not embeddings_data:
        print("No embeddings generated.")
        return

    success = insert_into_supabase(embeddings_data)

    print("\n" + "=" * 60)
    if success:
        print(f"Pipeline completed! Loaded {len(embeddings_data)} documents.")
    else:
        print("Pipeline failed during insertion.")
    print("=" * 60)

if __name__ == "__main__":
    main()
