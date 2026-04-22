import { useState } from "react";
import { collections } from "../data";
import { BookOpen, Share2, FolderOpen } from "lucide-react";

const weeklyData = [
  { week: "Mar 24", read: 18 },
  { week: "Mar 31", read: 22 },
  { week: "Apr 7",  read: 20 },
  { week: "Apr 14", read: 25 },
];

const maxRead = Math.max(...weeklyData.map(d => d.read));
const allTopics = ["All", ...new Set(collections.map(c => c.topic))];

export default function Collections() {
  const [tab, setTab] = useState("collections");
  const [activeFilter, setActiveFilter] = useState("All");

  const filtered = activeFilter === "All"
    ? collections
    : collections.filter(c => c.topic === activeFilter);

  return (
    <div style={s.card}>
      <div style={s.tabs}>
        <button style={{ ...s.tab, ...(tab === "collections" ? s.activeTab : {}) }} onClick={() => setTab("collections")}>
          <FolderOpen size={12} /> Collections
        </button>
        <button style={{ ...s.tab, ...(tab === "stats" ? s.activeTab : {}) }} onClick={() => setTab("stats")}>
          <BookOpen size={12} /> Your Stats
        </button>
      </div>

      {tab === "collections" && (
        <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
          <div style={s.filters}>
            {allTopics.map(t => (
              <button
                key={t}
                style={{ ...s.filterBtn, ...(activeFilter === t ? s.filterActive : {}) }}
                onClick={() => setActiveFilter(t)}
              >
                {t}
              </button>
            ))}
          </div>
          <div style={s.collList}>
            {filtered.map(c => (
              <div key={c.id} style={s.collItem}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={s.collName}>{c.name}</div>
                  <div style={s.collCount}>{c.count} articles</div>
                </div>
                <div style={s.collDate}>{c.date}</div>
              </div>
            ))}
          </div>
          <div style={s.moreBtn}>+ 5 more collections</div>
        </div>
      )}

      {tab === "stats" && (
        <div style={s.stats}>
          <div style={s.delta}>+23% from last week</div>
          <div style={s.statsGrid}>
            <div style={s.statBox}>
              <div style={{ ...s.statIcon, background: "#e8f0fe" }}><BookOpen size={13} color="#0067b8" /></div>
              <div style={s.statLabel}>Read this week</div>
              <div style={s.statVal}>25</div>
            </div>
            <div style={s.statBox}>
              <div style={{ ...s.statIcon, background: "#fdf0e8" }}><Share2 size={13} color="#e07b39" /></div>
              <div style={s.statLabel}>Shared this week</div>
              <div style={s.statVal}>6</div>
            </div>
            <div style={s.statBox}>
              <div style={{ ...s.statIcon, background: "#e8f0fe" }}><BookOpen size={13} color="#0067b8" /></div>
              <div style={s.statLabel}>Read total</div>
              <div style={s.statVal}>236</div>
            </div>
            <div style={s.statBox}>
              <div style={{ ...s.statIcon, background: "#fdf0e8" }}><Share2 size={13} color="#e07b39" /></div>
              <div style={s.statLabel}>Shared total</div>
              <div style={s.statVal}>40</div>
            </div>
          </div>
          <div style={s.chartLabel}>Articles read per week</div>
          <div style={s.chart}>
            {weeklyData.map((d, i) => (
              <div key={i} style={s.barCol}>
                <div style={s.barWrap}>
                  <div style={{ ...s.bar, height: `${(d.read / maxRead) * 100}%` }} />
                </div>
                <div style={s.barVal}>{d.read}</div>
                <div style={s.barWeek}>{d.week}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const s = {
  card: { background: "#fff", border: "1px solid #e8e4de", borderRadius: 14, padding: "13px 15px", display: "flex", flexDirection: "column", gap: 10 },
  tabs: { display: "flex", gap: 6, marginBottom: 2 },
  tab: { display: "flex", alignItems: "center", gap: 4, background: "#f3f0eb", border: "1px solid #e0dbd3", borderRadius: 20, padding: "4px 10px", fontSize: 11.5, color: "#666", cursor: "pointer", fontFamily: "inherit" },
  activeTab: { background: "#1a1a1a", color: "#fff", border: "1px solid #1a1a1a" },
  filters: { display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 8 },
  filterBtn: { background: "#f3f0eb", border: "1px solid #e0dbd3", borderRadius: 20, padding: "3px 9px", fontSize: 11, color: "#666", cursor: "pointer", fontFamily: "inherit" },
  filterActive: { background: "#1a1a1a", color: "#fff", border: "1px solid #1a1a1a" },
  collList: { display: "flex", flexDirection: "column", flex: 1 },
  collItem: { display: "flex", alignItems: "center", gap: 8, padding: "7px 0", borderBottom: "1px solid #f2ede8", cursor: "pointer" },
  collName: { fontSize: 12, fontWeight: 500, color: "#1a1a1a", marginBottom: 2 },
  collCount: { fontSize: 10.5, color: "#aaa" },
  collDate: { fontSize: 10.5, color: "#bbb", flexShrink: 0, marginLeft: 8 },
  moreBtn: { fontSize: 11.5, color: "#0067b8", textAlign: "center", padding: "10px 0 2px", cursor: "pointer", borderTop: "1px solid #f2ede8", marginTop: 4 },
  stats: { display: "flex", flexDirection: "column", gap: 10 },
  delta: { fontSize: 12, color: "#27a157", fontWeight: 500 },
  statsGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 },
  statBox: { background: "#f8f5f1", borderRadius: 10, padding: "9px 11px", display: "flex", flexDirection: "column", gap: 4 },
  statIcon: { width: 24, height: 24, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center" },
  statLabel: { fontSize: 10.5, color: "#999" },
  statVal: { fontSize: 18, fontWeight: 600, color: "#1a1a1a", letterSpacing: "-0.4px" },
  chartLabel: { fontSize: 11, color: "#aaa", marginTop: 4 },
  chart: { display: "flex", gap: 8, alignItems: "flex-end", height: 90 },
  barCol: { flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 3, height: "100%" },
  barWrap: { flex: 1, width: "100%", display: "flex", alignItems: "flex-end" },
  bar: { width: "100%", background: "#0067b8", borderRadius: "4px 4px 0 0", transition: "height .3s ease", minHeight: 4 },
  barVal: { fontSize: 10, color: "#555", fontWeight: 500 },
  barWeek: { fontSize: 9, color: "#bbb", textAlign: "center" },
};