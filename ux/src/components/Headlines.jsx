const headlines = [
  {
    id: 1,
    text: "DOJ moves to dismiss Jan. 6 convictions against 12 former Proud Boys and Oath Keepers",
    publisher: "CBS News",
    time: "APR 15, 2026",
    url: "https://www.cbsnews.com/news/doj-moves-dismiss-jan-6-convictions-proud-boys-oath-keepers-seditious-conspiracy/",
    publisherColor: "#fff",
    publisherBg: "#003876",
    publisherFont: "Arial, sans-serif",
  },
  {
    id: 2,
    text: "Super Typhoon Sinlaku barrels over remote U.S. islands in the Pacific",
    publisher: "CBS News",
    time: "APR 15, 2026",
    url: "https://www.cbsnews.com/news/super-typhoon-sinlaku-remote-us-islands-pacific/",
    publisherColor: "#fff",
    publisherBg: "#003876",
    publisherFont: "Arial, sans-serif",
  },
  {
    id: 3,
    text: "Drug overdose deaths are plummeting in the U.S. in ways never seen before",
    publisher: "NPR",
    time: "APR 14, 2026",
    url: "https://www.npr.org/sections/news",
    publisherColor: "#fff",
    publisherBg: "#222",
    publisherFont: "Georgia, serif",
  },
  {
    id: 4,
    text: "US blockade of Strait of Hormuz: Iran ceasefire talks could resume before deadline",
    publisher: "CNN",
    time: "APR 14, 2026",
    url: "https://www.cnn.com/2026/04/14/world/live-news/iran-war-blockade-us-trump",
    publisherColor: "#fff",
    publisherBg: "#cc0000",
    publisherFont: "Arial, sans-serif",
  },
];

export default function Headlines() {
  return (
    <div style={s.card}>
      <div style={s.title}>Top Headlines Today</div>
      {headlines.map(h => (
        <a key={h.id} href={h.url} target="_blank" rel="noreferrer" style={s.item}>
          <div style={s.text}>{h.text}</div>
          <div style={s.bottom}>
            <span style={{
              ...s.publisherBadge,
              background: h.publisherBg,
              color: h.publisherColor,
              fontFamily: h.publisherFont,
            }}>
              {h.publisher}
            </span>
            <span style={s.time}>{h.time}</span>
          </div>
        </a>
      ))}
    </div>
  );
}

const s = {
  card: { background: "#fff", border: "1px solid #e8e4de", borderRadius: 16, padding: 16, display: "flex", flexDirection: "column", gap: 2 },
  title: { fontSize: 13.5, fontWeight: 600, color: "#1a1a1a", marginBottom: 8 },
  item: { display: "flex", flexDirection: "column", padding: "8px 0", borderBottom: "1px solid #f2ede8", textDecoration: "none", cursor: "pointer" },
  text: { fontSize: 12.5, color: "#333", lineHeight: 1.4, marginBottom: 5 },
  bottom: { display: "flex", alignItems: "center", gap: 8 },
  publisherBadge: { fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 4, letterSpacing: "0.02em" },
  time: { fontSize: 10, color: "#bbb" },
};