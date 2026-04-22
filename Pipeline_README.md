# MSN Sentiment-Aware News Pipeline — End-to-End Guide
 
This document describes the full MSN sentiment-aware recommendation
system: the ML pipeline (`pipeline/`), the FastAPI backend (`app.py`),
and the React dashboard (`frontend/`). It covers setup, the API surface
consumed by the UI, calling conventions, and worked examples.
 
Research goal (unchanged from the proposal): move MSN's feed away from
engagement-maximizing objectives toward **affective alignment** —
recommending articles whose entity-level sentiment (valence, arousal)
matches the user's reading-graph state, countering doomscrolling.
 
## 1. Architecture
 
```
                     ┌─────────────────────────────────────────────────────────────┐
                     │                    React dashboard                          │
                     │              (frontend/ — Vite + Leaflet)                   │
                     │                                                             │
                     │   TopTopics · Headlines · WelcomeCard · MoodCards           │
                     │   Collections · SourceBias · GlobalMap · ChatBar            │
                     └───────────────────────────┬─────────────────────────────────┘
                                                 │ HTTP / JSON (fetch via src/api.js)
                                                 ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                      FastAPI backend (app.py)                            │
  │  ┌───────────────────────────────┐   ┌───────────────────────────────┐  │
  │  │ /classify /process /ingest    │   │ /feed/*  /users/{id}/*        │  │
  │  │ /recommend  (ML pipeline tier)│   │ /map/markers /search /chat    │  │
  │  │                               │   │ (Dashboard tier, FeedService) │  │
  │  └──────────────┬────────────────┘   └──────────────┬────────────────┘  │
  └─────────────────┼──────────────────────────────────┼─────────────────────┘
                    │                                  │
                    ▼                                  ▼
  ┌──────────────┐   ┌──────────────────────────┐   ┌────────────────────────┐
  │ Incoming     │   │ DistilBERT Category      │   │ Category-specific      │
  │ Article      │──▶│ Classifier (11 classes)  │──▶│ Fine-tuned Qwen2.5     │
  │ (title+body) │   │  Classifier/             │   │ LoRA (MoE router)      │
  └──────────────┘   └──────────────────────────┘   └───────────┬────────────┘
                                                                │
                                              entities + affect ▼
                            ┌──────────────────────────────────────────────────┐
                            │  ArticleAffectVector                              │
                            │  {category, confidence, entities[{text, type,    │
                            │   sentiment, valence ∈ [-1,1], arousal ∈ [0,1]}]}│
                            └─────────┬─────────────────────────┬───────────────┘
                                      │                         │
                             ingest() │                         │ recommend()
                                      ▼                         ▼
                            ┌───────────────────┐     ┌───────────────────────┐
                            │ UserProfile       │     │ Recommender           │
                            │ (knowledge graph, │◀───▶│ cosine sim(u, cand.)  │
                            │  reads/shares/    │     │ + entity overlap      │
                            │  collections)     │     └───────────────────────┘
                            └───────────────────┘
                                      ▲
                                      │ seeded corpus + derived views
                            ┌───────────────────┐
                            │ ArticleStore      │   — publisher, region, lean
                            │ FeedService       │   — views for the dashboard
                            └───────────────────┘
```
 
### Mapping to the codebase
 
| Stage | Source | Wrapper |
|---|---|---|
| 1. Classifier | `Classifier/mind-bert-classifier (1).ipynb` | `pipeline/classifier.py` |
| 2. Entity + Affect LLM (MoE) | `Entity Extraction_MSN/entity_extraction.ipynb` | `pipeline/entity_extractor.py` |
| 3. Affect score vector | aggregation step | `pipeline/schemas.py` |
| 4a. UX integration (legacy) | `Entity Extraction_MSN/ux.py` | superseded — see §5 below |
| 4b. User knowledge graph | new | `pipeline/user_profile.py` |
| 4c. Recommender | cosine-similarity | `pipeline/recommender.py` |
| 5. Article corpus | seeded in-memory store | `pipeline/article_store.py` |
| 6. Publisher metadata (brand + lean) | — | `pipeline/publishers.py` |
| 7. Dashboard composite views | — | `pipeline/feed_service.py` |
| 8. HTTP API | — | `app.py` |
| 9. React dashboard | Vite + Leaflet | `frontend/` |
 
