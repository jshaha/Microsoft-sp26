"""
User knowledge-graph profile.
 
Stores running per-entity and per-category affect statistics so that
(a) we can generate natural-language summaries of the user's feed
    ("You've been reading a lot of negative articles on JP Morgan"), and
(b) we can produce a single affect vector for cosine-similarity matching
    against candidate articles.
 
In addition to the affect graph, the profile also tracks the
dashboard-facing behavioural state that the frontend needs:
 
    - reading_events  [{article_id, ts}]        (populates stats + last-read)
    - shares          [{article_id, ts}]        (share counter)
    - collections     {id: {name, topic, article_ids, created_at}}
    - publisher_counts {publisher: count}       (feeds source-bias arc)
"""
 
from __future__ import annotations
 
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
 
from .schemas import ArticleAffectVector, EntityAffect
 
 
@dataclass
class _EntityRunningStat:
    count: int = 0
    valence_sum: float = 0.0
    arousal_sum: float = 0.0
    last_type: str = ""
 
    def update(self, e: EntityAffect) -> None:
        self.count += 1
        self.valence_sum += e.valence
        self.arousal_sum += e.arousal
        self.last_type = e.type or self.last_type
 
    @property
    def mean_valence(self) -> float:
        return self.valence_sum / self.count if self.count else 0.0
 
    @property
    def mean_arousal(self) -> float:
        return self.arousal_sum / self.count if self.count else 0.0
 
 
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
 
 
def _parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)
 
 
class UserProfile:
    """In-memory user knowledge-graph profile.
 
    Persist with `UserProfile.to_dict()` / `UserProfile.from_dict()`.
    """
 
    def __init__(self, user_id: str, display_name: str = ""):
        self.user_id = user_id
        self.display_name = display_name or user_id.replace("_", " ").title()
        self._entities: Dict[str, _EntityRunningStat] = {}
        self._category_counts: Dict[str, int] = {}
        self._publisher_counts: Dict[str, int] = {}
        self.history_ids: List[str] = []
 
        # Behavioural state consumed by the dashboard endpoints
        self.reading_events: List[Dict[str, str]] = []   # {article_id, ts}
        self.shares: List[Dict[str, str]] = []           # {article_id, ts}
        self.collections: Dict[str, Dict[str, Any]] = {} # id -> record
        self.last_read_article_id: Optional[str] = None
 
    # ------------------------------------------------------------------
    def update(self, article_vec: ArticleAffectVector,
               publisher: Optional[str] = None,
               ts: Optional[str] = None) -> None:
        """Fold a freshly-processed article into the profile."""
        self.history_ids.append(article_vec.article_id)
        self._category_counts[article_vec.category] = (
            self._category_counts.get(article_vec.category, 0) + 1
        )
        if publisher:
            self._publisher_counts[publisher] = (
                self._publisher_counts.get(publisher, 0) + 1
            )
        for e in article_vec.entities:
            key = e.text.strip().lower()
            if not key:
                continue
            stat = self._entities.setdefault(key, _EntityRunningStat())
            stat.update(e)
 
        self.record_read(article_vec.article_id, ts=ts)
 
    # ------------------------------------------------------------------ behavioural events
    def record_read(self, article_id: str, ts: Optional[str] = None) -> None:
        self.reading_events.append({"article_id": article_id, "ts": ts or _now_iso()})
        self.last_read_article_id = article_id
 
    def record_share(self, article_id: str, ts: Optional[str] = None) -> None:
        self.shares.append({"article_id": article_id, "ts": ts or _now_iso()})
 
    def record_publisher(self, publisher: str) -> None:
        if publisher:
            self._publisher_counts[publisher] = self._publisher_counts.get(publisher, 0) + 1
 
    # ------------------------------------------------------------------ collections
    def add_collection(self, name: str, topic: str) -> str:
        cid = str(uuid.uuid4())
        self.collections[cid] = {
            "id": cid,
            "name": name,
            "topic": topic,
            "article_ids": [],
            "created_at": _now_iso(),
        }
        return cid
 
    def add_to_collection(self, collection_id: str, article_id: str) -> None:
        coll = self.collections.get(collection_id)
        if coll is None:
            raise KeyError(f"Collection '{collection_id}' not found.")
        if article_id not in coll["article_ids"]:
            coll["article_ids"].append(article_id)
 
    def collections_by_topic(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        items = list(self.collections.values())
        if topic and topic.lower() != "all":
            items = [c for c in items if c["topic"].lower() == topic.lower()]
        return sorted(items, key=lambda c: c["created_at"], reverse=True)
 
    # ------------------------------------------------------------------ stats
    def weekly_read_counts(self, n_weeks: int = 4) -> List[Tuple[str, int]]:
        """Return [(week_label, count)] for the most recent `n_weeks` weeks (chronological)."""
        now = datetime.now(timezone.utc)
        # Monday-anchored week starts
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        buckets: List[Tuple[datetime, int]] = [
            (week_start - timedelta(weeks=i), 0) for i in range(n_weeks - 1, -1, -1)
        ]
        for ev in self.reading_events:
            t = _parse_iso(ev["ts"])
            for i, (start, count) in enumerate(buckets):
                end = start + timedelta(weeks=1)
                if start <= t < end:
                    buckets[i] = (start, count + 1)
                    break
        return [
            (f"{start.strftime('%b')} {start.day}", c)
            for start, c in buckets
        ]
 
    def reads_since(self, days: int = 7) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(1 for ev in self.reading_events if _parse_iso(ev["ts"]) >= cutoff)
 
    def shares_since(self, days: int = 7) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(1 for ev in self.shares if _parse_iso(ev["ts"]) >= cutoff)
 
    # ------------------------------------------------------------------ affect / recs
    def profile_vector(self) -> np.ndarray:
        """Count-weighted mean [valence, arousal] across all entities."""
        if not self._entities:
            return np.array([0.0, 0.0], dtype=np.float32)
        total = sum(s.count for s in self._entities.values())
        v = sum(s.valence_sum for s in self._entities.values()) / total
        a = sum(s.arousal_sum for s in self._entities.values()) / total
        return np.array([v, a], dtype=np.float32)
 
    def entity_vector(self, entity_text: str) -> Optional[np.ndarray]:
        stat = self._entities.get(entity_text.strip().lower())
        if stat is None:
            return None
        return np.array([stat.mean_valence, stat.mean_arousal],
                        dtype=np.float32)
 
    def top_entities(
        self, k: int = 10
    ) -> List[Tuple[str, float, float, int]]:
        """Returns [(entity_text, mean_valence, mean_arousal, count), ...]."""
        items = sorted(
            self._entities.items(), key=lambda kv: kv[1].count, reverse=True
        )[:k]
        return [
            (text, s.mean_valence, s.mean_arousal, s.count)
            for text, s in items
        ]
 
    def top_categories(self, k: int = 5) -> List[Tuple[str, int]]:
        return sorted(
            self._category_counts.items(), key=lambda kv: kv[1], reverse=True
        )[:k]
 
    def top_publishers(self, k: int = 10) -> List[Tuple[str, int]]:
        return sorted(
            self._publisher_counts.items(), key=lambda kv: kv[1], reverse=True
        )[:k]
 
    # ------------------------------------------------------------------
    def describe(self, top_n: int = 3) -> List[str]:
        """
        Generate human-readable descriptions of the user's consumption,
        e.g. "You've been reading a lot of negative articles on JP Morgan".
        """
        bullets: List[str] = []
        for entity, val, _arousal, count in self.top_entities(top_n):
            if count < 2:
                continue
            if val >= 0.15:
                tone = "positive"
            elif val <= -0.15:
                tone = "negative"
            else:
                tone = "neutral"
            bullets.append(
                f"You've been reading a lot of {tone} articles on "
                f"{entity.title()} ({count} articles, mean valence "
                f"{val:+.2f})."
            )
        return bullets
 
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "history_ids": list(self.history_ids),
            "category_counts": dict(self._category_counts),
            "publisher_counts": dict(self._publisher_counts),
            "entities": {
                text: {
                    "count": s.count,
                    "valence_sum": s.valence_sum,
                    "arousal_sum": s.arousal_sum,
                    "last_type": s.last_type,
                }
                for text, s in self._entities.items()
            },
            "reading_events": list(self.reading_events),
            "shares": list(self.shares),
            "collections": {k: dict(v) for k, v in self.collections.items()},
            "last_read_article_id": self.last_read_article_id,
        }
 
    @classmethod
    def from_dict(cls, d: Dict) -> "UserProfile":
        u = cls(d["user_id"], display_name=d.get("display_name", ""))
        u.history_ids = list(d.get("history_ids", []))
        u._category_counts = dict(d.get("category_counts", {}))
        u._publisher_counts = dict(d.get("publisher_counts", {}))
        for text, payload in d.get("entities", {}).items():
            s = _EntityRunningStat(
                count=int(payload["count"]),
                valence_sum=float(payload["valence_sum"]),
                arousal_sum=float(payload["arousal_sum"]),
                last_type=str(payload.get("last_type", "")),
            )
            u._entities[text] = s
        u.reading_events = list(d.get("reading_events", []))
        u.shares = list(d.get("shares", []))
        u.collections = {k: dict(v) for k, v in d.get("collections", {}).items()}
        u.last_read_article_id = d.get("last_read_article_id")
        return u