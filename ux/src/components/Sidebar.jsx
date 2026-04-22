import { LayoutDashboard, Rss, Search, Bookmark, Bell, DollarSign, Clock, Home, FolderOpen } from "lucide-react";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", id: "dashboard" },
  { icon: Rss, label: "My Feed", id: "feed" },
  { icon: Search, label: "Discover", id: "discover" },
  { icon: Bookmark, label: "Saved", id: "saved" },
  { icon: Bell, label: "Alerts", id: "alerts" },
];

const topicItems = [
  { icon: DollarSign, label: "Finance", id: "finance" },
  { icon: Clock, label: "Sports", id: "sports" },
  { icon: Home, label: "Politics", id: "politics" },
  { icon: FolderOpen, label: "Collections", id: "collections" },
];

const recent = ["Fed Rate Decision Analysis", "Creative Sleep-Friendly Nighttime…", "Arctic Ice Record Low 2024"];

export default function Sidebar({ active, setActive }) {
  return (
    <aside style={s.sidebar}>
      <div style={s.logo}>MSN News</div>

      {navItems.map(({ icon: Icon, label, id }) => (
        <div key={id} style={{ ...s.navItem, ...(active === id ? s.activeItem : {}) }} onClick={() => setActive(id)}>
          <Icon size={15} strokeWidth={1.6} style={{ opacity: 0.7, flexShrink: 0 }} />
          {label}
        </div>
      ))}

      <hr style={s.divider} />
      <div style={s.section}>Topics</div>

      {topicItems.map(({ icon: Icon, label, id }) => (
        <div key={id} style={{ ...s.navItem, ...(active === id ? s.activeItem : {}) }} onClick={() => setActive(id)}>
          <Icon size={15} strokeWidth={1.6} style={{ opacity: 0.7, flexShrink: 0 }} />
          {label}
        </div>
      ))}

      <hr style={s.divider} />
      <div style={s.section}>Recent</div>
      {recent.map((r, i) => (
        <div key={i} style={s.recentItem}>{r}</div>
      ))}

      <div style={s.footer}>
        <div style={s.signInNote}>Sign in to upload files, use Voice without limits, and build memory.</div>
        <button style={s.signInBtn}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
          </svg>
          Sign in
        </button>
      </div>
    </aside>
  );
}

const s = {
  sidebar: { width: 210, minWidth: 210, background: "#ede9e3", borderRight: "1px solid #e0dbd3", display: "flex", flexDirection: "column", padding: "16px 0", height: "100vh", overflow: "hidden" },
  logo: { fontSize: 16, fontWeight: 600, color: "#1a1a1a", padding: "4px 20px 18px", letterSpacing: "-0.3px" },
  navItem: { display: "flex", alignItems: "center", gap: 10, padding: "8px 20px", cursor: "pointer", color: "#555", fontSize: 13, transition: "background .12s" },
  activeItem: { background: "#ddd8d0", color: "#000", fontWeight: 500 },
  divider: { border: "none", borderTop: "1px solid #d8d3cc", margin: "8px 0" },
  section: { fontSize: 10, color: "#999", textTransform: "uppercase", letterSpacing: ".07em", padding: "5px 20px 2px" },
  recentItem: { padding: "6px 20px", fontSize: 12, color: "#777", cursor: "pointer", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  footer: { marginTop: "auto", padding: "12px 20px", borderTop: "1px solid #d8d3cc" },
  signInNote: { fontSize: 11, color: "#999", textAlign: "center", marginBottom: 8, lineHeight: 1.45 },
  signInBtn: { width: "100%", background: "#1a1a1a", color: "#fff", border: "none", borderRadius: 24, padding: 9, fontSize: 13, fontFamily: "inherit", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 7 },
};