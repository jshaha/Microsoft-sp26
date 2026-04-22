"""
End-to-end orchestrator: classify -> route -> extract -> vectorize -> rank.
"""

from __future__ import annotations

import uuid
from typing import List, Dict, Optional, Iterable, Tuple

from .classifier import CategoryClassifier
from .entity_extractor import (
    EntityAffectExtractor,
    EntityExtractorRegistry,
    FINANCE_ENTITY_TYPES,
)
from .schemas import ArticleAffectVector
from .user_profile import UserProfile
from .recommender import Recommender


class NewsRecommendationPipeline:
    """
    High-level facade covering the full backend pipeline.

    Example
    -------
    >>> pipe = NewsRecommendationPipeline(
    ...     classifier_dir="models/mind_distilbert_classifier",
    ...     qwen_base_model="Qwen/Qwen2.5-0.5B-Instruct",
    ...     category_adapters={"finance": "models/qwen2.5_finance_lora"},
    ... )
    >>> user = UserProfile("alice")
    >>> vec = pipe.ingest(user, title="...", abstract="...")
    >>> ranked = pipe.recommend(user, candidates=[...], top_k=5)
    """

    def __init__(
        self,
        classifier_dir: str,
        qwen_base_model: str = "Qwen/Qwen2.5-0.5B-Instruct",
        category_adapters: Optional[Dict[str, str]] = None,
        default_num_entities: int = 5,
        confidence_threshold: float = 0.60,
        device: Optional[str] = None,
    ):
        self.classifier = CategoryClassifier(
            classifier_dir,
            confidence_threshold=confidence_threshold,
            device=device,
        )

        self.extractors = EntityExtractorRegistry()

        # Always register a default (base Qwen, generic entity types)
        default_extractor = EntityAffectExtractor(
            base_model_name=qwen_base_model, adapter_dir=None, device=device
        )
        self.extractors.set_default(default_extractor)

        # Register each category-specific fine-tuned adapter
        category_adapters = category_adapters or {}
        for category, adapter_dir in category_adapters.items():
            entity_types = (
                FINANCE_ENTITY_TYPES if category.lower() == "finance" else None
            )
            self.extractors.register(
                category,
                EntityAffectExtractor(
                    base_model_name=qwen_base_model,
                    adapter_dir=adapter_dir,
                    entity_types=entity_types,
                    device=device,
                ),
            )

        self.default_num_entities = default_num_entities
        self.recommender = Recommender()

    # ------------------------------------------------------------------
    def process_article(
        self,
        title: str,
        abstract: str = "",
        article_id: Optional[str] = None,
        num_entities: Optional[int] = None,
    ) -> ArticleAffectVector:
        """Run the full pipeline on one article and return its affect vector."""
        route = self.classifier.route(title, abstract)
        category = route["category"]
        confidence = route["confidence"]

        body = (title + "\n\n" + abstract).strip()
        entities = self.extractors.extract(
            category,
            body,
            num_entities=num_entities or self.default_num_entities,
        )

        return ArticleAffectVector(
            article_id=article_id or str(uuid.uuid4()),
            title=title,
            abstract=abstract,
            category=category,
            confidence=confidence,
            entities=entities,
        )

    # ------------------------------------------------------------------
    def ingest(
        self,
        user: UserProfile,
        title: str,
        abstract: str = "",
        article_id: Optional[str] = None,
    ) -> ArticleAffectVector:
        """Process an article AND fold it into the user's profile."""
        vec = self.process_article(title, abstract, article_id=article_id)
        user.update(vec)
        return vec

    # ------------------------------------------------------------------
    def recommend(
        self,
        user: UserProfile,
        candidates: Iterable[Dict],
        top_k: Optional[int] = 10,
    ) -> List[Dict]:
        """
        Process each candidate (dict with at least `title` and `abstract`)
        and return a ranked list of dicts with scores.
        """
        processed: List[ArticleAffectVector] = []
        for c in candidates:
            processed.append(
                self.process_article(
                    title=c.get("title", ""),
                    abstract=c.get("abstract", ""),
                    article_id=c.get("id") or c.get("article_id"),
                )
            )

        ranked: List[Tuple[ArticleAffectVector, float]] = self.recommender.rank(
            user, processed, top_k=top_k
        )

        return [
            {**v.to_dict(), "score": float(score)}
            for v, score in ranked
        ]

    # ------------------------------------------------------------------
    def describe_user(self, user: UserProfile, top_n: int = 3) -> List[str]:
        """NL bullets for the UI (""You've been reading a lot of ..."")."""
        return user.describe(top_n=top_n)
