import { useState } from "react";
import api from "../api";
import { useUser } from "../UserContext";

const IMAGES = {
  cheer_me_up: "https://images.unsplash.com/photo-1590698933947-a202b069a861?q=80&w=1035&auto=format&fit=crop",
  feeling_lucky: "https://plus.unsplash.com/premium_photo-1664392434825-eb95db0931d4?q=80&w=1650&auto=format&fit=crop",
};

export default function MoodCards() {
  const { userId } = useUser();
  const [hovered, setHovered] = useState(null);

  const handleClick = async (mode) => {
    try {
      const res = await api.mood(userId, mode);
      if (res?.article?.url) {
        api.ingestById(userId, res.article.id).catch(() => {});
        window.open(res.article.url, "_blank");
        return;
      }
    } catch { /* backend offline — fall through */ }
    // graceful fallback: if backend is unreachable, open Positive News
    window.open(
      mode === "cheer_me_up"
        ? "https://www.positive.news/"
        : "https://www.npr.org/",
      "_blank",
    );
  };

  return (
    <div style={s.col}>
      {[
        { mode: "cheer_me_up",  label: "Cheer Me Up",      sub: "Happy News · Based on likes" },
        { mode: "feeling_lucky", label: "I'm Feeling Lucky", sub: "Surprise Me! · Based on likes" },
      ].map(({ mode, label, sub }) => (
        <div
          key={mode}
          style={{ ...s.card, background: hovered === mode ? "#f5f2ee" : "#fff" }}
          onClick={() => handleClick(mode)}
          onMouseEnter={() => setHovered(mode)}
          onMouseLeave={() => setHovered(null)}
        >
          <div style={s.row}>
            <div style={s.text}>
              <div style={s.label}>{label}</div>
              <div style={s.sub}>{sub}</div>
            </div>
            <img src={IMAGES[mode]} alt={label} style={s.photo} />
          </div>
        </div>
      ))}
    </div>
  );
}

const s = {
  col: { display: "flex", flexDirection: "column", gap: 8 },
  card: { border: "1px solid #e8e4de", borderRadius: 12, padding: "9px 12px", cursor: "pointer", flex: 1, transition: "background 0.15s" },
  row: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 },
  text: { display: "flex", flexDirection: "column", flex: 1 },
  label: { fontSize: 12, fontWeight: 500, color: "#1a1a1a" },
  sub: { fontSize: 10, color: "#bbb", marginBottom: 4 },
  photo: { width: 48, height: 48, borderRadius: 8, objectFit: "cover", flexShrink: 0 },
};