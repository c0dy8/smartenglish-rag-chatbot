# Architecture

## System Overview

```
User Input
    ↓
[n8n Workflow] → Telegram/Webhook
    ↓
[FastAPI Backend] ← HTTP Request
    ↓
┌───────────────────┴───────────────────┐
│                                       │
[RAG Pipeline]                    [OpenAI API]
    ↓                                  ↓
[Query Embedding]              [Response Generation]
    ↓
[Supabase Vector DB]
    ↓
[Similarity Search]
    ↓
[Retrieved Context]
    ↓
Back to OpenAI → Response → Backend → n8n → User
```

## Components

### 1. Knowledge Base (Supabase)

- **Table**: `documents`
- **Columns**:
  - `id` (UUID): Unique document chunk ID
  - `content` (TEXT): Chunk text
  - `embedding` (VECTOR 1536): OpenAI embeddings
  - `metadata` (JSONB): Source, chunk index, etc.

- **Function**: `match_documents(query_embedding, match_count, similarity_threshold)`
  - Returns top K most similar documents
  - Uses HNSW index for fast retrieval

### 2. Backend (FastAPI)

- **Config** (`src/config.py`): Centralized env variables
- **Services**:
  - `openai_service.py`: Embeddings + response generation
  - `supabase_service.py`: Database queries
  - `rag_service.py`: RAG pipeline orchestration
- **Routes** (`src/routes/chat.py`): REST API endpoints
- **Schemas** (`src/schemas/models.py`): Request/response validation

### 3. RAG Pipeline

**Flow:**
1. User sends query → `POST /api/v1/chat`
2. Generate embedding for query (OpenAI)
3. Search Supabase for similar documents
4. Build context from top-k matches
5. Send to OpenAI with system prompt + context
6. Return response + metadata (escalation, confidence, etc.)

**Prompt Engineering:**
- System prompt defines role, constraints, escalation rules
- Few-shot examples for consistent behavior
- Temperature = 0.2 (low randomness, factual answers)

### 4. n8n Automation

**Workflow steps:**
1. **Trigger**: Telegram bot receives message or webhook HTTP
2. **Extract**: Get message text and user ID
3. **Call Backend**: HTTP POST to `/api/v1/chat`
4. **Check Response**: 
   - If `escalate: true` → Notify human team
   - Otherwise → Send response to user
5. **Log**: Store metrics (cost, confidence, tokens)

### 5. Data Loading Pipeline

`scripts/load_documents.py`:
1. Read PDFs from `data/documents/`
2. Extract text (pypdf)
3. Chunk with overlap (LangChain RecursiveCharacterTextSplitter)
4. Generate embeddings (OpenAI text-embedding-3-small, 1536 dims)
5. Insert into Supabase with metadata

**Parameters:**
- Chunk size: 500 characters
- Overlap: 100 characters
- Embedding model: `text-embedding-3-small`

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Supabase + pgvector |
| Automation | n8n |
| Chat Platform | Telegram |
| Language | Python 3.10+ |

## Data Flow

### Query Processing
```
User Query
    ↓
[Embedding Generation] (OpenAI)
    ↓
[Vector Search] (Supabase)
    ↓
[Context Building] (Top-K documents)
    ↓
[Response Generation] (OpenAI + Context)
    ↓
[Response with Metadata]
    ↓
[n8n Routes to User]
```

### Document Loading
```
PDF Files
    ↓
[Text Extraction] (pypdf)
    ↓
[Chunking] (LangChain)
    ↓
[Embedding] (OpenAI)
    ↓
[Supabase Insert]
```

## Cost Optimization

1. **Embedding Reuse**: Documents embedded once, queries cheap
2. **Response Caching**: Frequent queries cached (planned)
3. **Model Selection**: Using GPT-4o-mini for cost efficiency
4. **Batch Embeddings**: Load documents in batches
5. **Metrics Tracking**: Monitor cost per query

## Scalability

- **Async Processing**: FastAPI async endpoints
- **Vector Index**: HNSW for O(log n) search
- **Connection Pooling**: Supabase + OpenAI
- **Horizontal Scale**: Stateless backend, deployable on any platform

## Security

- API keys in `.env` (never hardcoded)
- CORS configured for webhook access
- Service role key only for data loading (not exposed in client)
- Anon key for runtime queries (limited permissions)
