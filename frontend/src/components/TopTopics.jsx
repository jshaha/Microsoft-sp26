import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";
import api from "../api";
import { useUser } from "../UserContext";
import { topTopics as FALLBACK } from "../data";

export default function TopTopics() {
  const { userId } = useUser();
  const [topics, setTopics] = useState(FALLBACK);
 
  useEffect(() => {
    let alive = true;
    api.topTopics(userId, 3)
      .then(r => { if (alive && r?.topics?.length) setTopics(r.topics); })
      .catch(() => {});
    return () => { alive = false; };
  }, [userId]);
 
  const onArticleClick = (articleId) => {
    if (articleId) api.ingestById(userId, articleId).catch(() => {});
  };
 
  return (
    <div>
      <div style={s.label}>Your Top Topics</div>
      <div style={s.grid}>
        {topics.map(t => (
          <div key={t.id} style={s.card}>
            <div style={s.cardTop}>
              <div style={s.topicLabel}>{t.label}</div>
              <div style={s.topicMeta}>
                {t.value}{t.delta && t.delta !== "—" ? ` · ${t.delta}` : ""}
                </div>
            </div>
            {t.article ? (
              <a
                href={t.article.url || "#"}
                target="_blank"
                rel="noreferrer"
                style={s.articlePreview}
                onClick={() => onArticleClick(t.article.id)}
              >
                {t.article.image && (
                  <img src={t.article.image} alt="" style={s.articleImg} />
                )}
                <div style={s.articleBody}>
                  <div
                    style={{
                      ...s.articlePublisher,
                      color: t.article.publisherColor || "#0067b8",
                    }}
                  >
                    {t.article.publisher}
                  </div>
                  <div style={s.articleTitle}>{t.article.title}</div>
                  <div style={s.articleLink}>
                    <ExternalLink size={10} /> Read article
                  </div>
                </div>
              </a>
            ) : (
              <div style={{ ...s.articlePreview, color: "#bbb", fontSize: 11 }}>
                No article available yet.
              </div>
            )}
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
  cardTop: { display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 10 },
  topicLabel: { fontSize: 13, fontWeight: 600, color: "#1a1a1a" },
  topicMeta: { fontSize: 10.5, color: "#999" },
  articlePreview: { display: "flex", gap: 9, background: "#f8f5f1", borderRadius: 10, padding: 9, textDecoration: "none", border: "1px solid #ede9e3" },
  articleImg: { width: 56, height: 56, borderRadius: 8, objectFit: "cover", flexShrink: 0 },
  articleBody: { flex: 1, minWidth: 0 },
  articlePublisher: { fontSize: 10, fontWeight: 500, marginBottom: 3 },
  articleTitle: { fontSize: 11.5, color: "#333", lineHeight: 1.4, marginBottom: 4 },
  articleLink: { fontSize: 10, color: "#0067b8", display: "flex", alignItems: "center", gap: 3 },
};