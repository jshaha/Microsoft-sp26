import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import { X } from "lucide-react";
import "leaflet/dist/leaflet.css";
import api from "../api";
import { useUser } from "../UserContext";
import { mapMarkers as FALLBACK } from "../data";

function badgeStyle(article) {
  return {
    background: article.bg || "#eee",
    color: article.color || "#333",
    fontFamily: article.font || "Arial, sans-serif",
  };
}

export default function GlobalMap() {
  const { userId } = useUser();
  const [markers, setMarkers] = useState(FALLBACK);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let alive = true;
    api.mapMarkers()
      .then(r => { if (alive && r?.markers?.length) setMarkers(r.markers); })
      .catch(() => {});
    return () => { alive = false; };
  }, []);
 
  const onArticleClick = (article) => {
    if (article.id) api.ingestById(userId, article.id).catch(() => {});
  };

  return (
    <div style={s.card}>
      <div style={s.header}>
        <div style={s.title}>Global View</div>
        <div style={s.meta}>{markers.length} regions this month</div>
      </div>
      <div style={s.mapWrap}>
        <MapContainer
          center={[20, 10]}
          zoom={2}
          style={{ height: "100%", width: "100%", borderRadius: 10 }}
          scrollWheelZoom={false}
          zoomControl={true}
          attributionControl={false}
        >
          <TileLayer url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png" />
          {markers.map((m, i) => (
            <CircleMarker
              key={i}
              center={[m.lat, m.lng]}
              radius={(m.articles?.length || 1) * 4 + 5}
              pathOptions={{ color: "#0067b8", fillColor: "#0067b8", fillOpacity: 0.6, weight: 1.5 }}
              eventHandlers={{ click: () => setSelected(m) }}
            >
              <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
                <strong>{m.label}</strong> · {m.articles?.length || 0} articles
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {selected && (
        <div style={s.panel}>
          <div style={s.panelHeader}>
            <div style={s.panelTitle}>{selected.label}</div>
            <div style={s.panelCount}>{selected.articles?.length || 0} articles</div>
            <button style={s.closeBtn} onClick={() => setSelected(null)}>
              <X size={13} />
            </button>
          </div>
          <div style={s.articleList}>
            {(selected.articles || []).map((a, i) => (
              <a
                key={i}
                href={a.url}
                target="_blank"
                rel="noreferrer"
                style={s.articleItem}
                onClick={() => onArticleClick(a)}
              >
                <div style={s.articleTitle}>{a.title}</div>
                <div style={s.articleBottom}>
                  <span style={{ ...s.publisherBadge, ...badgeStyle(a) }}>
                    {a.publisher}
                  </span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const s = {
  card: { background: "#fff", border: "1px solid #e8e4de", borderRadius: 14, padding: "13px 15px", display: "flex", flexDirection: "column", flex: 1 },
  header: { display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 },
  title: { fontSize: 13, fontWeight: 600, color: "#1a1a1a" },
  meta: { fontSize: 11, color: "#27a157" },
  mapWrap: { flex: 1, minHeight: 200, borderRadius: 10, overflow: "hidden" },
  panel: { marginTop: 10, background: "#fff", borderRadius: 12, border: "1px solid #e8e4de", overflow: "hidden" },
  panelHeader: { display: "flex", alignItems: "center", gap: 6, padding: "10px 12px", borderBottom: "1px solid #f2ede8" },
  panelTitle: { fontSize: 13, fontWeight: 600, color: "#1a1a1a", flex: 1 },
  panelCount: { fontSize: 11, color: "#0067b8" },
  closeBtn: { background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", color: "#aaa", padding: 0 },
  articleList: { display: "flex", flexDirection: "column" },
  articleItem: { display: "flex", flexDirection: "column", gap: 5, padding: "9px 12px", borderBottom: "1px solid #f2ede8", textDecoration: "none", cursor: "pointer", background: "#fff" },
  articleTitle: { fontSize: 12, color: "#333", lineHeight: 1.4 },
  articleBottom: { display: "flex", alignItems: "center" },
  publisherBadge: { fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 3, letterSpacing: "0.02em" },
};