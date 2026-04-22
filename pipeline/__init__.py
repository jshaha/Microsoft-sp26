"""
MSN News Recommendation Pipeline
================================
Hyperpersonalized, sentiment-aware article recommendation layer.

Pipeline stages (see docs/Pipeline_README.md):
    1. DistilBERT category classifier        -> Classifier/
    2. Category-routed Qwen2.5 entity+affect  -> Entity Extraction_MSN/
    3. Article affect vector aggregation
    4. Cosine-similarity match vs. user KG    -> Recommender
"""

from .classifier import CategoryClassifier
from .entity_extractor import (
    EntityAffectExtractor,
    EntityExtractorRegistry,
    FINANCE_ENTITY_TYPES,
)
from .schemas import EntityAffect, ArticleAffectVector
from .user_profile import UserProfile
from .recommender import Recommender, cosine_similarity
from .pipeline import NewsRecommendationPipeline

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
]
