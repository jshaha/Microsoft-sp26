"""
User knowledge-graph profile.

Stores running per-entity and per-category affect statistics so that
(a) we can generate natural-language summaries of the user's feed
    ("You've been reading a lot of negative articles on JP Morgan"), and
(b) we can produce a single affect vector for cosine-similarity matching
    against candidate articles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
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


class UserProfile:
    """In-memory user knowledge-graph profile.

    Persist with `UserProfile.to_dict()` / `UserProfile.from_dict()`.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._entities: Dict[str, _EntityRunningStat] = {}
        self._category_counts: Dict[str, int] = {}
        self.history_ids: List[str] = []

    # ------------------------------------------------------------------
    def update(self, article_vec: ArticleAffectVector) -> None:
        """Fold a freshly-processed article into the profile."""
        self.history_ids.append(article_vec.article_id)
        self._category_counts[article_vec.category] = (
            self._category_counts.get(article_vec.category, 0) + 1
        )
        for e in article_vec.entities:
            key = e.text.strip().lower()
            if not key:
                continue
            stat = self._entities.setdefault(key, _EntityRunningStat())
            stat.update(e)

    # ------------------------------------------------------------------
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
            "history_ids": list(self.history_ids),
            "category_counts": dict(self._category_counts),
            "entities": {
                text: {
                    "count": s.count,
                    "valence_sum": s.valence_sum,
                    "arousal_sum": s.arousal_sum,
                    "last_type": s.last_type,
                }
                for text, s in self._entities.items()
            },
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "UserProfile":
        u = cls(d["user_id"])
        u.history_ids = list(d.get("history_ids", []))
        u._category_counts = dict(d.get("category_counts", {}))
        for text, payload in d.get("entities", {}).items():
            s = _EntityRunningStat(
                count=int(payload["count"]),
                valence_sum=float(payload["valence_sum"]),
                arousal_sum=float(payload["arousal_sum"]),
                last_type=str(payload.get("last_type", "")),
            )
            u._entities[text] = s
        return u
