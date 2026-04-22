"""Typed data structures used across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class EntityAffect:
    text: str
    type: str
    sentiment: str        # "positive" | "neutral" | "negative"
    valence: float        # in [-1.0, 1.0]
    arousal: float        # in [ 0.0, 1.0]
    evidence: str = ""

    def as_vector(self) -> np.ndarray:
        return np.array([self.valence, self.arousal], dtype=np.float32)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EntityAffect":
        return cls(
            text=str(d.get("text", "")),
            type=str(d.get("type", "")),
            sentiment=str(d.get("sentiment", "neutral")).lower(),
            valence=float(d.get("valence", 0.0)),
            arousal=float(d.get("arousal", 0.0)),
            evidence=str(d.get("evidence", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArticleAffectVector:
    """One article, fully annotated by the pipeline."""
    article_id: str
    title: str
    category: str                   # classifier output (or "uncertain")
    confidence: float               # top-1 classifier confidence
    entities: List[EntityAffect] = field(default_factory=list)
    abstract: str = ""

    # ---- aggregate affect ------------------------------------------------
    def mean_valence(self) -> float:
        if not self.entities:
            return 0.0
        return float(np.mean([e.valence for e in self.entities]))

    def mean_arousal(self) -> float:
        if not self.entities:
            return 0.0
        return float(np.mean([e.arousal for e in self.entities]))

    def as_vector(self) -> np.ndarray:
        """2-D article-level affect vector [mean_valence, mean_arousal]."""
        return np.array([self.mean_valence(), self.mean_arousal()],
                        dtype=np.float32)

    # ---- serialisation ---------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "abstract": self.abstract,
            "category": self.category,
            "confidence": self.confidence,
            "entities": [e.to_dict() for e in self.entities],
            "mean_valence": self.mean_valence(),
            "mean_arousal": self.mean_arousal(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArticleAffectVector":
        return cls(
            article_id=str(d["article_id"]),
            title=str(d.get("title", "")),
            abstract=str(d.get("abstract", "")),
            category=str(d.get("category", "uncertain")),
            confidence=float(d.get("confidence", 0.0)),
            entities=[EntityAffect.from_dict(e) for e in d.get("entities", [])],
        )
