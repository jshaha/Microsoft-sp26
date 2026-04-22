export const topTopics = [
  {
    id: 1,
    label: "Today's Money",
    value: "$53,000",
    delta: "+55%",
    up: true,
    icon: "💰",
    article: {
      title: "Fed holds rates steady as inflation cools to 2.4%",
      publisher: "Financial Times",
      image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&q=80",
      url: "https://ft.com",
    },
  },
  {
    id: 2,
    label: "Economy & Business",
    value: "+3,052",
    delta: "-14%",
    up: false,
    icon: "📄",
    article: {
      title: "Global supply chains show signs of strain after tariff hike",
      publisher: "Reuters",
      image: "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=80",
      url: "https://reuters.com",
    },
  },
  {
    id: 3,
    label: "Sports",
    value: "$173,000",
    delta: "+8%",
    up: true,
    icon: "🏅",
    article: {
      title: "NBA playoffs: Warriors edge Celtics in overtime thriller",
      publisher: "ESPN",
      image: "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=400&q=80",
      url: "https://espn.com",
    },
  },
];

export const headlines = [
  { id: 1, color: "#0067b8", text: "Starmer holds off from emergency measures", publisher: "BBC News", time: "22 DEC 7:20 PM" },
  { id: 2, color: "#c0392b", text: "DNA testing confirms Ted Bundy killed Utah teen", publisher: "Associated Press", time: "21 DEC 11:21 PM" },
  { id: 3, color: "#888", text: "U.S. lifts sanctions on acting Venezuelan President", publisher: "Reuters", time: "21 DEC 9:28 PM" },
  { id: 4, color: "#27a157", text: "Scientists announce breakthrough in Alzheimer's treatment", publisher: "Nature", time: "21 DEC 6:10 PM" },
];

export const collections = [
  { id: 1, name: "US Politics", topic: "Politics", count: 15, date: "Apr 14, 2026" },
  { id: 2, name: "AI & Big Tech", topic: "Technology", count: 11, date: "Apr 12, 2026" },
  { id: 3, name: "Markets This Week", topic: "Finance", count: 14, date: "Apr 10, 2026" },
  { id: 4, name: "Climate Policy", topic: "Science", count: 9, date: "Apr 7, 2026" },
  { id: 5, name: "Fed Rate Decisions", topic: "Finance", count: 8, date: "Apr 3, 2026" },
  { id: 6, name: "Health & Medicine", topic: "Science", count: 7, date: "Mar 31, 2026" },
];

export const biasData = {
  left: { sources: 145, lean: "Left-leaning" },
  center: { sources: 78, lean: "Center" },
  right: { sources: 22, lean: "Right-leaning" },
};

export const statsData = {
  articlesReadThisWeek: 247,
  articlesReadTotal: 32984,
  articlesShared: "2.42m",
  weekDelta: "+23",
};

export const mapMarkers = [
  {
    lat: 51.5, lng: -0.12, label: "London", stories: 3,
    articles: [
      { title: "London Underground to face four days of disruption due to RMT strike action", publisher: "Time Out London", url: "https://www.timeout.com/london/news/london-tube-and-train-strikes-spring-2026-full-list-of-dates-and-lines-impacted-how-to-travel-everything-you-need-to-know-march-april-may-031026" },
      { title: "Lady Mayor of the City of London warns against protectionism at diplomat gathering", publisher: "City of London", url: "https://news.cityoflondon.gov.uk/" },
      { title: "UK house prices fall in London and South East as mortgage approvals drop 4% year-on-year", publisher: "House of Commons Library", url: "https://commonslibrary.parliament.uk/research-briefings/sn02820/"},
    ]
  },
  {
    lat: 40.71, lng: -74.0, label: "New York", stories: 3,
    articles: [
      { title: "NYPD says subway is safe despite weekend violence as overall crime drops 1.5%", publisher: "Spectrum News NY1", url: "https://ny1.com/nyc/all-boroughs/morning-briefing/2026/04/15/morning-briefing--april-15--2026" },
      { title: "Northeast Supply Enhancement natural gas pipeline breaks ground in Brooklyn", publisher: "Spectrum News NY1", url: "https://ny1.com/nyc/all-boroughs/morning-briefing/2026/04/15/morning-briefing--april-15--2026" },
      { title: "Mayor Mamdani announces La Marqueta as first site for city's public grocery stores", publisher: "NYC.gov", url: "https://www.nyc.gov/main" },
    ]
  },
  {
    lat: 35.68, lng: 139.69, label: "Tokyo", stories: 2,
    articles: [
      { title: "Tokyo-based Dirbato acquires Singapore's Icon Consulting Group in international expansion", publisher: "Staffing Industry", url: "https://www.staffingindustry.com/news/global-daily-news/japans-dirbato-acquires-singapore-based-icon-consulting-group" },
      { title: "Flight disruptions across Asia: Tokyo among hardest hit hubs with 182 delays", publisher: "Travel and Tour World", url: "https://www.travelandtourworld.com/news/article/flights-cancelled-in-asia-as-thailand-japan-singapore-uae-india-and-indonesia-cancel-67-and-delay-1470-flights-disrupting-emirates-jal-ana-thai-airways-air-india-and-others-in-dubai-tokyo-bangkok-delh/" },
    ]
  },
  {
    lat: -23.55, lng: -46.63, label: "São Paulo", stories: 3,
    articles: [
      { title: "Ibovespa hits record 197,324 as dollar falls to R$5.01 — strongest real in two years", publisher: "The Rio Times", url: "https://www.riotimesonline.com/" },
      { title: "Brazil inflation forecast rises to 4.71%, above target ceiling for first time this cycle", publisher: "The Rio Times", url: "https://www.riotimesonline.com/" },
      { title: "São Paulo prepares to host WTM Latin America 2026 with global tourism industry focus", publisher: "Travel and Tour World", url: "https://www.travelandtourworld.com/news/article/brazil-travel-outlook-as-sao-paulo-prepares-to-host-wtm-latin-america-2026-with-global-industry-focus/" },
    ]
  },
  {
    lat: 28.61, lng: 77.2, label: "New Delhi", stories: 2,
    articles: [
      { title: "Delhi and Tokyo align on West Asia de-escalation and maritime security strategy", publisher: "Indian Defence News", url: "https://www.indiandefensenews.in/2026/04/new-strategic-synergy-delhi-and-tokyo.html" },
      { title: "Delhi airport among hardest hit as 176 flight delays reported across Indian hubs", publisher: "Travel and Tour World", url: "https://www.travelandtourworld.com/news/article/flights-cancelled-in-asia-as-thailand-japan-singapore-uae-india-and-indonesia-cancel-67-and-delay-1470-flights-disrupting-emirates-jal-ana-thai-airways-air-india-and-others-in-dubai-tokyo-bangkok-delh/" },
    ]
  },
  {
    lat: 1.35, lng: 103.82, label: "Singapore", stories: 2,
    articles: [
      { title: "Singapore Airlines suspends Dubai and Gulf routes as Middle East ceasefire holds", publisher: "Wego Travel Blog", url: "https://blog.wego.com/singapore-airlines-flight-status-2026/" },
      { title: "Commander of Royal Brunei Navy makes introductory visit to Singapore Ministry of Defence", publisher: "MINDEF Singapore", url: "https://www.mindef.gov.sg/news-and-events/latest-releases/15apr26-nr/" },
    ]
  },
];