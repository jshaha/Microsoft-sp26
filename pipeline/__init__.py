"""
MSN News Recommendation Pipeline
================================
Hyperpersonalized, sentiment-aware article recommendation layer.
 
Pipeline stages (see Pipeline_README.md):
    1. DistilBERT category classifier        -> Classifier/
    2. Category-routed Qwen2.5 entity+affect  -> Entity Extraction_MSN/
    3. Article affect vector aggregation
    4. Cosine-similarity match vs. user KG    -> Recommender
 
Dashboard integration layer:
    - ArticleStore   : in-memory article corpus + metadata
    - FeedService    : composite views consumed by the frontend
    - publishers     : publisher styling + political lean
 
The ML modules (classifier, entity_extractor, pipeline) import torch /
transformers; they are loaded lazily on first access so that a
dashboard-only deployment (e.g. frontend devs running only FeedService
against seeded data) does not require those heavy dependencies to be
installed.
"""
 
from .schemas import EntityAffect, ArticleAffectVector
from .user_profile import UserProfile
from .recommender import Recommender, cosine_similarity
from .article_store import ArticleStore
from .feed_service import FeedService
from .publishers import (
    PUBLISHER_META,
    UNKNOWN_PUBLISHER,
    publisher_style,
    publisher_lean,
)
 
 
def __getattr__(name):
    """Lazy-import the ML wrappers; skip when torch/transformers are absent."""
    if name == "CategoryClassifier":
        from .classifier import CategoryClassifier as _C
        return _C
    if name in ("EntityAffectExtractor", "EntityExtractorRegistry",
                "FINANCE_ENTITY_TYPES"):
        from . import entity_extractor as _e
        return getattr(_e, name)
    if name == "NewsRecommendationPipeline":
        from .pipeline import NewsRecommendationPipeline as _P
        return _P
    raise AttributeError(name)
 
 
__all__ = [
    "CategoryClassifier",
    "EntityAffectExtractor",
    "EntityExtractorRegistry",
    "FINANCE_ENTITY_TYPES",
    "EntityAffect",
    "ArticleAffectVector",
    "UserProfile",
    "Recommender",
    "cosine_similarity",
    "NewsRecommendationPipeline",
    "ArticleStore",
    "FeedService",
    "PUBLISHER_META",
    "UNKNOWN_PUBLISHER",
    "publisher_style",
    "publisher_lean",
]