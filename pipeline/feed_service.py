"""
Dashboard-facing facade.
 
The web dashboard (frontend/) pulls every view from a small set of
composite endpoints. Each of those endpoints is a thin wrapper around a
method on `FeedService`, which in turn orchestrates:
 
    - the NewsRecommendationPipeline (classifier + MoE extractor + recommender)
    - the in-memory ArticleStore
    - the UserProfile knowledge graph
    - publisher metadata for branding and political-lean attribution
 
If the heavy Qwen / DistilBERT models haven't been loaded (e.g. during
local UI development), `FeedService` still works end-to-end by falling
back to seeded valence/arousal on the article records and category
heuristics — the dashboard is never empty.
"""
 
from __future__ import annotations
 
import random
from typing import Dict, List, Optional, Any, TYPE_CHECKING
 
from .article_store import ArticleStore
from .user_profile import UserProfile
from .publishers import publisher_style, publisher_lean, PUBLISHER_META
 
if TYPE_CHECKING:
    from .pipeline import NewsRecommendationPipeline  # noqa: F401
 
 
TOPIC_ICONS = {
    "finance": "💰",
    "sports": "🏅",
    "politics": "🗳",
    "technology": "💻",
    "science": "🔬",
    "health": "🩺",
    "entertainment": "🎬",
    "travel": "✈",
    "weather": "⛈",
    "lifestyle": "🌿",
    "news": "📰",
    "foodanddrink": "🍽",
    "movies": "🎞",
    "music": "🎵",
    "autos": "🚗",
}
 