## 2. Setup
 
### 2.1 Backend
 
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
 
The backend has two deployment modes:
 
1. **Full mode** — with `torch` / `transformers` / `peft` and the DistilBERT +
   Qwen weights available. All pipeline endpoints (`/classify`,
   `/process`, `/ingest`, `/recommend`) work, and dashboard endpoints
   run real affect extraction through the pipeline.
2. **Dashboard-only mode** — the ML deps are not installed (or the
   classifier directory is missing). The `/feed/*` and `/users/{id}/*`
   endpoints still serve the UI using the seeded valence/arousal on
   stored articles; the `/classify` / `/process` endpoints return HTTP
   503 with a clear error. Useful for frontend work.
### 2.2 Train / obtain weights (full mode)
 
Both notebooks save HuggingFace-compatible artifacts. Place them under
`models/`:
 
```
models/
├── mind_distilbert_classifier/    ←  notebook cell 9 of the classifier
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer.json / vocab.txt
│   └── label_map.json
└── qwen2.5_finance_lora/          ←  `trainer.save_model(...)` LoRA adapter
    ├── adapter_config.json
    └── adapter_model.safetensors
```
 
### 2.3 Environment variables (consumed by `app.py`)
 
| Variable | Default | Meaning |
|---|---|---|
| `CLASSIFIER_DIR` | `models/mind_distilbert_classifier` | Path to exported DistilBERT classifier (optional — dashboard mode works without it) |
| `QWEN_BASE_MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` | HF id of the Qwen base model |
| `FINANCE_ADAPTER_DIR` | *(unset)* | Path to the finance LoRA adapter |
| `DEVICE` | auto | Force `cuda` or `cpu` |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173` | Comma-separated CORS origins |
 
### 2.4 Frontend
 
```bash
cd frontend
npm install
npm run dev           # opens http://localhost:5173
```
 
`vite.config.js` proxies `/api/*` → `http://localhost:8000`, so the
React client calls relative URLs (`/api/feed/welcome?...`) and the same
code works in production if you build with
`VITE_API_BASE=https://your-api npm run build`.
 
## 3. Running the full stack
 
In two shells:
 
```bash
# shell 1 — backend
export CLASSIFIER_DIR=models/mind_distilbert_classifier
export FINANCE_ADAPTER_DIR=models/qwen2.5_finance_lora
uvicorn app:app --host 0.0.0.0 --port 8000
 
# shell 2 — frontend
cd frontend && npm run dev
```
 
Visit `http://localhost:5173` for the dashboard and
`http://localhost:8000/docs` for the OpenAPI UI.
 
## 4. Python API (programmatic use — pipeline tier)
 
```python
from pipeline import NewsRecommendationPipeline, UserProfile
 
pipe = NewsRecommendationPipeline(
    classifier_dir="models/mind_distilbert_classifier",
    qwen_base_model="Qwen/Qwen2.5-0.5B-Instruct",
    category_adapters={"finance": "models/qwen2.5_finance_lora"},
    confidence_threshold=0.60,
)
 
alice = UserProfile("alice")
 
# 1. Ingest an article into the user's profile
vec = pipe.ingest(
    alice,
    title="Apple rose after reporting stronger services revenue",
    abstract="Apple shares climbed 3% after Q4 services revenue beat expectations...",
)
 
# 2. Describe the user in natural language
for bullet in pipe.describe_user(alice):
    print(bullet)
 
# 3. Rank candidate articles by affective alignment
ranked = pipe.recommend(alice, candidates=[{...}, {...}], top_k=5)
```
 
### Key objects
 
| Object | Purpose |
|---|---|
| `CategoryClassifier` | DistilBERT + label map; `{category, confidence, uncertain}` |
| `EntityAffectExtractor` | One Qwen expert (base or LoRA-adapter) |
| `EntityExtractorRegistry` | MoE router: `category -> extractor` + default |
| `ArticleAffectVector` | Typed article record; `.as_vector()` → `[mean_valence, mean_arousal]` |
| `UserProfile` | Entity-level stats + reading events, shares, collections |
| `Recommender` | Blend of affect similarity + entity overlap |
| `NewsRecommendationPipeline` | Facade combining all of the above |
| `ArticleStore` | Thread-safe in-memory seeded corpus |
| `FeedService` | Composite views for the dashboard (headlines, top-topics, mood, stats, bias, map, chat) |
| `publishers.publisher_style/lean` | Brand colours, font, political lean |
 
## 5. HTTP API
 
All endpoints accept/return JSON. The API has two tiers.
 
### 5.1 Pipeline tier (needs `torch`/`transformers` + model weights)
 
#### `GET /health`
```json
{"status": "ok", "pipeline": "loaded", "articles": "33"}
```
 
#### `POST /classify` — stage 1 only
```json
// request
{"title": "Apple unveils new MacBook Pro", "abstract": "", "top_k": 3}
 
// response
{"predictions": [
  {"category": "autos", "confidence": 0.73, "uncertain": false},
  {"category": "entertainment", "confidence": 0.17, "uncertain": false},
  {"category": "finance", "confidence": 0.05, "uncertain": false}
]}
```
 
#### `POST /process` — full pipeline on one article
```json
{
  "article_id": "a1",
  "title": "Tesla shares fell...",
  "category": "finance",
  "confidence": 0.91,
  "entities": [
    {"text": "Tesla", "type": "Company", "sentiment": "negative",
     "valence": -0.68, "arousal": 0.62,
     "evidence": "Tesla shares fell"}
  ],
  "mean_valence": -0.5,
  "mean_arousal": 0.55
}
```
 
#### `POST /ingest` — process + attribute to user
```json
{"user_id": "alice", "article": {"title": "...", "abstract": "..."}}
```
 
#### `POST /recommend`
```json
{
  "user_id": "alice",
  "top_k": 5,
  "candidates": [{"id": "a1", "title": "...", "abstract": "..."}, ...]
}
```
 
#### `GET /users/{user_id}/summary`, `GET /users/{user_id}/profile`, `DELETE /users/{user_id}` — unchanged from v0.1.
 
### 5.2 Dashboard tier (works in both modes)
 
Every endpoint below is called by exactly one frontend component.
 
| Component | Endpoint(s) |
|---|---|
| `WelcomeCard` | `GET /feed/welcome?user_id=` |
| `Headlines` | `GET /feed/headlines?user_id=&n=` |
| `TopTopics` | `GET /feed/top-topics?user_id=&k=` |
| `MoodCards` | `POST /feed/mood  {user_id, mode: "cheer_me_up" \| "feeling_lucky"}` |
| `Collections` (Collections tab) | `GET /users/{id}/collections?topic=`, `POST /users/{id}/collections`, `POST /users/{id}/collections/{cid}/articles` |
| `Collections` (Stats tab) | `GET /users/{id}/stats` |
| `SourceBias` | `GET /users/{id}/bias` |
| `GlobalMap` | `GET /map/markers` |
| `ChatBar` | `POST /chat  {user_id, message}` |
| `TopBar` (search box) | `GET /search?q=&k=` |
| All (click-through) | `POST /ingest/by-id  {user_id, article_id}` |
| Share action | `POST /users/{id}/shares  {article_id}` |
| Browse corpus | `GET /articles?category=&limit=`, `GET /articles/{id}` |
 
#### Example: `GET /feed/top-topics?user_id=mark_johnson&k=3`
```json
{
  "topics": [
    {
      "id": 1, "category": "finance", "label": "Today's Money", "icon": "💰",
      "value": "12 articles", "delta": "+18%", "up": true,
      "article": {
        "id": "a-ft-fed-rates",
        "title": "Fed holds rates steady as inflation cools to 2.4%",
        "publisher": "Financial Times",
        "image": "https://...", "url": "https://ft.com",
        "publisherBg": "#fff1e5", "publisherColor": "#0d0d0d",
        "publisherFont": "Georgia, serif"
      }
    },
    ...
  ]
}
```
 
#### Example: `GET /users/{id}/bias`
```json
{
  "left":   {"sources": 6, "lean": "Left-leaning"},
  "center": {"sources": 9, "lean": "Center"},
  "right":  {"sources": 2, "lean": "Right-leaning"},
  "total": 17
}
```
 
#### Example: `POST /feed/mood`
```json
// request
{"user_id": "mark_johnson", "mode": "cheer_me_up"}
 
// response
{
  "mode": "cheer_me_up",
  "article": {
    "id": "a-posi-kingbirds",
    "title": "King of the birds set to return to England's skies",
    "url": "https://www.positive.news/...",
    "publisher": "Positive News",
    "valence": 0.8, "arousal": 0.4,
    "publisherBg": "#f6a623", "publisherColor": "#000",
    "publisherFont": "Arial, sans-serif"
  }
}
```
 
Mood filtering is pipeline-aligned: cheer-me-up surfaces articles whose
`mean_valence ≥ 0.45` *and* `arousal ≤ 0.65` (high positive, low
agitation — antithesis of doomscroll fuel). Feeling-lucky samples
uniformly but excludes already-read ids.
 
## 6. Calling conventions & contracts
 
- **Sentiment labels**: lower-case strings `"positive" | "neutral" | "negative"`.
- **Valence**: float in `[-1.0, 1.0]` — clamped automatically in the extractor.
- **Arousal**: float in `[0.0, 1.0]` — clamped automatically.
- **Category strings**: one of the 11 DistilBERT classes (`autos`,
  `entertainment`, `finance`, `foodanddrink`, `health`, `lifestyle`,
  `movies`, `music`, `sports`, `travel`, `weather`), or `"uncertain"`
  when `top1_confidence < confidence_threshold`.
- **Uncertain routing**: the registry's default extractor (generic base
  Qwen) is used.
- **Article identifiers**: store ids look like `a-<slug>`; user-
  submitted articles generate UUID4 if `id` is omitted.
- **Political lean**: `"left" | "center" | "right"`, attached per
  publisher in `pipeline/publishers.py`. Extend as needed.
- **Timestamps**: ISO-8601 strings (UTC). The backend generates them if
  the client omits them.
## 7. Extending with new category experts
 
```python
from pipeline import EntityAffectExtractor
 
sports = EntityAffectExtractor(
    base_model_name="Qwen/Qwen2.5-0.5B-Instruct",
    adapter_dir="models/qwen2.5_sports_lora",
    entity_types=["Team", "Player", "Coach", "Competition",
                  "League", "Venue", "Event"],
)
pipe.extractors.register("sports", sports)
```
 
The pipeline hot-picks the new expert for any article the classifier
routes to `sports`. No other code changes are needed; the dashboard
TopTopics card for the user's sports-heavy sessions will automatically
feature articles scored by the new expert.
 
## 8. Persistence
 
`UserProfile.to_dict()` / `UserProfile.from_dict()` round-trip:
 
- entity knowledge-graph (valence/arousal running sums)
- category counts, publisher counts
- reading events (`[{article_id, ts}]`), shares, collections
- `last_read_article_id`
Store in Redis / Postgres / a JSON column keyed on `user_id`. Swap the
in-memory `_users` dict in `app.py` for your store of choice.
 
```python
import json, pathlib
pathlib.Path(f"profiles/{alice.user_id}.json").write_text(
    json.dumps(alice.to_dict())
)
```
 
`ArticleStore.upsert(article)` takes any dict with an `id` field and is
thread-safe — replace the seeded corpus with a content-service adapter
in production.
 
## 9. Worked end-to-end example
 
```python
from pipeline import (
    NewsRecommendationPipeline, UserProfile, ArticleStore, FeedService,
)
 
pipe  = NewsRecommendationPipeline(
    classifier_dir="models/mind_distilbert_classifier",
    category_adapters={"finance": "models/qwen2.5_finance_lora"},
)
store = ArticleStore()
feed  = FeedService(pipeline=pipe, store=store)
 
mark = UserProfile("mark_johnson", display_name="Mark Johnson")
 
# Drive reads (would be POST /ingest/by-id calls from the dashboard)
for aid in ["a-ft-fed-rates", "a-reuters-supply", "a-espn-nba",
            "a-nyt-stocks-record"]:
    feed.ingest_url(mark, aid)
 
# Dashboard views
print(feed.welcome(mark))
print(feed.headlines(mark, n=4))
print(feed.top_topics(mark, k=3))
print(feed.source_bias(mark))
print(feed.stats(mark))
print(feed.mood(mark, "cheer_me_up"))
print(feed.chat(mark, "what is happening with the Fed?"))
 
# The cognitively-balanced recommendation is still the classic call:
ranked = pipe.recommend(mark, candidates=store.by_category("finance"), top_k=5)
```
 
## 10. Frontend integration notes
 
- State management: `frontend/src/UserContext.jsx` provides the
  current `userId` to every component. Swap it for your auth hook.
- Data layer: `frontend/src/api.js` is the single fetch wrapper. Every
  component calls `api.*` with no direct URL literals in the UI.
- Fallback: every component renders fine against the seeded
  `frontend/src/data.js` if the backend is down, so the dashboard is
  never blank during demos.
- Click-tracking: headline / top-topic / map / search clicks fire
  `POST /ingest/by-id` (fire-and-forget). This feeds the affect graph,
  which in turn changes the user's top-topics, bias arc, and mood
  recommendations on the next render.
## 11. Performance notes
 
- **Model load is the expensive step** — do it once at process start
  (`uvicorn --workers 1` if memory-bound; more workers replicates models).
- DistilBERT inference is ~10 ms/article on CPU; Qwen-0.5B is 1–3 s on
  CPU, ~200 ms on a T4.
- `FeedService` views are O(#articles + #user-entities) per call and
  don't invoke the Qwen expert unless a new article is ingested.
- `UserProfile.update` is O(#entities); profile vectors are O(1) per
  read via stored running sums.
- The `ArticleStore` is in-memory and thread-safe; swap for a
  content-service adapter with the same interface in production.
## 12. Troubleshooting
 
| Symptom | Fix |
|---|---|
| `FileNotFoundError: Classifier directory not found` | Export the DistilBERT notebook artifact via `model.save_pretrained(dir); tokenizer.save_pretrained(dir)` and point `CLASSIFIER_DIR` at it. |
| `ImportError: peft is required ...` | `pip install peft` — only required when loading a LoRA adapter. |
| `[startup] ML pipeline unavailable (torch/transformers missing?)` | Intentional: dashboard-only mode. `pip install torch transformers peft` to enable the full pipeline, then restart. |
| HTTP 503 `"ML pipeline not initialised"` on `/classify` etc. | Same as above — load the models. |
| Extractor returns `entities: []` | Qwen didn't emit valid JSON. Increase `max_new_tokens`, lower article length, or retry with the base model (default fallback). |
| HTTP 400 `"User has no reading history"` on `/recommend` | Call `/ingest` (or `/ingest/by-id` from the UI) first, or seed with editorial defaults. |
| Classifier always returns `"uncertain"` | Lower `confidence_threshold` (default 0.60) or retrain with more data for the confused classes. |
| Frontend shows blank cards | Check the vite dev server proxy in `frontend/vite.config.js`; make sure the backend is listening at `VITE_BACKEND_URL` (default `http://localhost:8000`). |
| CORS errors in the browser console | Add your origin to the `ALLOWED_ORIGINS` env var before starting `uvicorn`. |
 
## 13. Frontend integration checklist (superseded — now implemented)
 
1. ✅ Ingest on interaction — every click in `Headlines`, `TopTopics`,
   `GlobalMap`, search dropdown, and `MoodCards` fires
   `POST /ingest/by-id`.
2. ✅ "You've been reading a lot of …" banner — returned by
   `GET /users/{id}/summary.descriptions` and surfaced in the
   ChatBar reply panel.
3. ✅ Rank candidates by affect — `POST /recommend` (unchanged). The
   dashboard's TopTopics featured articles are rank-1 picks from each
   of the user's top categories.
4. ✅ Chip colours via `sentiment` + `arousal` — publisher badges in
   `Headlines` and `GlobalMap` already pull from
   `pipeline/publishers.py`.