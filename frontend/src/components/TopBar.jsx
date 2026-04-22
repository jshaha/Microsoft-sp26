import { useState } from "react";
import { Search, Settings, Bell } from "lucide-react";

export default function TopBar() {
  const [query, setQuery] = useState("");
  return (
    <div style={s.bar}>
      <div style={s.breadcrumb}>Pages / <span style={{ color: "#555" }}>Dashboard</span></div>
      <div style={s.searchWrap}>
        <Search size={13} color="#bbb" strokeWidth={2} />
        <input style={s.input} placeholder="Search news…" value={query} onChange={e => setQuery(e.target.value)} />
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        <div style={s.iconBtn}><Settings size={14} color="#777" /></div>
        <div style={s.iconBtn}><Bell size={14} color="#777" /></div>
      </div>
    </div>
  );
}

const s = {
  bar: { display: "flex", alignItems: "center", gap: 12, padding: "10px 22px", borderBottom: "1px solid #e0dbd3", background: "#f3f0eb", flexShrink: 0 },
  breadcrumb: { fontSize: 12, color: "#999" },
  searchWrap: { marginLeft: "auto", display: "flex", alignItems: "center", gap: 7, background: "#fff", border: "1px solid #e0dbd3", borderRadius: 24, padding: "6px 13px", width: 220 },
  input: { background: "none", border: "none", outline: "none", color: "#333", fontSize: 13, fontFamily: "inherit", flex: 1, width: "100%" },
  iconBtn: { width: 30, height: 30, borderRadius: "50%", background: "transparent", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" },
};