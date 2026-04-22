"""
MSN News Recommendation backend (FastAPI).
 
Run:
    uvicorn app:app --host 0.0.0.0 --port 8000
 
The backend exposes two tiers of endpoints:
 
    1. Pipeline endpoints (/classify, /process, /ingest, /recommend,
       /users/{id}/summary, /users/{id}/profile) — the core MoE-routed
       affect pipeline as described in Pipeline_README.md §1.
 
    2. Dashboard endpoints (/feed/*, /users/{id}/stats,
       /users/{id}/bias, /users/{id}/collections, /map/markers,
       /search, /chat) — composite views consumed by the React dashboard
       in frontend/. Implemented in pipeline.feed_service.FeedService.
 
Environment variables:
    CLASSIFIER_DIR      path to mind_distilbert_classifier/ (optional —
                        dashboard endpoints degrade gracefully if absent)
    QWEN_BASE_MODEL     HF id of base Qwen model (default Qwen/Qwen2.5-0.5B-Instruct)
    FINANCE_ADAPTER_DIR path to qwen2.5_finance_lora/ (optional)
    DEVICE              "cuda" | "cpu" (auto)
    ALLOWED_ORIGINS     comma-separated CORS origins (default:
                        http://localhost:5173, http://localhost:3000)
"""
 
from __future__ import annotations
 
import os
from typing import Dict, List, Optional
 
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
 
from pipeline import (
    ArticleStore,
    FeedService,
    UserProfile,
)
# NewsRecommendationPipeline pulls torch + transformers; import lazily so
# that dashboard-only deployments can start without those deps.
try:
    from pipeline import NewsRecommendationPipeline  # type: ignore
except Exception as _exc:  # pragma: no cover
    NewsRecommendationPipeline = None
    print(f"[startup] ML pipeline unavailable (torch/transformers missing?): {_exc}")
 
 
# ---------------------------------------------------------------- config ---
CLASSIFIER_DIR = os.environ.get("CLASSIFIER_DIR", "models/mind_distilbert_classifier")
QWEN_BASE_MODEL = os.environ.get("QWEN_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
FINANCE_ADAPTER_DIR = os.environ.get("FINANCE_ADAPTER_DIR")
DEVICE = os.environ.get("DEVICE")
 
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
    ).split(",") if o.strip()
]
 
category_adapters: Dict[str, str] = {}
if FINANCE_ADAPTER_DIR:
    category_adapters["finance"] = FINANCE_ADAPTER_DIR
 
 
# ---------------------------------------------------------------- app ------
app = FastAPI(title="MSN Sentiment-Aware News Recommendation", version="0.2.0")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
_pipeline = None
_store: ArticleStore = ArticleStore()
_feed: FeedService = FeedService(pipeline=None, store=_store)
_users: Dict[str, UserProfile] = {}
 
 
@app.on_event("startup")
def _load_models() -> None:
    """Best-effort: bring up the full ML pipeline if the classifier weights
    are available. If not, the dashboard endpoints still work because
    `FeedService` has a no-ML fallback path using seeded article affect."""
    global _pipeline, _feed
    if NewsRecommendationPipeline is not None and os.path.isdir(CLASSIFIER_DIR):
        try:
            _pipeline = NewsRecommendationPipeline(
                classifier_dir=CLASSIFIER_DIR,
                qwen_base_model=QWEN_BASE_MODEL,
                category_adapters=category_adapters,
                device=DEVICE,
            )
        except Exception as exc:  # pragma: no cover — depends on local env
            print(f"[startup] pipeline init failed: {exc}")
            _pipeline = None
    else:
        print(
            f"[startup] CLASSIFIER_DIR={CLASSIFIER_DIR!r} not found or "
            "torch/transformers unavailable; dashboard endpoints will use "
            "seeded affect only."
        )
    _feed = FeedService(pipeline=_pipeline, store=_store)
 
 
def _require_pipeline():
    if _pipeline is None:
        raise HTTPException(
            503,
            "ML pipeline not initialised. Set CLASSIFIER_DIR / "
            "FINANCE_ADAPTER_DIR and restart, or use dashboard endpoints.",
        )
    return _pipeline
 
 
def _get_user(user_id: str, display_name: str = "") -> UserProfile:
    if user_id not in _users:
        _users[user_id] = UserProfile(user_id, display_name=display_name)
    return _users[user_id]
 
 
# ---------------------------------------------------------------- schemas --
class Article(BaseModel):
    title: str
    abstract: str = ""
    id: Optional[str] = None
 
 
class IngestRequest(BaseModel):
    user_id: str
    article: Article
 
 
class IngestByIdRequest(BaseModel):
    user_id: str
    article_id: str
 
 
