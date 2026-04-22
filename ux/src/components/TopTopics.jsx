import { topTopics } from "../data";
import { ExternalLink } from "lucide-react";

export default function TopTopics() {
  return (
    <div>
      <div style={s.label}>Your Top Topics</div>
      <div style={s.grid}>
        {topTopics.map(t => (
          <div key={t.id} style={s.card}>
            <div style={s.cardTop}>
              <div style={s.topicLabel}>{t.label}</div>
            </div>
            <a href={t.article.url} target="_blank" rel="noreferrer" style={s.articlePreview}>
              <img src={t.article.image} alt="" style={s.articleImg} />
              <div style={s.articleBody}>
                <div style={s.articlePublisher}>{t.article.publisher}</div>
                <div style={s.articleTitle}>{t.article.title}</div>
                <div style={s.articleLink}><ExternalLink size={10} /> Read article</div>
              </div>
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

const s = {
  label: { fontSize: 11, color: "#999", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 },
  grid: { display: "grid", gridTemplateColumns: "repeat(3, minmax(0,1fr))", gap: 10 },
  card: { background: "#fff", border: "1px solid #e8e4de", borderRadius: 14, padding: "13px 15px", display: "flex", flexDirection: "column", gap: 10 },
  cardTop: { display: "flex", alignItems: "center", gap: 10 },
  topicLabel: { fontSize: 13, fontWeight: 600, color: "#1a1a1a" },
  icon: { width: 34, height: 34, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, flexShrink: 0 },
  articlePreview: { display: "flex", gap: 9, background: "#f8f5f1", borderRadius: 10, padding: 9, textDecoration: "none", border: "1px solid #ede9e3" },
  articleImg: { width: 56, height: 56, borderRadius: 8, objectFit: "cover", flexShrink: 0 },
  articleBody: { flex: 1, minWidth: 0 },
  articlePublisher: { fontSize: 10, color: "#0067b8", fontWeight: 500, marginBottom: 3 },
  articleTitle: { fontSize: 11.5, color: "#333", lineHeight: 1.4, marginBottom: 4 },
  articleLink: { fontSize: 10, color: "#0067b8", display: "flex", alignItems: "center", gap: 3 },
};