# Human-readable labels for the three Top-Topic cards.
TOPIC_LABEL = {
    "finance": "Today's Money",
    "news": "Economy & Business",
    "sports": "Sports",
    "politics": "Politics Watch",
    "technology": "Tech Pulse",
    "health": "Well-being",
    "entertainment": "Entertainment",
    "travel": "Travel Desk",
    "lifestyle": "Lifestyle",
    "weather": "Weather",
    "movies": "Movies",
    "music": "Music",
    "foodanddrink": "Food & Drink",
    "autos": "Autos",
    "science": "Science",
}
 
 
class FeedService:
 
    def __init__(
        self,
        pipeline: "Optional[NewsRecommendationPipeline]",
        store: ArticleStore,
    ):
        self.pipeline = pipeline
        self.store = store
 
    # ─────────────────────────────────────────────────────────── ingest
    def ingest_url(self, user: UserProfile, article_id: str,
                   ts: Optional[str] = None) -> Dict[str, Any]:
        """
        Record that a user read a stored article. If the ML pipeline is
        loaded, run full affect extraction; otherwise fold the seeded
        affect values into the knowledge graph directly.
        """
        article = self.store.get(article_id)
        if article is None:
            raise KeyError(f"Unknown article: {article_id}")
 
        publisher = article.get("publisher")
 
        if self.pipeline is not None:
            vec = self.pipeline.ingest(
                user,
                title=article["title"],
                abstract=article.get("abstract", ""),
                article_id=article_id,
            )
            # Attribute publisher (pipeline.ingest doesn't know about it)
            if publisher:
                user.record_publisher(publisher)
            # Re-record so last_read_article_id has the store id
            self.store.apply_affect(
                article_id, vec.mean_valence(), vec.mean_arousal()
            )
            return vec.to_dict()
 
        # ── Fallback path (no ML models loaded) ──
        user.history_ids.append(article_id)
        cat = article.get("category", "uncertain")
        user._category_counts[cat] = user._category_counts.get(cat, 0) + 1
        user.record_publisher(publisher or "")
        user.record_read(article_id, ts=ts)
        return {
            "article_id": article_id,
            "title": article["title"],
            "category": cat,
            "confidence": 1.0,
            "entities": [],
            "mean_valence": article.get("valence", 0.0),
            "mean_arousal": article.get("arousal", 0.0),
            "abstract": article.get("abstract", ""),
        }
 
    # ─────────────────────────────────────────────────────────── views
    def welcome(self, user: UserProfile) -> Dict[str, Any]:
        """Data for the WelcomeCard ("Pick up where you left off")."""
        last_id = user.last_read_article_id
        last = self.store.get(last_id) if last_id else None
        if last is None:
            last = self.store.get("a-nyt-stocks-record")  # seeded default
        return {
            "user_id": user.user_id,
            "display_name": user.display_name,
            "last_article": last,
        }
 
    def headlines(self, user: Optional[UserProfile] = None,
                  n: int = 4) -> List[Dict[str, Any]]:
        """Top headlines with publisher branding for the Headlines card."""
        # Sort by publish time (recent first); if user is present, bump
        # articles whose publisher the user already reads.
        pool = self.store.all()
        pool.sort(key=lambda a: a.get("published_at", ""), reverse=True)
        if user is not None and user._publisher_counts:
            pool.sort(
                key=lambda a: user._publisher_counts.get(a.get("publisher"), 0),
                reverse=True,
            )
        out = []
        for a in pool[:n]:
            meta = publisher_style(a.get("publisher", ""))
            out.append({
                "id": a["id"],
                "text": a["title"],
                "url": a.get("url", ""),
                "publisher": a.get("publisher", ""),
                "time": a.get("published_at", ""),
                "publisherBg": meta["bg"],
                "publisherColor": meta["color"],
                "publisherFont": meta["font"],
            })
        return out
 
    def top_topics(self, user: UserProfile,
                   k: int = 3) -> List[Dict[str, Any]]:
        """Top k categories from the user's history, each with a featured article."""
        # Prefer user's actual top categories; pad with sensible defaults.
        defaults = ["finance", "news", "sports"]
        ranked = [c for c, _ in user.top_categories(k)] or []
        for d in defaults:
            if len(ranked) >= k:
                break
            if d not in ranked:
                ranked.append(d)
        ranked = ranked[:k]
 
        cards: List[Dict[str, Any]] = []
        for i, cat in enumerate(ranked, start=1):
            bucket = self.store.by_category(cat)
            bucket.sort(key=lambda a: a.get("published_at", ""), reverse=True)
            featured = bucket[0] if bucket else None
 
            # "Value" = articles read in that category; "delta" = vs. last week
            count = user._category_counts.get(cat, 0)
            last_week = max(0, user.reads_since(days=14) - user.reads_since(days=7))
            delta_pct = 0
            if last_week > 0:
                this_week = user.reads_since(days=7)
                delta_pct = int(round((this_week - last_week) / last_week * 100))
 
            if featured is not None:
                meta = publisher_style(featured.get("publisher", ""))
                article_block = {
                    "id": featured["id"],
                    "title": featured["title"],
                    "publisher": featured.get("publisher", ""),
                    "image": featured.get("image", ""),
                    "url": featured.get("url", ""),
                    "publisherColor": meta["color"],
                    "publisherBg": meta["bg"],
                    "publisherFont": meta["font"],
                }
            else:
                article_block = None
 
            cards.append({
                "id": i,
                "category": cat,
                "label": TOPIC_LABEL.get(cat, cat.title()),
                "icon": TOPIC_ICONS.get(cat, "📰"),
                "value": f"{count} articles",
                "delta": f"{delta_pct:+d}%" if delta_pct else "—",
                "up": delta_pct >= 0,
                "article": article_block,
            })
        return cards
 
    def mood(self, user: UserProfile, mode: str) -> Dict[str, Any]:
        """Return one article matching the requested mood.
 
        `mode` in {"cheer_me_up", "feeling_lucky"}.
        """
        key = (mode or "").lower()
        pool = self.store.by_mood(key)
        read_ids = {ev["article_id"] for ev in user.reading_events}
        fresh = [a for a in pool if a["id"] not in read_ids] or pool
        if not fresh:
            return {"article": None}
        choice = random.choice(fresh)
        meta = publisher_style(choice.get("publisher", ""))
        return {
            "mode": key,
            "article": {
                **choice,
                "publisherBg": meta["bg"],
                "publisherColor": meta["color"],
                "publisherFont": meta["font"],
            },
        }
 
    def stats(self, user: UserProfile) -> Dict[str, Any]:
        weekly = user.weekly_read_counts(n_weeks=4)
        this_week = user.reads_since(days=7)
        prev_week = max(0, user.reads_since(days=14) - this_week)
        delta_pct = 0
        if prev_week > 0:
            delta_pct = int(round((this_week - prev_week) / prev_week * 100))
        return {
            "articles_read_this_week": this_week,
            "articles_read_total": len(user.reading_events),
            "articles_shared_this_week": user.shares_since(days=7),
            "articles_shared_total": len(user.shares),
            "week_delta_pct": delta_pct,
            "weekly_chart": [
                {"week": label, "read": count} for label, count in weekly
            ],
        }
 
    def source_bias(self, user: UserProfile) -> Dict[str, Any]:
        """Aggregate political lean of the user's sources."""
        buckets = {"left": 0, "center": 0, "right": 0}
        for publisher, count in user._publisher_counts.items():
            lean = publisher_lean(publisher)
            buckets[lean] = buckets.get(lean, 0) + count
        total = sum(buckets.values())
        if total == 0:
            # Seed with corpus-level totals so the arc is never empty
            for meta in PUBLISHER_META.values():
                buckets[meta["lean"]] += 1
            total = sum(buckets.values())
        return {
            "left":   {"sources": buckets["left"],   "lean": "Left-leaning"},
            "center": {"sources": buckets["center"], "lean": "Center"},
            "right":  {"sources": buckets["right"],  "lean": "Right-leaning"},
            "total": total,
        }
 
    def map_markers(self) -> List[Dict[str, Any]]:
        """Regional bubbles for the GlobalMap component."""
        grouped = self.store.by_region()
        markers: List[Dict[str, Any]] = []
        for region, articles in grouped.items():
            lat = articles[0]["lat"]
            lng = articles[0]["lng"]
            markers.append({
                "label": region,
                "lat": lat,
                "lng": lng,
                "stories": len(articles),
                "articles": [
                    {
                        "title": a["title"],
                        "publisher": a.get("publisher", ""),
                        "url": a.get("url", ""),
                        **{k: v for k, v in publisher_style(a.get("publisher", "")).items()
                           if k in ("bg", "color", "font")},
                    }
                    for a in articles
                ],
            })
        return markers
 
    # ─────────────────────────────────────────────────────────── collections
    def list_collections(self, user: UserProfile,
                         topic: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = user.collections_by_topic(topic)
        out: List[Dict[str, Any]] = []
        for c in rows:
            out.append({
                "id": c["id"],
                "name": c["name"],
                "topic": c["topic"],
                "count": len(c["article_ids"]),
                "date": c["created_at"][:10],
            })
        return out
 
    def create_collection(self, user: UserProfile,
                          name: str, topic: str) -> Dict[str, Any]:
        cid = user.add_collection(name=name, topic=topic)
        return user.collections[cid]
 
    # ─────────────────────────────────────────────────────────── chat + search
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.store.search(query, limit=limit)
 
    def chat(self, user: UserProfile, message: str) -> Dict[str, Any]:
        """
        Copilot chat bar handler — keeps the conversation in-scope of the
        user's news graph. If the ML pipeline is available we route the
        question through the classifier to pick a category, then surface
        matching articles; otherwise we fall back to substring search.
        """
        msg = (message or "").strip()
        if not msg:
            return {"reply": "Ask me about today's news.", "articles": []}
 
        category = None
        if self.pipeline is not None:
            try:
                route = self.pipeline.classifier.route(msg, "")
                category = route.get("category")
            except Exception:
                category = None
 
        pool = (
            self.store.by_category(category)
            if category and category != "uncertain"
            else []
        )
        if not pool:
            pool = self.store.search(msg, limit=20)
        if not pool:
            # Token-wise fallback — try each meaningful word.
            tokens = [
                t.strip(".,?!") for t in (msg.lower().split())
                if len(t) >= 3 and t not in {
                    "what", "when", "where", "which", "whose", "about",
                    "tell", "show", "give", "find", "with", "this", "that",
                    "from", "happening", "going",
                }
            ]
            seen = set()
            for tok in tokens:
                for a in self.store.search(tok, limit=5):
                    if a["id"] in seen:
                        continue
                    seen.add(a["id"])
                    pool.append(a)
                    if len(pool) >= 5:
                        break
                if len(pool) >= 5:
                    break
        articles = pool[:5]
 
        descriptions = user.describe(top_n=2)
        hint = (" " + descriptions[0]) if descriptions else ""
        reply = (
            f"I found {len(articles)} article{'s' if len(articles) != 1 else ''} "
            f"related to your question"
            f"{' in ' + category if category and category != 'uncertain' else ''}."
            + hint
        )
        return {
            "reply": reply,
            "category": category,
            "articles": [
                {
                    "id": a["id"],
                    "title": a["title"],
                    "publisher": a.get("publisher", ""),
                    "url": a.get("url", ""),
                }
                for a in articles
            ],
        }