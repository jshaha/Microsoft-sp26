"""
In-memory article corpus.
 
The dashboard (headlines, top-topics, global map, mood cards) reads from
this store. In production this would be a content-service client; for the
prototype we ship a seeded corpus that mirrors the frontend mock data so
the UI is never empty before the model warms up.
 
Each record carries:
    - id, title, abstract, url, publisher, category
    - published_at (ISO string)
    - region, lat, lng  (optional — populates the Global Map panel)
    - image            (optional — TopTopics / Mood cards)
    - valence, arousal (optional — filled by the pipeline on /process or
                        /ingest, used by mood filtering)
    - mood             (optional hint: "cheer" | "lucky" — seeded only)
"""
 
from __future__ import annotations
 
import copy
import random
import threading
from typing import Dict, List, Optional, Tuple, Iterable
 
 
_SEED_ARTICLES: List[Dict] = [
    # ── Top topic featured cards ──────────────────────────────────────────
    {
        "id": "a-ft-fed-rates",
        "title": "Fed holds rates steady as inflation cools to 2.4%",
        "abstract": "Federal Reserve officials voted to hold the target range unchanged as headline CPI cooled to 2.4% year over year, signalling a data-dependent path for the rest of the cycle.",
        "url": "https://ft.com",
        "publisher": "Financial Times",
        "category": "finance",
        "published_at": "2026-04-21T14:00:00Z",
        "image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&q=80",
        "valence": 0.25, "arousal": 0.35,
    },
    {
        "id": "a-reuters-supply",
        "title": "Global supply chains show signs of strain after tariff hike",
        "abstract": "Exporters reported longer lead times and rising freight premiums after the latest round of tariff increases, according to a Reuters survey of shippers.",
        "url": "https://reuters.com",
        "publisher": "Reuters",
        "category": "finance",
        "published_at": "2026-04-20T09:30:00Z",
        "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=80",
        "valence": -0.35, "arousal": 0.55,
    },
    {
        "id": "a-espn-nba",
        "title": "NBA playoffs: Warriors edge Celtics in overtime thriller",
        "abstract": "Stephen Curry hit a deep three in overtime as the Warriors narrowly beat the Celtics 118-115 in Game 4 of the NBA playoffs.",
        "url": "https://espn.com",
        "publisher": "ESPN",
        "category": "sports",
        "published_at": "2026-04-21T04:15:00Z",
        "image": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=400&q=80",
        "valence": 0.55, "arousal": 0.75,
    },
 
    # ── Top headlines ─────────────────────────────────────────────────────
    {
        "id": "a-cbs-jan6",
        "title": "DOJ moves to dismiss Jan. 6 convictions against 12 former Proud Boys and Oath Keepers",
        "abstract": "The Department of Justice filed motions to vacate seditious-conspiracy convictions against twelve defendants connected to the January 6 Capitol attack.",
        "url": "https://www.cbsnews.com/news/doj-moves-dismiss-jan-6-convictions-proud-boys-oath-keepers-seditious-conspiracy/",
        "publisher": "CBS News",
        "category": "news",
        "published_at": "2026-04-15T18:00:00Z",
        "valence": -0.2, "arousal": 0.6,
    },
    {
        "id": "a-cbs-typhoon",
        "title": "Super Typhoon Sinlaku barrels over remote U.S. islands in the Pacific",
        "abstract": "Category-5 Super Typhoon Sinlaku made landfall on several remote Pacific territories overnight, damaging infrastructure across multiple atolls.",
        "url": "https://www.cbsnews.com/news/super-typhoon-sinlaku-remote-us-islands-pacific/",
        "publisher": "CBS News",
        "category": "weather",
        "published_at": "2026-04-15T12:00:00Z",
        "valence": -0.5, "arousal": 0.75,
    },
    {
        "id": "a-npr-overdose",
        "title": "Drug overdose deaths are plummeting in the U.S. in ways never seen before",
        "abstract": "CDC provisional data show drug overdose deaths dropped for a fifth consecutive quarter — the steepest sustained decline on record.",
        "url": "https://www.npr.org/sections/news",
        "publisher": "NPR",
        "category": "health",
        "published_at": "2026-04-14T15:00:00Z",
        "valence": 0.4, "arousal": 0.45,
    },
    {
        "id": "a-cnn-hormuz",
        "title": "US blockade of Strait of Hormuz: Iran ceasefire talks could resume before deadline",
        "abstract": "Negotiators said talks to restore a ceasefire around the Strait of Hormuz could reconvene this week as the US blockade enters a third day.",
        "url": "https://www.cnn.com/2026/04/14/world/live-news/iran-war-blockade-us-trump",
        "publisher": "CNN",
        "category": "news",
        "published_at": "2026-04-14T20:00:00Z",
        "valence": -0.4, "arousal": 0.7,
    },
 
    # ── Welcome-card "pick up where you left off" ─────────────────────────
    {
        "id": "a-nyt-stocks-record",
        "title": "Stocks Hit Record High",
        "abstract": "Wall Street closed at a fresh all-time high as investors cheered resilient earnings and softer inflation data despite geopolitical tension.",
        "url": "https://www.nytimes.com/2026/04/15/business/stocks-record-iran-war.html",
        "publisher": "The New York Times",
        "category": "finance",
        "published_at": "2026-04-15T21:00:00Z",
        "image": "https://images.unsplash.com/photo-1606836591695-4d58a73eba1e?q=80&w=1200",
        "valence": 0.5, "arousal": 0.55,
    },
 
    # ── Cheer-me-up (Positive News) ───────────────────────────────────────
    {
        "id": "a-posi-kingbirds",
        "title": "King of the birds set to return to England's skies",
        "abstract": "Conservationists announced a successful release of a breeding pair of white-tailed eagles in southern England.",
        "url": "https://www.positive.news/environment/king-of-the-birds-set-to-return-to-englands-skies/",
        "publisher": "Positive News", "category": "lifestyle",
        "published_at": "2026-04-18T10:00:00Z",
        "valence": 0.8, "arousal": 0.4, "mood": "cheer",
    },
    {
        "id": "a-posi-community-energy",
        "title": "What does the new £1bn investment in community energy really mean",
        "abstract": "A £1bn commitment from the UK government could mean local co-operatives own nearly a fifth of new wind and solar builds by 2030.",
        "url": "https://www.positive.news/environment/energy/what-does-the-new-1bn-investment-in-community-energy-really-mean/",
        "publisher": "Positive News", "category": "lifestyle",
        "published_at": "2026-04-17T09:30:00Z",
        "valence": 0.7, "arousal": 0.35, "mood": "cheer",
    },
    {
        "id": "a-posi-good-15",
        "title": "Good news stories from week 15 of 2026",
        "abstract": "Our weekly round-up: from a reef restoration breakthrough in Queensland to a record year for urban tree-planting in São Paulo.",
        "url": "https://www.positive.news/society/good-news-stories-from-week-15-of-2026/",
        "publisher": "Positive News", "category": "lifestyle",
        "published_at": "2026-04-13T08:00:00Z",
        "valence": 0.75, "arousal": 0.3, "mood": "cheer",
    },
    {
        "id": "a-posi-cancer",
        "title": "Cancer deaths fall to historic low in the UK — this is probably why",
        "abstract": "Age-standardised UK cancer mortality reached its lowest point on record, driven by screening uptake and targeted therapies.",
        "url": "https://www.positive.news/lifestyle/health/cancer-deaths-fall-to-historic-low-in-uk-this-is-probably-why/",
        "publisher": "Positive News", "category": "health",
        "published_at": "2026-04-12T07:45:00Z",
        "valence": 0.65, "arousal": 0.4, "mood": "cheer",
    },
    {
        "id": "a-posi-good-13",
        "title": "Good news stories from week 13 of 2026",
        "abstract": "From a major renewable-energy milestone to a community-led rewilding project in the Scottish Highlands.",
        "url": "https://www.positive.news/society/good-news-stories-from-week-13-of-2026/",
        "publisher": "Positive News", "category": "lifestyle",
        "published_at": "2026-03-30T08:30:00Z",
        "valence": 0.7, "arousal": 0.3, "mood": "cheer",
    },
 
    # ── Feeling lucky (serendipitous) ─────────────────────────────────────
    {
        "id": "a-nyt-trump-live",
        "title": "Live updates from the White House",
        "abstract": "Rolling coverage of the day's announcements from the administration.",
        "url": "https://www.nytimes.com/live/2026/04/15/us/trump-news",
        "publisher": "The New York Times", "category": "news",
        "published_at": "2026-04-15T16:00:00Z",
        "valence": 0.0, "arousal": 0.55, "mood": "lucky",
    },
    {
        "id": "a-ap-marcos",
        "title": "Philippine president shares exercise routine amid health speculation",
        "abstract": "An AP feature takes readers inside the unlikely morning routine of a sitting head of state.",
        "url": "https://apnews.com/article/philippine-marcos-health-exercises-10041aaa1dca49fa2ba29e4da7fd9334",
        "publisher": "Associated Press", "category": "lifestyle",
        "published_at": "2026-04-08T09:00:00Z",
        "valence": 0.15, "arousal": 0.3, "mood": "lucky",
    },
    {
        "id": "a-npr-robowar",
        "title": "Inside RoboWar: the underground league where hobbyist robots duel",
        "abstract": "NPR visits a converted warehouse in Detroit where engineers unwind by sending 50-pound bots into the arena.",
        "url": "https://www.npr.org/2026/03/13/nx-s1-5680260/robowar-robot-battle-detroit",
        "publisher": "NPR", "category": "entertainment",
        "published_at": "2026-03-13T14:00:00Z",
        "valence": 0.35, "arousal": 0.7, "mood": "lucky",
    },
    {
        "id": "a-npr-dude",
        "title": "The surfer origin of 'dude'",
        "abstract": "An etymological romp through decades of slang, from mid-century cowboys to The Big Lebowski.",
        "url": "https://www.npr.org/2025/07/30/nx-s1-5482984/dude-big-lebowski-surfer-origin-etymology",
        "publisher": "NPR", "category": "entertainment",
        "published_at": "2025-07-30T13:00:00Z",
        "valence": 0.5, "arousal": 0.3, "mood": "lucky",
    },
    {
        "id": "a-npr-capuchin",
        "title": "Baby monkey kidnappings: a strange new 'culture' among capuchins",
        "abstract": "Primatologists document an unusual pattern of infant abductions between neighbouring capuchin groups.",
        "url": "https://www.npr.org/2025/05/19/nx-s1-5395983/baby-monkey-kidnappings-capuchin-howler-culture",
        "publisher": "NPR", "category": "news",
        "published_at": "2025-05-19T10:00:00Z",
        "valence": -0.15, "arousal": 0.5, "mood": "lucky",
    },
 
    # ── Global map: London ───────────────────────────────────────────────
    {
        "id": "a-london-tube",
        "title": "London Underground to face four days of disruption due to RMT strike action",
        "abstract": "Tube drivers plan a four-day strike this spring, with TfL warning of severe disruption on major lines.",
        "url": "https://www.timeout.com/london/news/london-tube-and-train-strikes-spring-2026-full-list-of-dates-and-lines-impacted-how-to-travel-everything-you-need-to-know-march-april-may-031026",
        "publisher": "Time Out London", "category": "travel",
        "published_at": "2026-04-11T08:00:00Z",
        "region": "London", "lat": 51.5, "lng": -0.12,
        "valence": -0.35, "arousal": 0.55,
    },
    {
        "id": "a-london-mayor",
        "title": "Lady Mayor of the City of London warns against protectionism at diplomat gathering",
        "abstract": "At her annual diplomats' dinner the Lady Mayor called for an open-trade agenda and warned against rising protectionism.",
        "url": "https://news.cityoflondon.gov.uk/",
        "publisher": "City of London", "category": "news",
        "published_at": "2026-04-10T19:00:00Z",
        "region": "London", "lat": 51.5, "lng": -0.12,
        "valence": 0.1, "arousal": 0.35,
    },
    {
        "id": "a-london-housing",
        "title": "UK house prices fall in London and South East as mortgage approvals drop 4% year-on-year",
        "abstract": "ONS and Bank of England figures show softening prices and weaker mortgage approvals concentrated in London and the South East.",
        "url": "https://commonslibrary.parliament.uk/research-briefings/sn02820/",
        "publisher": "House of Commons Library", "category": "finance",
        "published_at": "2026-04-09T11:00:00Z",
        "region": "London", "lat": 51.5, "lng": -0.12,
        "valence": -0.25, "arousal": 0.5,
    },
 
    # ── Global map: New York ────────────────────────────────────────────
    {
        "id": "a-ny-subway",
        "title": "NYPD says subway is safe despite weekend violence as overall crime drops 1.5%",
        "abstract": "The commissioner cited a 1.5% year-on-year drop in overall subway crime even as two high-profile incidents raised concern.",
        "url": "https://ny1.com/nyc/all-boroughs/morning-briefing/2026/04/15/morning-briefing--april-15--2026",
        "publisher": "Spectrum News NY1", "category": "news",
        "published_at": "2026-04-15T07:00:00Z",
        "region": "New York", "lat": 40.71, "lng": -74.0,
        "valence": -0.2, "arousal": 0.6,
    },
    {
        "id": "a-ny-pipeline",
        "title": "Northeast Supply Enhancement natural gas pipeline breaks ground in Brooklyn",
        "abstract": "Construction crews broke ground on a contested segment of the NESE pipeline beneath Brooklyn's waterfront.",
        "url": "https://ny1.com/nyc/all-boroughs/morning-briefing/2026/04/15/morning-briefing--april-15--2026",
        "publisher": "Spectrum News NY1", "category": "news",
        "published_at": "2026-04-15T08:00:00Z",
        "region": "New York", "lat": 40.71, "lng": -74.0,
        "valence": 0.0, "arousal": 0.5,
    },
    {
        "id": "a-ny-grocery",
        "title": "Mayor Mamdani announces La Marqueta as first site for city's public grocery stores",
        "abstract": "NYC's first public grocery store will anchor the East Harlem landmark under the mayor's new food-access initiative.",
        "url": "https://www.nyc.gov/main",
        "publisher": "NYC.gov", "category": "news",
        "published_at": "2026-04-14T16:00:00Z",
        "region": "New York", "lat": 40.71, "lng": -74.0,
        "valence": 0.35, "arousal": 0.4,
    },
 
    # ── Global map: Tokyo ───────────────────────────────────────────────
    {
        "id": "a-tokyo-dirbato",
        "title": "Tokyo-based Dirbato acquires Singapore's Icon Consulting Group in international expansion",
        "abstract": "The acquisition gives Japan's Dirbato a staffing footprint across Southeast Asia.",
        "url": "https://www.staffingindustry.com/news/global-daily-news/japans-dirbato-acquires-singapore-based-icon-consulting-group",
        "publisher": "Staffing Industry", "category": "finance",
        "published_at": "2026-04-12T03:00:00Z",
        "region": "Tokyo", "lat": 35.68, "lng": 139.69,
        "valence": 0.4, "arousal": 0.5,
    },
    {
        "id": "a-tokyo-flights",
        "title": "Flight disruptions across Asia: Tokyo among hardest-hit hubs with 182 delays",
        "abstract": "Tokyo recorded 182 flight delays overnight as regional air traffic disruption spread across Asia.",
        "url": "https://www.travelandtourworld.com/news/article/flights-cancelled-in-asia-as-thailand-japan-singapore-uae-india-and-indonesia-cancel-67-and-delay-1470-flights-disrupting-emirates-jal-ana-thai-airways-air-india-and-others-in-dubai-tokyo-bangkok-delh/",
        "publisher": "Travel and Tour World", "category": "travel",
        "published_at": "2026-04-11T12:00:00Z",
        "region": "Tokyo", "lat": 35.68, "lng": 139.69,
        "valence": -0.4, "arousal": 0.65,
    },
 
    # ── Global map: São Paulo ───────────────────────────────────────────
    {
        "id": "a-sao-ibovespa",
        "title": "Ibovespa hits record 197,324 as dollar falls to R$5.01 — strongest real in two years",
        "abstract": "Brazilian equities set a new record high as the real strengthened to its best level since 2024.",
        "url": "https://www.riotimesonline.com/",
        "publisher": "The Rio Times", "category": "finance",
        "published_at": "2026-04-10T22:00:00Z",
        "region": "São Paulo", "lat": -23.55, "lng": -46.63,
        "valence": 0.6, "arousal": 0.55,
    },
    {
        "id": "a-sao-inflation",
        "title": "Brazil inflation forecast rises to 4.71%, above target ceiling for first time this cycle",
        "abstract": "Central bank expectations surveys push year-end inflation above the 4.5% ceiling.",
        "url": "https://www.riotimesonline.com/",
        "publisher": "The Rio Times", "category": "finance",
        "published_at": "2026-04-09T13:00:00Z",
        "region": "São Paulo", "lat": -23.55, "lng": -46.63,
        "valence": -0.3, "arousal": 0.5,
    },
    {
        "id": "a-sao-tourism",
        "title": "São Paulo prepares to host WTM Latin America 2026 with global tourism industry focus",
        "abstract": "The World Travel Market Latin America edition returns to São Paulo with more than 8,000 participants.",
        "url": "https://www.travelandtourworld.com/news/article/brazil-travel-outlook-as-sao-paulo-prepares-to-host-wtm-latin-america-2026-with-global-industry-focus/",
        "publisher": "Travel and Tour World", "category": "travel",
        "published_at": "2026-04-07T10:00:00Z",
        "region": "São Paulo", "lat": -23.55, "lng": -46.63,
        "valence": 0.45, "arousal": 0.4,
    },
 
    # ── Global map: New Delhi ───────────────────────────────────────────
    {
        "id": "a-delhi-tokyo",
        "title": "Delhi and Tokyo align on West Asia de-escalation and maritime security strategy",
        "abstract": "Indo-Japanese foreign ministries issued a joint statement on West Asia and maritime security.",
        "url": "https://www.indiandefensenews.in/2026/04/new-strategic-synergy-delhi-and-tokyo.html",
        "publisher": "Indian Defence News", "category": "news",
        "published_at": "2026-04-11T09:30:00Z",
        "region": "New Delhi", "lat": 28.61, "lng": 77.2,
        "valence": 0.2, "arousal": 0.45,
    },
    {
        "id": "a-delhi-flights",
        "title": "Delhi airport among hardest hit as 176 flight delays reported across Indian hubs",
        "abstract": "IGI airport recorded 176 delays as weather and ATC congestion rippled across Indian hubs.",
        "url": "https://www.travelandtourworld.com/news/article/flights-cancelled-in-asia-as-thailand-japan-singapore-uae-india-and-indonesia-cancel-67-and-delay-1470-flights-disrupting-emirates-jal-ana-thai-airways-air-india-and-others-in-dubai-tokyo-bangkok-delh/",
        "publisher": "Travel and Tour World", "category": "travel",
        "published_at": "2026-04-11T12:00:00Z",
        "region": "New Delhi", "lat": 28.61, "lng": 77.2,
        "valence": -0.35, "arousal": 0.55,
    },
 
    # ── Global map: Singapore ───────────────────────────────────────────
    {
        "id": "a-sg-sq",
        "title": "Singapore Airlines suspends Dubai and Gulf routes as Middle East ceasefire holds",
        "abstract": "SQ suspended Dubai and Gulf services in a precautionary move while the regional ceasefire holds.",
        "url": "https://blog.wego.com/singapore-airlines-flight-status-2026/",
        "publisher": "Wego Travel Blog", "category": "travel",
        "published_at": "2026-04-13T05:00:00Z",
        "region": "Singapore", "lat": 1.35, "lng": 103.82,
        "valence": -0.3, "arousal": 0.5,
    },
    {
        "id": "a-sg-mindef",
        "title": "Commander of Royal Brunei Navy makes introductory visit to Singapore Ministry of Defence",
        "abstract": "Bilateral defence ties were reaffirmed at the SAF's Changi Naval Base visit.",
        "url": "https://www.mindef.gov.sg/news-and-events/latest-releases/15apr26-nr/",
        "publisher": "MINDEF Singapore", "category": "news",
        "published_at": "2026-04-15T11:00:00Z",
        "region": "Singapore", "lat": 1.35, "lng": 103.82,
        "valence": 0.15, "arousal": 0.3,
    },
]
 
 
class ArticleStore:
    """Thread-safe in-memory article corpus."""
 
    def __init__(self, seed: Optional[Iterable[Dict]] = None):
        self._lock = threading.RLock()
        self._articles: Dict[str, Dict] = {}
        for a in (seed if seed is not None else _SEED_ARTICLES):
            self.upsert(a)
 
    # ------------------------------------------------------------------
    def upsert(self, article: Dict) -> Dict:
        """Insert or overwrite an article by id."""
        with self._lock:
            record = copy.deepcopy(article)
            if not record.get("id"):
                raise ValueError("article must have an 'id'")
            self._articles[record["id"]] = record
            return record
 
    def get(self, article_id: str) -> Optional[Dict]:
        with self._lock:
            a = self._articles.get(article_id)
            return copy.deepcopy(a) if a else None
 
    def all(self) -> List[Dict]:
        with self._lock:
            return [copy.deepcopy(a) for a in self._articles.values()]
 
    def by_category(self, category: str) -> List[Dict]:
        category = (category or "").lower()
        return [a for a in self.all() if a.get("category", "").lower() == category]
 
    def by_mood(self, mood: str) -> List[Dict]:
        """Return articles seeded with the requested mood hint, OR derive
        from valence (cheer = valence ≥ 0.45 & arousal ≤ 0.6; lucky = any)."""
        mood = (mood or "").lower()
        all_rows = self.all()
        tagged = [a for a in all_rows if a.get("mood", "").lower() == mood]
        if tagged:
            return tagged
        if mood == "cheer" or mood == "cheer_me_up":
            return [
                a for a in all_rows
                if a.get("valence", 0.0) >= 0.45 and a.get("arousal", 0.0) <= 0.65
            ]
        if mood == "lucky" or mood == "feeling_lucky":
            return all_rows
        return all_rows
 
    def by_region(self) -> Dict[str, List[Dict]]:
        """Group articles by region; only returns articles with lat/lng."""
        grouped: Dict[str, List[Dict]] = {}
        for a in self.all():
            region = a.get("region")
            if not region or a.get("lat") is None or a.get("lng") is None:
                continue
            grouped.setdefault(region, []).append(a)
        return grouped
 
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Naive case-insensitive substring search over title+abstract."""
        q = (query or "").strip().lower()
        if not q:
            return []
        hits: List[Tuple[int, Dict]] = []
        for a in self.all():
            hay = (a.get("title", "") + " " + a.get("abstract", "")).lower()
            if q in hay:
                score = hay.count(q) * 10 + (1 if q in a.get("title", "").lower() else 0)
                hits.append((score, a))
        hits.sort(key=lambda t: t[0], reverse=True)
        return [a for _score, a in hits[:limit]]
 
    def sample(self, n: int, exclude_ids: Optional[Iterable[str]] = None,
               seed: Optional[int] = None) -> List[Dict]:
        exclude = set(exclude_ids or [])
        pool = [a for a in self.all() if a.get("id") not in exclude]
        if seed is not None:
            random.Random(seed).shuffle(pool)
        else:
            random.shuffle(pool)
        return pool[: max(0, n)]
 
    def apply_affect(self, article_id: str, valence: float, arousal: float) -> None:
        """Record affect scores on a stored article (called after /process)."""
        with self._lock:
            a = self._articles.get(article_id)
            if a is None:
                return
            a["valence"] = float(valence)
            a["arousal"] = float(arousal)
 
    def __len__(self) -> int:
        with self._lock:
            return len(self._articles)