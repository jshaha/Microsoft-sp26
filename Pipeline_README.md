# Pipeline Wrapper & Backend Integration Guide

This document describes the end-to-end backend wrapper that combines every
stage of the MSN sentiment-aware recommendation system into a single
importable package (`pipeline/`) and HTTP service (`app.py`). It covers
setup, API surface, calling conventions, and worked examples.

## 1. Architecture

```
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
                            │ (knowledge graph) │◀───▶│ cosine sim(u, cand.)  │
                            └───────────────────┘     └───────────────────────┘
```

### Mapping to the codebase
| Stage | Source | Wrapper |
|---|---|---|
| 1. Classifier | `Classifier/mind-bert-classifier (1).ipynb` | `pipeline/classifier.py` |
| 2. Entity + Affect LLM | `Entity Extraction_MSN/entity_extraction.ipynb` | `pipeline/entity_extractor.py` |
| 3. Affect score vector | aggregation step | `pipeline/schemas.py` |
| 4. UX integration | `Entity Extraction_MSN/ux.py` | `pipeline/user_profile.py`, `pipeline/recommender.py`, `app.py` |

## 2. Setup

### 2.1 Install

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 Train / obtain weights

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
| `CLASSIFIER_DIR` | `models/mind_distilbert_classifier` | Path to exported DistilBERT classifier |
| `QWEN_BASE_MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` | HF id of the Qwen base model |
| `FINANCE_ADAPTER_DIR` | *(unset)* | Path to the finance LoRA adapter |
| `DEVICE` | auto | Force `cuda` or `cpu` |

## 3. Running the backend

```bash
export CLASSIFIER_DIR=models/mind_distilbert_classifier
export FINANCE_ADAPTER_DIR=models/qwen2.5_finance_lora
uvicorn app:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the OpenAPI UI.

## 4. Python API (programmatic use)

```python
from pipeline import NewsRecommendationPipeline, UserProfile

pipe = NewsRecommendationPipeline(
    classifier_dir="models/mind_distilbert_classifier",
    qwen_base_model="Qwen/Qwen2.5-0.5B-Instruct",
    category_adapters={"finance": "models/qwen2.5_finance_lora"},
    confidence_threshold=0.60,
)

alice = UserProfile("alice")

# ── 1. Ingest an article into the user's profile ─────────────────────────
vec = pipe.ingest(
    alice,
    title="Apple rose after reporting stronger services revenue",
    abstract="Apple shares climbed 3% after Q4 services revenue beat expectations...",
)
print(vec.category, vec.confidence, vec.mean_valence(), vec.mean_arousal())

# ── 2. Describe the user in natural language ─────────────────────────────
for bullet in pipe.describe_user(alice):
    print(bullet)
# ⇒ "You've been reading a lot of positive articles on Apple ..."

# ── 3. Rank a set of candidate articles by affective alignment ───────────
candidates = [
    {"id": "a1", "title": "Tesla shares fell...",
     "abstract": "Tesla shares fell after delivery guidance was cut..."},
    {"id": "a2", "title": "Brent crude gained...",
     "abstract": "Brent crude gained as supply risks..."},
]
ranked = pipe.recommend(alice, candidates, top_k=5)
for r in ranked:
    print(r["article_id"], r["score"], r["category"])
```

### Key objects

| Object | Purpose |
|---|---|
| `CategoryClassifier` | Load DistilBERT + label map; returns `{category, confidence, uncertain}` |
| `EntityAffectExtractor` | One Qwen expert (base or LoRA-adapter); `extract(article, num_entities)` |
| `EntityExtractorRegistry` | MoE router: `category -> extractor`, with a default fallback |
| `ArticleAffectVector` | Typed article record; `.as_vector()` → `[mean_valence, mean_arousal]` |
| `UserProfile` | Entity-level running statistics (valence, arousal, count) + category histogram |
| `Recommender` | Blend of `(affect_weight · affect_sim) + (entity_overlap_weight · entity_sim)` |
| `NewsRecommendationPipeline` | Facade combining all of the above |

## 5. HTTP API

All endpoints accept/return JSON.

### `GET /health`
```json
{"status": "ok"}
```

### `POST /classify` — stage 1 only
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

### `POST /process` — full pipeline on one article
```json
// request
{"title": "Tesla shares fell...", "abstract": "...", "id": "a1"}

// response
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

### `POST /ingest` — process + attribute to user
```json
{"user_id": "alice", "article": {"title": "...", "abstract": "..."}}
```
Response: `{ "article": { ... }, "profile_size": N }`.

### `POST /recommend`
```json
{
  "user_id": "alice",
  "top_k": 5,
  "candidates": [
    {"id": "a1", "title": "...", "abstract": "..."},
    {"id": "a2", "title": "...", "abstract": "..."}
  ]
}
```
Response: `{ "recommendations": [ {...vector..., "score": 0.84}, ... ] }`
sorted by descending score.

