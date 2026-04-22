"""
Cosine-similarity based recommender.

The recommendation objective is *affective alignment*, not engagement
maximization. For each candidate article we compute the cosine similarity
between the 2-D article affect vector [mean_valence, mean_arousal] and
the user's aggregated profile vector, then rank descending.

`score_entity_level=True` also rewards candidate articles whose entities
overlap with the user's top entities (weighted by count).
"""

from __future__ import annotations

from typing import List, Tuple, Optional
import numpy as np

from .schemas import ArticleAffectVector
from .user_profile import UserProfile


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class Recommender:

    def __init__(
        self,
        entity_overlap_weight: float = 0.35,
        affect_weight: float = 0.65,
    ):
        assert 0.0 <= entity_overlap_weight <= 1.0
        assert 0.0 <= affect_weight <= 1.0
        self.entity_overlap_weight = entity_overlap_weight
        self.affect_weight = affect_weight

    # ------------------------------------------------------------------
    def affect_score(
        self, user: UserProfile, article: ArticleAffectVector
    ) -> float:
        return cosine_similarity(user.profile_vector(), article.as_vector())

    def entity_overlap_score(
        self, user: UserProfile, article: ArticleAffectVector
    ) -> float:
        if not article.entities:
            return 0.0
        matched = 0.0
        for e in article.entities:
            vec = user.entity_vector(e.text)
            if vec is not None:
                matched += cosine_similarity(vec, e.as_vector())
        return matched / max(len(article.entities), 1)

    def score(
        self, user: UserProfile, article: ArticleAffectVector
    ) -> float:
        return (
            self.affect_weight * self.affect_score(user, article)
            + self.entity_overlap_weight
            * self.entity_overlap_score(user, article)
        )

    # ------------------------------------------------------------------
    def rank(
        self,
        user: UserProfile,
        candidates: List[ArticleAffectVector],
        top_k: Optional[int] = None,
    ) -> List[Tuple[ArticleAffectVector, float]]:
        scored = [(c, self.score(user, c)) for c in candidates]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:top_k] if top_k else scored