class RecommendRequest(BaseModel):
    user_id: str
    candidates: List[Article]
    top_k: int = Field(10, ge=1, le=200)
 
 
class ClassifyRequest(BaseModel):
    title: str
    abstract: str = ""
    top_k: int = Field(3, ge=1, le=10)
 
 
class MoodRequest(BaseModel):
    user_id: str
    mode: str  # "cheer_me_up" | "feeling_lucky"
 
 
class CollectionCreateRequest(BaseModel):
    name: str
    topic: str
 
 
class CollectionArticleRequest(BaseModel):
    article_id: str
 
 
class ShareRequest(BaseModel):
    article_id: str
 
 
class ChatRequest(BaseModel):
    user_id: str
    message: str
 
 
# ============================================================ ML pipeline ==
@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "pipeline": "loaded" if _pipeline is not None else "offline",
        "articles": str(len(_store)),
    }
 
 
@app.post("/classify")
def classify(req: ClassifyRequest):
    pipe = _require_pipeline()
    return {"predictions": pipe.classifier.classify(
        req.title, req.abstract, top_k=req.top_k
    )}
 
 
@app.post("/process")
def process(article: Article):
    pipe = _require_pipeline()
    vec = pipe.process_article(
        title=article.title,
        abstract=article.abstract,
        article_id=article.id,
    )
    return vec.to_dict()
 
 
@app.post("/ingest")
def ingest(req: IngestRequest):
    pipe = _require_pipeline()
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
    pipe = _require_pipeline()
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
        "display_name": user.display_name,
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
 
 
# ============================================================ dashboard ==
@app.post("/ingest/by-id")
def ingest_by_id(req: IngestByIdRequest):
    """Record a read of a stored article (runs the pipeline if available)."""
    user = _get_user(req.user_id)
    try:
        vec = _feed.ingest_url(user, req.article_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    return {"article": vec, "profile_size": len(user.history_ids)}
 
 
@app.get("/feed/welcome")
def feed_welcome(user_id: str = Query(...)):
    return _feed.welcome(_get_user(user_id))
 
 
@app.get("/feed/headlines")
def feed_headlines(user_id: Optional[str] = None, n: int = 4):
    user = _get_user(user_id) if user_id else None
    return {"headlines": _feed.headlines(user=user, n=n)}
 
 
@app.get("/feed/top-topics")
def feed_top_topics(user_id: str = Query(...), k: int = 3):
    return {"topics": _feed.top_topics(_get_user(user_id), k=k)}
 
 
@app.post("/feed/mood")
def feed_mood(req: MoodRequest):
    return _feed.mood(_get_user(req.user_id), req.mode)
 
 
@app.get("/users/{user_id}/stats")
def user_stats(user_id: str):
    return _feed.stats(_get_user(user_id))
 
 
@app.get("/users/{user_id}/bias")
def user_bias(user_id: str):
    return _feed.source_bias(_get_user(user_id))
 
 
@app.get("/users/{user_id}/collections")
def list_collections(user_id: str, topic: Optional[str] = None):
    return {"collections": _feed.list_collections(_get_user(user_id), topic=topic)}
 
 
@app.post("/users/{user_id}/collections")
def create_collection(user_id: str, req: CollectionCreateRequest):
    return _feed.create_collection(_get_user(user_id), req.name, req.topic)
 
 
@app.post("/users/{user_id}/collections/{collection_id}/articles")
def add_article_to_collection(
    user_id: str, collection_id: str, req: CollectionArticleRequest
):
    user = _get_user(user_id)
    try:
        user.add_to_collection(collection_id, req.article_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    return user.collections[collection_id]
 
 
@app.post("/users/{user_id}/shares")
def record_share(user_id: str, req: ShareRequest):
    user = _get_user(user_id)
    user.record_share(req.article_id)
    return {"shares": len(user.shares)}
 
 
@app.get("/map/markers")
def map_markers():
    return {"markers": _feed.map_markers()}
 
 
@app.get("/search")
def search(q: str = Query(..., min_length=1), k: int = 10):
    return {"results": _feed.search(q, limit=k)}
 
 
@app.post("/chat")
def chat(req: ChatRequest):
    return _feed.chat(_get_user(req.user_id), req.message)
 
 
@app.get("/articles")
def list_articles(category: Optional[str] = None, limit: int = 50):
    rows = _store.by_category(category) if category else _store.all()
    rows.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    return {"articles": rows[:limit]}
 
 
@app.get("/articles/{article_id}")
def get_article(article_id: str):
    a = _store.get(article_id)
    if a is None:
        raise HTTPException(404, f"Article '{article_id}' not found.")
    return a