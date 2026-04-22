import { useState } from "react";
import { Plus, Mic, Send, ChevronDown, ExternalLink } from "lucide-react";
import api from "../api";
import { useUser } from "../UserContext";

export default function ChatBar() {
  const { userId } = useUser();
  const [msg, setMsg] = useState("");
  const [reply, setReply] = useState(null);
  const [articles, setArticles] = useState([]);
  const [busy, setBusy] = useState(false);
 
  const submit = async () => {
    const q = msg.trim();
    if (!q || busy) return;
    setBusy(true);
    setMsg("");
    try {
      const res = await api.chat(userId, q);
      setReply(res.reply);
      setArticles(res.articles || []);
    } catch {
      setReply("Chat is offline — start the backend with `uvicorn app:app` to use Copilot.");
      setArticles([]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={s.bar}>
    {reply && (
        <div style={s.reply}>
          <div style={s.replyText}>{reply}</div>
          {articles.map(a => (
            <a key={a.id} href={a.url} target="_blank" rel="noreferrer" style={s.replyItem}
               onClick={() => api.ingestById(userId, a.id).catch(() => {})}>
              <ExternalLink size={10} />
              <span style={s.replyTitle}>{a.title}</span>
              <span style={s.replyPub}>{a.publisher}</span>
            </a>
          ))}
        </div>
      )}
      <div style={s.inner}>
        <div style={s.inputRow}>
          <input
            style={s.input}
            placeholder="Message MSN News…"
            value={msg}
            onChange={e => setMsg(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") submit(); }}
            disabled={busy}
          />
          {msg && (
            <button style={s.sendBtn} onClick={submit} disabled={busy}>
              <Send size={14} color="#fff" />
            </button>
          )}
        </div>
        <div style={s.actions}>
          <div style={s.iconBtn}><Plus size={15} color="#666" /></div>
          <div style={s.modelBtn}>
            Smart <ChevronDown size={12} />
          </div>
          <div style={s.spacer} />
          <div style={s.iconBtn}><Mic size={15} color="#666" /></div>
        </div>
      </div>
    </div>
  );
}

const s = {
  bar: { borderTop: "1px solid #e0dbd3", padding: "12px 22px 14px", background: "#f3f0eb", flexShrink: 0 },
  reply: { background: "#fff", border: "1px solid #e0dbd3", borderRadius: 14, padding: "10px 14px", marginBottom: 8, boxShadow: "0 2px 8px rgba(0,0,0,.04)" },
  replyText: { fontSize: 12.5, color: "#333", marginBottom: 6 },
  replyItem: { display: "flex", alignItems: "center", gap: 6, padding: "4px 0", textDecoration: "none", color: "#0067b8", fontSize: 11.5 },
  replyTitle: { flex: 1, color: "#333" },
  replyPub: { fontSize: 10, color: "#999" },
  inner: { background: "#fff", border: "1px solid #e0dbd3", borderRadius: 20, padding: "10px 16px", boxShadow: "0 2px 8px rgba(0,0,0,.05)", width: "100%" },
  inputRow: { display: "flex", alignItems: "center", gap: 8, marginBottom: 8 },
  input: { flex: 1, background: "none", border: "none", outline: "none", fontSize: 13.5, fontFamily: "inherit", color: "#333" },
  sendBtn: { width: 28, height: 28, borderRadius: "50%", background: "#1a1a1a", border: "none", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 },
  actions: { display: "flex", alignItems: "center", gap: 7 },
  iconBtn: { width: 28, height: 28, borderRadius: "50%", background: "#f3f0eb", border: "1px solid #ddd", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" },
  modelBtn: { background: "#f3f0eb", border: "1px solid #ddd", borderRadius: 20, padding: "4px 11px", fontSize: 12, color: "#555", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontFamily: "inherit" },
  spacer: { flex: 1 },
};