### `GET /users/{user_id}/summary`
```json
{
  "user_id": "alice",
  "history_size": 12,
  "top_entities": [["apple", 0.42, 0.38, 5], ...],
  "top_categories": [["finance", 9], ["sports", 3]],
  "descriptions": [
    "You've been reading a lot of positive articles on Apple ..."
  ],
  "profile_vector": [0.12, 0.41]
}
```

### `GET /users/{user_id}/profile` — full serialised profile (persistable).

### `DELETE /users/{user_id}` — reset.

## 6. Calling conventions & contracts

- **Sentiment labels**: lower-case strings `"positive" | "neutral" | "negative"`.
- **Valence**: float in `[-1.0, 1.0]` — clamped automatically in the extractor.
- **Arousal**: float in `[0.0, 1.0]` — clamped automatically in the extractor.
- **Category strings**: exactly one of the 11 classes the DistilBERT
  model was trained on (`autos`, `entertainment`, `finance`,
  `foodanddrink`, `health`, `lifestyle`, `movies`, `music`, `sports`,
  `travel`, `weather`), or `"uncertain"` when
  `top1_confidence < confidence_threshold`.
- **Uncertain routing**: when `category == "uncertain"`, the registry's
  **default** extractor (generic base Qwen) is used. Swap this for a
  human-review queue in production if desired.
- **Unknown categories**: any category without a registered adapter
  falls back to the default extractor rather than erroring.
- **Article identifiers**: if `id` / `article_id` is omitted, a UUID4 is
  generated.

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
routes to `sports`. No other code changes are needed.

## 8. Persistence

`UserProfile.to_dict()` and `UserProfile.from_dict()` round-trip the
full knowledge-graph state. Store in Redis / Postgres / a JSON column
keyed on `user_id`. Swap the in-memory `_users` dict in `app.py` for
your store of choice.

```python
import json, pathlib
pathlib.Path(f"profiles/{alice.user_id}.json").write_text(
    json.dumps(alice.to_dict())
)
```

## 9. Worked end-to-end example

```python
from pipeline import NewsRecommendationPipeline, UserProfile

pipe = NewsRecommendationPipeline(
    classifier_dir="models/mind_distilbert_classifier",
    category_adapters={"finance": "models/qwen2.5_finance_lora"},
)

bob = UserProfile("bob")

history = [
    ("JPMorgan faces regulatory probe",
     "The SEC opened a probe into JPMorgan's trading desk..."),
    ("JPMorgan profits slide 12% on weak loan demand",
     "Q3 profits at JPMorgan fell as loan growth stalled..."),
    ("JPMorgan warns on Q4 outlook",
     "The bank cut Q4 guidance citing weakening demand..."),
]
for title, abstract in history:
    pipe.ingest(bob, title=title, abstract=abstract)

print(pipe.describe_user(bob))
# ["You've been reading a lot of negative articles on Jpmorgan ..."]

candidates = [
    {"id": "c1", "title": "JPMorgan launches record buyback",
     "abstract": "JPMorgan announced a record $30B share buyback..."},
    {"id": "c2", "title": "Apple unveils M5 MacBook",
     "abstract": "Apple unveiled a new MacBook Pro..."},
    {"id": "c3", "title": "Fed cuts rates 25bps",
     "abstract": "The FOMC cut the federal funds rate..."},
]
for r in pipe.recommend(bob, candidates, top_k=3):
    print(f"{r['article_id']:4s} score={r['score']:+.3f} "
          f"val={r['mean_valence']:+.2f} cat={r['category']}")
```

## 10. Performance notes

- **Model load is the expensive step** — do it once at process start
  (`uvicorn --workers 1` if memory-bound; more workers replicates models).
- DistilBERT inference is ~10 ms/article on CPU; Qwen-0.5B is 1–3 s on
  CPU, ~200 ms on a T4.
- `process_article` is pure/stateless and safe to parallelise across
  requests.
- `UserProfile.update` is O(#entities); profile vectors are O(1) per
  read via stored running sums.

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `FileNotFoundError: Classifier directory not found` | Export the DistilBERT notebook artifact via `model.save_pretrained(dir); tokenizer.save_pretrained(dir)` and point `CLASSIFIER_DIR` at it. |
| `ImportError: peft is required ...` | `pip install peft` — only required when loading a LoRA adapter. |
| Extractor returns `entities: []` | Qwen didn't emit valid JSON. Increase `max_new_tokens`, lower the candidate article length, or retry with the base model (default fallback). |
| HTTP 400 "User has no reading history" | Call `/ingest` for that user at least once before `/recommend`, or seed the profile with editorial defaults. |
| Classifier always returns `"uncertain"` | Lower `confidence_threshold` (default 0.60) or retrain with more data for the confused classes. |

## 12. Frontend integration checklist

The frontend (not implemented in this repo) should:
1. Call `POST /ingest` every time a user reads an article (from click or scroll dwell).
2. Call `GET /users/{id}/summary` to render the "You've been reading a lot of …" banner.
3. Call `POST /recommend` with the candidate pool from your existing content service; render in descending `score` order.
4. Show chip colours using each entity's `sentiment` + `arousal`, mirroring `Entity Extraction_MSN/ux.py::entity_style` (already implemented there — reuse the CSS).
