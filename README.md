# SmartEnglish RAG ChatBot

**Intelligent AI-powered customer support assistant for SmartEnglish PRO academy** combining Retrieval Augmented Generation (RAG), OpenAI LLMs, and real-time analytics.

A production-ready FastAPI backend that answers student inquiries about courses, schedules, pricing, and certifications using semantic search over a knowledge base. Includes automated Telegram integration via n8n, intelligent escalation routing, real-time metrics dashboard, and comprehensive cost tracking.

---

## 🎯 Features

- **🤖 AI-Powered Responses** — OpenAI GPT-4o-mini with context-aware prompts
- **📚 RAG System** — Semantic vector search with fine-tuned similarity thresholds for Spanish queries
- **📊 Real-Time Dashboard** — Interactive charts, metrics history, topic mapping, escalation alerts via WebSocket
- **🔄 n8n Integration** — Telegram automation with intelligent escalation workflows
- **💾 Vector Database** — Supabase pgvector for persistent embeddings
- **💰 Cost Tracking** — Token-based pricing calculation with cache savings analytics
- **⚡ Async Backend** — FastAPI with WebSocket support for real-time updates
- **🛡️ Production Ready** — Error handling, health checks, environment validation

---

## 📋 How It Works

### RAG Pipeline

1. **Document Ingestion** — PDFs are processed and split into 500-character chunks with 100-character overlap
2. **Embedding Generation** — Text chunks converted to vectors using OpenAI's `text-embedding-3-small` model
3. **Vector Storage** — Embeddings stored in Supabase with cosine similarity indexing
4. **Query Processing** — User messages embedded and compared against knowledge base (similarity threshold: 0.45)
5. **Response Generation** — Top-K relevant documents (K=5) passed to GPT-4o-mini with system prompt
6. **Intelligent Escalation** — If confidence < threshold or no relevant documents found, escalate to human team

### Metrics & Analytics

- **Real-Time Tracking** — Every query logged with response time, confidence, document count
- **Cost Calculation** — Token estimates multiplied by OpenAI pricing (embeddings: $0.02/1K, chat input: $0.15/1K, chat output: $0.60/1K)
- **Cache Statistics** — Embedding cache hits/misses monitored for optimization
- **Topic Analysis** — Query keywords extracted and ranked by frequency
- **Escalation Monitoring** — Alerts for low-confidence responses requiring human intervention

---

## 🏗️ Architecture

```
User (Telegram / HTTP)
    ↓
n8n Workflow (Cloud)
    ↓
FastAPI Backend (Python)
    ├── Chat Route (/api/v1/chat)
    ├── Metrics Routes (/api/v1/metrics, /api/v1/ws/metrics)
    └── Health Check (/api/v1/health)
    ↓
RAG Service
    ├── Embedding Cache (JSON)
    ├── OpenAI API (embeddings + chat)
    └── Supabase (vector DB)
    ↓
Response + Metrics Broadcast (WebSocket)
    ↓
Dashboard (Vanilla JS + Chart.js + TailwindCSS)
```

### File Structure

```
.
├── src/
│   ├── main.py                          # FastAPI app & WebSocket setup
│   ├── config.py                        # Environment variables & RAG settings
│   ├── routes/
│   │   ├── chat.py                      # /api/v1/chat endpoint
│   │   └── metrics.py                   # /api/v1/metrics & WebSocket
│   ├── services/
│   │   ├── rag_service.py               # RAG pipeline (semantic search)
│   │   ├── openai_service.py            # OpenAI API client
│   │   ├── supabase_service.py          # Database operations
│   │   ├── metrics_service.py           # Query logging & analytics
│   │   ├── websocket_manager.py         # WebSocket broadcast manager
│   │   └── embedding_cache.py           # In-memory embedding cache
│   ├── schemas/
│   │   └── models.py                    # Pydantic request/response models
│   └── static/
│       └── dashboard.html               # Real-time analytics dashboard
├── scripts/
│   ├── load_documents.py                # Ingest PDFs to Supabase
│   └── export_embeddings_cache.py       # Backup embeddings cache
├── workflows/
│   └── n8n.json                         # Telegram bot automation
├── data/
│   ├── documents/                       # PDF knowledge base (Horarios, Precios, Niveles)
│   ├── embeddings/embeddings_cache.json # Cached embeddings
│   └── metrics/metrics.json             # Persistent metrics data
├── tests/                               # Unit tests
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment template
└── README.md                            # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key
- Supabase project with pgvector extension
- (Optional) Telegram bot token for n8n integration

### 1. Clone & Install

```bash
git clone <repo-url>
cd prueba\ desempeno\ IA
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
TELEGRAM_BOT_TOKEN=... (optional, for n8n)
TELEGRAM_CHAT_ID=... (optional, for escalations)
BACKEND_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Load Knowledge Base

Place PDF files in `data/documents/` then:

```bash
python scripts/load_documents.py
```

This extracts text, generates embeddings, and inserts into Supabase. Monitor progress in logs.

### 4. Start Backend

```bash
python src/main.py
```

Server runs on `http://127.0.0.1:8000`

### 5. Access Dashboard & Docs

- **API Docs:** http://127.0.0.1:8000/docs
- **Dashboard:** http://127.0.0.1:8000/dashboard (real-time metrics)
- **Health Check:** http://127.0.0.1:8000/api/v1/health

---

## 📡 API Reference

### POST `/api/v1/chat`

**Send a query and receive AI response with RAG context.**

**Request:**
```json
{
  "message": "¿Cuáles son los horarios disponibles?"
}
```

