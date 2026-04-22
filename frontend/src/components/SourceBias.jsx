import { biasData } from "../data";

export default function SourceBias() {
  const total = biasData.left.sources + biasData.center.sources + biasData.right.sources;

  return (
    <div style={s.card}>
      <div style={s.header}>
        <div style={s.title}>Source Political Diversity</div>
        <div style={s.subtitle}>Political leaning of your sources</div>
      </div>

      {/* Arc — left is blue, right is red */}
      <div style={s.gaugeWrap}>
        <svg width="160" height="90" viewBox="0 0 160 90" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="biasGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0067b8" />
              <stop offset="50%" stopColor="#9b59b6" />
              <stop offset="100%" stopColor="#c0392b" />
            </linearGradient>
          </defs>
          <path d="M16 82 A64 64 0 0 1 144 82" fill="none" stroke="#eee" strokeWidth="10" strokeLinecap="round" />
          <path d="M16 82 A64 64 0 0 1 144 82" fill="none" stroke="url(#biasGrad)" strokeWidth="10" strokeLinecap="round" />
          {/* needle */}
          <line
            x1="80" y1="82"
            x2={80 + 46 * Math.cos(Math.PI - (biasData.left.sources / total) * Math.PI)}
            y2={82 - 46 * Math.sin((biasData.left.sources / total) * Math.PI)}
            stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round"
          />
          <circle cx="80" cy="82" r="4" fill="#1a1a1a" />
        </svg>
      </div>

      <div style={s.rows}>
        {[
          { label: "Left", value: biasData.left.sources, color: "#0067b8", bg: "#e8f0fe" },
          { label: "Center", value: biasData.center.sources, color: "#9b59b6", bg: "#f5effe" },
          { label: "Right", value: biasData.right.sources, color: "#c0392b", bg: "#fdeeed" },
        ].map(r => (
          <div key={r.label} style={s.row}>
            <div style={{ ...s.rowDot, background: r.color }} />
            <div style={s.rowLabel}>{r.label}</div>
            <div style={s.rowBar}>
              <div style={{ ...s.rowFill, width: `${(r.value / total) * 100}%`, background: r.color }} />
            </div>
            <div style={s.rowVal}>{r.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const s = {
  card: { background: "#fff", border: "1px solid #e8e4de", borderRadius: 14, padding: "13px 15px" },
  header: { marginBottom: 8 },
  title: { fontSize: 13, fontWeight: 600, color: "#1a1a1a" },
  subtitle: { fontSize: 10.5, color: "#aaa", marginTop: 2 },
  gaugeWrap: { display: "flex", justifyContent: "center", margin: "4px 0 8px" },
  rows: { display: "flex", flexDirection: "column", gap: 6 },
  row: { display: "flex", alignItems: "center", gap: 7 },
  rowDot: { width: 8, height: 8, borderRadius: "50%", flexShrink: 0 },
  rowLabel: { fontSize: 11, color: "#555", width: 36 },
  rowBar: { flex: 1, height: 4, background: "#f0ece7", borderRadius: 2, overflow: "hidden" },
  rowFill: { height: "100%", borderRadius: 2 },
  rowVal: { fontSize: 11, color: "#888", width: 28, textAlign: "right" },
};