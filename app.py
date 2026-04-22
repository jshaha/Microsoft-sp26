"""
MSN News Recommendation backend (FastAPI).

Run:
    uvicorn app:app --host 0.0.0.0 --port 8000

Environment variables:
    CLASSIFIER_DIR      path to mind_distilbert_classifier/ (required)
    QWEN_BASE_MODEL     HF id of base Qwen model (default Qwen/Qwen2.5-0.5B-Instruct)
    FINANCE_ADAPTER_DIR path to qwen2.5_finance_lora/ (optional)
    DEVICE              "cuda" | "cpu" (auto)
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pipeline import NewsRecommendationPipeline, UserProfile


# ---------------------------------------------------------------- config ---
CLASSIFIER_DIR = os.environ.get(
    "CLASSIFIER_DIR", "models/mind_distilbert_classifier"
)
QWEN_BASE_MODEL = os.environ.get("QWEN_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
FINANCE_ADAPTER_DIR = os.environ.get("FINANCE_ADAPTER_DIR")
DEVICE = os.environ.get("DEVICE")

category_adapters: Dict[str, str] = {}
if FINANCE_ADAPTER_DIR:
    category_adapters["finance"] = FINANCE_ADAPTER_DIR


# ---------------------------------------------------------------- app ------
app = FastAPI(title="MSN Sentiment-Aware News Recommendation", version="0.1.0")

_pipeline: Optional[NewsRecommendationPipeline] = None
_users: Dict[str, UserProfile] = {}       # replace with Redis/DB in prod


@app.on_event("startup")
def _load_models() -> None:
    global _pipeline
    _pipeline = NewsRecommendationPipeline(
        classifier_dir=CLASSIFIER_DIR,
        qwen_base_model=QWEN_BASE_MODEL,
        category_adapters=category_adapters,
        device=DEVICE,
    )


def _get_pipeline() -> NewsRecommendationPipeline:
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not initialised yet.")
    return _pipeline


def _get_user(user_id: str) -> UserProfile:
    return _users.setdefault(user_id, UserProfile(user_id))


# ---------------------------------------------------------------- schemas --
class Article(BaseModel):
    title: str
    abstract: str = ""
    id: Optional[str] = None


class IngestRequest(BaseModel):
    user_id: str
    article: Article


class RecommendRequest(BaseModel):
    user_id: str
    candidates: List[Article]
    top_k: int = Field(10, ge=1, le=200)


class ClassifyRequest(BaseModel):
    title: str
    abstract: str = ""
    top_k: int = Field(3, ge=1, le=10)


# ---------------------------------------------------------------- routes --
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok" if _pipeline is not None else "loading"}


@app.post("/classify")
def classify(req: ClassifyRequest):
    """Stage 1 only: category routing."""
    pipe = _get_pipeline()
    return {"predictions": pipe.classifier.classify(
        req.title, req.abstract, top_k=req.top_k
    )}


@app.post("/process")
def process(article: Article):
    """Full pipeline on one article, without touching any user profile."""
    pipe = _get_pipeline()
    vec = pipe.process_article(
        title=article.title,
        abstract=article.abstract,
        article_id=article.id,
    )
    return vec.to_dict()


@app.post("/ingest")
def ingest(req: IngestRequest):
    """Process an article and attribute it to a user's history."""
    pipe = _get_pipeline()
    user = _get_user(req.user_id)
    vec = pipe.ingest(
        user,
        title=req.article.title,
        abstract=req.article.abstract,
        article_id=req.article.id,
    )
    return {"article": vec.to_dict(), "profile_size": len(user.history_ids)}


@app.post("/recommend")
def recommend(req: RecommendRequest):
    pipe = _get_pipeline()
    user = _get_user(req.user_id)
    if not user.history_ids:
        raise HTTPException(
            400,
            "User has no reading history; call /ingest first or "
            "send neutral recommendations from the client.",
        )
    ranked = pipe.recommend(
        user,
        candidates=[c.model_dump() for c in req.candidates],
        top_k=req.top_k,
    )
    return {"recommendations": ranked}


@app.get("/users/{user_id}/summary")
def user_summary(user_id: str):
    user = _get_user(user_id)
    return {
        "user_id": user_id,
        "history_size": len(user.history_ids),
        "top_entities": user.top_entities(k=10),
        "top_categories": user.top_categories(k=5),
        "descriptions": user.describe(top_n=3),
        "profile_vector": user.profile_vector().tolist(),
    }


@app.get("/users/{user_id}/profile")
def user_profile(user_id: str):
    return _get_user(user_id).to_dict()


@app.delete("/users/{user_id}")
def reset_user(user_id: str):
    _users.pop(user_id, None)
    return {"status": "cleared"}