**Response:**
```json
{
  "response": "Nuestros cursos están disponibles de lunes a viernes en tres franjas horarias: Mañana (6-8 AM), Mediodía (12-2 PM), Noche (6-8 PM)...",
  "escalate": false,
  "confidence": 0.588,
  "context_used": 3
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI-generated answer |
| `escalate` | boolean | Whether to escalate to human (low confidence/no docs) |
| `confidence` | float | 0-1 similarity score of top match |
| `context_used` | integer | Number of documents used for context |

### GET `/api/v1/health`

**Health check & system status.**

**Response:**
```json
{
  "status": "healthy",
  "documents_loaded": 9,
  "cache": {
    "total_cached": 18,
    "cache_size_mb": 0.43
  }
}
```

### GET `/api/v1/metrics`

**Full metrics snapshot (queries, costs, escalations, topics, history).**

```json
{
  "total_queries": 145,
  "total_escalations": 12,
  "escalation_rate": "8.3%",
  "avg_response_time_ms": 342,
  "avg_confidence": 0.72,
  "cache_hits": 34,
  "cache_misses": 111,
  "cost_saved_usd": 0.002345,
  "top_topics": [["horarios", 28], ["precios", 15], ["niveles", 12]],
  "history": [...],
  "recent_queries": [...],
  "escalation_alerts": [...]
}
```

### WS `/api/v1/ws/metrics`

**WebSocket for real-time metrics updates every 2 seconds + on each new query.**

```json
{
  "type": "metrics",
  "data": { /* same as GET /api/v1/metrics */ }
}
```

---

## 🤝 n8n Integration

The `workflows/n8n.json` file contains a Telegram bot automation:

**Flow:**
1. **Telegram Trigger** — Listens for messages
2. **HTTP Request** — Calls `POST /api/v1/chat` with message
3. **Check Escalation** — Routes based on `escalate` flag
4. **Response/Escalation** — Sends answer or notifies support team

**To import into n8n:**
1. Open n8n dashboard
2. **Menu → Import from clipboard**
3. Paste contents of `workflows/n8n.json`
4. Configure Telegram credentials
5. Set server URL (e.g., `http://your-server:8000` or ngrok tunnel for cloud n8n)

---

## ⚙️ Configuration

### RAG Parameters (src/config.py)

```python
RAG_SIMILARITY_THRESHOLD = 0.45  # Similarity cutoff (0-1)
RAG_TOP_K = 5                    # Documents to retrieve
RAG_CHUNK_SIZE = 500             # Characters per chunk
RAG_CHUNK_OVERLAP = 100          # Overlap between chunks
```

**Note:** Threshold of 0.45 is calibrated for Spanish queries with `text-embedding-3-small` model. Adjust based on your use case.

### Pricing (OpenAI)

Hardcoded in `metrics_service.py`:
- Embeddings: $0.00002 per 1K tokens
- Chat Input: $0.00015 per 1K tokens
- Chat Output: $0.00060 per 1K tokens

Update these if using different OpenAI models.

---

## 🧪 Testing

```bash
pytest tests/ -v
```

Tests cover:
- RAG pipeline (embedding cache, similarity search)
- Chat endpoint (request/response format)
- Health check & metrics routes

---

## 📦 Deployment

### Option 1: Railway (Recommended)

```bash
# 1. Create Railway project
# 2. Connect your GitHub repo
# 3. Set environment variables in Railway dashboard
# 4. Deploy automatically on push
```

**Environment Variables to set:**
- `OPENAI_API_KEY`
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `ENVIRONMENT=production`

### Option 2: Render

```bash
# 1. Push repo to GitHub
# 2. Connect Render to repo
# 3. Create Web Service
# 4. Set env vars and deploy
```

### Option 3: Docker

```bash
docker build -t smartenglish-rag .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e SUPABASE_URL=... \
  smartenglish-rag
```

### Exposing Local Server to Cloud n8n

Use **ngrok** for tunneling:

```bash
ngrok http 8000
# Gives you: https://xxxxx.ngrok.io
# Use in n8n: https://xxxxx.ngrok.io/api/v1/chat
```

---

## 📊 Dashboard Features

- **KPI Cards** — Total queries, escalation rate, avg response time, cost savings
- **Historical Charts** — Query volume & latency trends (24-hour rolling window)
- **Pie Chart** — Answered vs. escalated ratio
- **Cache Analytics** — Hits vs. misses bar chart
- **Topic Cloud** — Word cloud of most-asked topics
- **Escalation Alerts** — Real-time notification list
- **Recent Queries Table** — Last 20 queries with metadata

All updates via WebSocket with auto-reconnect.

---

## 🔍 Troubleshooting

**Q: Bot always escalates (no documents found)**
- ✅ Lower `RAG_SIMILARITY_THRESHOLD` in config.py
- ✅ Ensure PDFs are in `data/documents/` and loaded with `load_documents.py`
- ✅ Check Supabase connection and table contents

**Q: Slow responses**
- ✅ Enable embedding cache (auto-enabled)
- ✅ Increase `RAG_TOP_K` to retrieve more docs (default: 5)
- ✅ Monitor OpenAI API rate limits

**Q: n8n can't reach server**
- ✅ If n8n is in cloud, use ngrok or deploy FastAPI to cloud
- ✅ If local, use `http://127.0.0.1:8000` (on same machine only)
- ✅ Check firewall & port 8000 is open

**Q: Dashboard not updating**
- ✅ Verify WebSocket running: check `/api/v1/ws/metrics` in browser dev tools
- ✅ Ensure metrics service initialized (check logs on startup)
- ✅ Check CORS is enabled in main.py

---

## 📝 License

Internal use only. Proprietary to SmartEnglish PRO.

---

## 👤 Support

For issues or questions, contact the development team.

**Last Updated:** April 2026  
**Version:** 1.1.0
