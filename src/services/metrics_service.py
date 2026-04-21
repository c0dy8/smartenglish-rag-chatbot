"""Real-time metrics tracking service for RAG dashboard."""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque, Counter
from threading import Lock

METRICS_DIR = Path(__file__).parent.parent.parent / "data" / "metrics"
METRICS_FILE = METRICS_DIR / "metrics.json"

# Pricing (USD per 1K tokens, OpenAI reference rates)
EMBEDDING_COST_PER_1K = 0.00002   # text-embedding-3-small
CHAT_INPUT_COST_PER_1K = 0.00015  # gpt-4o-mini input
CHAT_OUTPUT_COST_PER_1K = 0.00060 # gpt-4o-mini output




class MetricsTracker:
    """In-memory metrics tracker with JSON persistence."""

    def __init__(self):
        self._lock = Lock()
        self.total_queries = 0
        self.total_escalations = 0
        self.total_cache_hits = 0
        self.total_cache_misses = 0
        self.total_response_time_ms = 0.0
        self.confidence_sum = 0.0
        self.context_docs_sum = 0
        self.total_cost_usd = 0.0
        self.cost_saved_usd = 0.0
        self.recent_queries = deque(maxlen=20)
        self.topic_counter = Counter()
        self.history = deque(maxlen=288)  # 24h @ 5min intervals
        self.escalation_alerts = deque(maxlen=10)
        self.started_at = datetime.now().isoformat()
        self._load()

    def _load(self):
        """Load persisted metrics if available."""
        if not METRICS_FILE.exists():
            return
        try:
            with open(METRICS_FILE, "r") as f:
                data = json.load(f)
            self.total_queries = data.get("total_queries", 0)
            self.total_escalations = data.get("total_escalations", 0)
            self.total_cache_hits = data.get("total_cache_hits", 0)
            self.total_cache_misses = data.get("total_cache_misses", 0)
            self.total_response_time_ms = data.get("total_response_time_ms", 0.0)
            self.confidence_sum = data.get("confidence_sum", 0.0)
            self.context_docs_sum = data.get("context_docs_sum", 0)
            self.total_cost_usd = data.get("total_cost_usd", 0.0)
            self.cost_saved_usd = data.get("cost_saved_usd", 0.0)
            self.recent_queries = deque(data.get("recent_queries", []), maxlen=20)
            self.topic_counter = Counter(data.get("topic_counter", {}))
            self.history = deque(data.get("history", []), maxlen=288)
            self.escalation_alerts = deque(data.get("escalation_alerts", []), maxlen=10)
            self.started_at = data.get("started_at", self.started_at)
        except Exception as e:
            print(f"Warning: could not load metrics: {e}")

    def _persist(self):
        """Persist metrics to disk."""
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            payload = {
                "total_queries": self.total_queries,
                "total_escalations": self.total_escalations,
                "total_cache_hits": self.total_cache_hits,
                "total_cache_misses": self.total_cache_misses,
                "total_response_time_ms": self.total_response_time_ms,
                "confidence_sum": self.confidence_sum,
                "context_docs_sum": self.context_docs_sum,
                "total_cost_usd": self.total_cost_usd,
                "cost_saved_usd": self.cost_saved_usd,
                "recent_queries": list(self.recent_queries),
                "topic_counter": dict(self.topic_counter),
                "history": list(self.history),
                "escalation_alerts": list(self.escalation_alerts),
                "started_at": self.started_at,
            }
            with open(METRICS_FILE, "w") as f:
                json.dump(payload, f)
        except Exception as e:
            print(f"Warning: could not persist metrics: {e}")

    def record_cache_hit(self, text: str):
        """Record an embedding cache hit (saved API call)."""
        with self._lock:
            self.total_cache_hits += 1
            tokens = max(1, len(text.split()))
            self.cost_saved_usd += (tokens / 1000) * EMBEDDING_COST_PER_1K
            self._persist()

    def record_cache_miss(self, text: str):
        """Record an embedding cache miss (API call made)."""
        with self._lock:
            self.total_cache_misses += 1
            tokens = max(1, len(text.split()))
            self.total_cost_usd += (tokens / 1000) * EMBEDDING_COST_PER_1K
            self._persist()

    def record_chat_cost(self, input_text: str, output_text: str):
        """Estimate and record cost of a chat completion."""
        in_tokens = max(1, len(input_text.split()))
        out_tokens = max(1, len(output_text.split()))
        cost = (in_tokens / 1000) * CHAT_INPUT_COST_PER_1K
        cost += (out_tokens / 1000) * CHAT_OUTPUT_COST_PER_1K
        with self._lock:
            self.total_cost_usd += cost

    def record_query(
        self,
        query: str,
        response: str,
        escalated: bool,
        confidence: float,
        context_docs: int,
        response_time_ms: float,
    ):
        """Record a completed query and its outcome."""
        with self._lock:
            self.total_queries += 1
            if escalated:
                self.total_escalations += 1
                self.escalation_alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": query[:200],
                    "confidence": round(confidence, 3),
                })
            self.total_response_time_ms += response_time_ms
            self.confidence_sum += confidence
            self.context_docs_sum += context_docs

            for word in self._extract_keywords(query):
                self.topic_counter[word] += 1

            self.recent_queries.appendleft({
                "timestamp": datetime.now().isoformat(),
                "query": query[:200],
                "response": response[:200],
                "escalated": escalated,
                "confidence": round(confidence, 3),
                "context_docs": context_docs,
                "response_time_ms": round(response_time_ms, 1),
            })

            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "total_queries": self.total_queries,
                "escalation_rate": self._escalation_rate(),
                "avg_response_time_ms": self._avg_response_time(),
                "avg_confidence": self._avg_confidence(),
                "cost_saved_usd": round(self.cost_saved_usd, 6),
            })
            self._persist()

    def _extract_keywords(self, text: str) -> list:
        words = re.findall(r"\b[a-záéíóúñü]{4,}\b", text.lower())
        return [w for w in words if w not in STOPWORDS]

    def _escalation_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return round(self.total_escalations / self.total_queries * 100, 2)

    def _avg_response_time(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return round(self.total_response_time_ms / self.total_queries, 1)

    def _avg_confidence(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return round(self.confidence_sum / self.total_queries, 3)

    def _cache_hit_rate(self) -> float:
        total = self.total_cache_hits + self.total_cache_misses
        if total == 0:
            return 0.0
        return round(self.total_cache_hits / total * 100, 2)

    def _queries_per_minute(self) -> float:
        """Queries in the last minute based on recent_queries."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        count = 0
        for q in self.recent_queries:
            try:
                ts = datetime.fromisoformat(q["timestamp"])
                if ts >= cutoff:
                    count += 1
            except Exception:
                continue
        return count

    def snapshot(self) -> dict:
        """Return a complete snapshot of all metrics."""
        with self._lock:
            return {
                "total_queries": self.total_queries,
                "total_escalations": self.total_escalations,
                "escalation_rate": self._escalation_rate(),
                "avg_response_time_ms": self._avg_response_time(),
                "avg_confidence": self._avg_confidence(),
                "avg_context_docs": round(
                    self.context_docs_sum / self.total_queries, 2
                ) if self.total_queries else 0.0,
                "cache_hits": self.total_cache_hits,
                "cache_misses": self.total_cache_misses,
                "cache_hit_rate": self._cache_hit_rate(),
                "total_cost_usd": round(self.total_cost_usd, 6),
                "cost_saved_usd": round(self.cost_saved_usd, 6),
                "queries_per_minute": self._queries_per_minute(),
                "recent_queries": list(self.recent_queries),
                "top_topics": self.topic_counter.most_common(15),
                "history": list(self.history)[-60:],
                "escalation_alerts": list(self.escalation_alerts),
                "started_at": self.started_at,
                "now": datetime.now().isoformat(),
            }


metrics = MetricsTracker()
