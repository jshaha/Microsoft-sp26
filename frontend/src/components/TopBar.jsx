import { useEffect, useRef, useState } from "react";
import { Search, Settings, Bell } from "lucide-react";
import api from "../api";
import { useUser } from "../UserContext";

export default function TopBar() {
  const { userId } = useUser();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const timer = useRef(null);
 
  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (!query.trim()) { setResults([]); setOpen(false); return; }
    timer.current = setTimeout(() => {
      api.search(query.trim(), 6)
        .then(r => { setResults(r?.results || []); setOpen(true); })
        .catch(() => { setResults([]); setOpen(false); });
    }, 200);
    return () => timer.current && clearTimeout(timer.current);
  }, [query]);
 
  return (
    <div style={s.bar}>
      <div style={s.breadcrumb}>Pages / <span style={{ color: "#555" }}>Dashboard</span></div>
      <div style={s.searchWrap}>
        <Search size={13} color="#bbb" strokeWidth={2} />
        <input
          style={s.input}
          placeholder="Search news…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => query && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
        />
        {open && results.length > 0 && (
          <div style={s.dropdown}>
            {results.map(r => (
              <a
                key={r.id}
                href={r.url || "#"}
                target="_blank"
                rel="noreferrer"
                style={s.drop}
                onMouseDown={() => api.ingestById(userId, r.id).catch(() => {})}
              >
                <div style={s.dropTitle}>{r.title}</div>
                <div style={s.dropMeta}>{r.publisher}</div>
              </a>
            ))}
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        <div style={s.iconBtn}><Settings size={14} color="#777" /></div>
        <div style={s.iconBtn}><Bell size={14} color="#777" /></div>
      </div>
    </div>
  );
}

const s = {
  bar: { display: "flex", alignItems: "center", gap: 12, padding: "10px 22px", borderBottom: "1px solid #e0dbd3", background: "#f3f0eb", flexShrink: 0, position: "relative" },
  breadcrumb: { fontSize: 12, color: "#999" },
  searchWrap: { marginLeft: "auto", display: "flex", alignItems: "center", gap: 7, background: "#fff", border: "1px solid #e0dbd3", borderRadius: 24, padding: "6px 13px", width: 260, position: "relative" },
  input: { background: "none", border: "none", outline: "none", color: "#333", fontSize: 13, fontFamily: "inherit", flex: 1, width: "100%" },
  dropdown: { position: "absolute", top: 38, left: 0, right: 0, background: "#fff", border: "1px solid #e0dbd3", borderRadius: 12, boxShadow: "0 4px 18px rgba(0,0,0,.08)", padding: 6, zIndex: 20 },
  drop: { display: "block", padding: "6px 9px", borderRadius: 8, textDecoration: "none", color: "#333" },
  dropTitle: { fontSize: 12, lineHeight: 1.35, marginBottom: 2 },
  dropMeta: { fontSize: 10, color: "#999" },
  iconBtn: { width: 30, height: 30, borderRadius: "50%", background: "transparent", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" },
};