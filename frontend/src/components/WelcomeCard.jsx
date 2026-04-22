export default function WelcomeCard() {
  const articleUrl = "https://www.nytimes.com/2026/04/15/business/stocks-record-iran-war.html";

  return (
    <a href={articleUrl} target="_blank" rel="noopener noreferrer" style={s.card}>
      <div style={s.art} />
      <div style={s.top}>
        <div style={s.sub}>Welcome back,</div>
        <div style={s.name}>Mark Johnson</div>
      </div>
      <div style={s.bottom}>
        <div style={s.body}>Stocks Hit Record High</div>
        <div style={s.link}>Pick up where you left off →</div>
      </div>
    </a>
  );
}

const s = {
  card:   { display: "flex", flexDirection: "column", justifyContent: "space-between", background: "#fff", border: "1px solid #e8e4de", borderRadius: 16, padding: 20, position: "relative", overflow: "hidden", minHeight: 200, cursor: "pointer", textDecoration: "none" },
  art:    { position: "absolute", right: 0, top: 0, bottom: 0, left: 0, backgroundImage: "linear-gradient(to right, #ffffff 0%, #ffffff 15%, transparent 65%), url('https://images.unsplash.com/photo-1606836591695-4d58a73eba1e?q=80&w=2671&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')", backgroundSize: "cover", backgroundPosition: "center" },
  top:    { position: "relative", zIndex: 1, maxWidth: "62%" },
  bottom: { position: "relative", zIndex: 1, maxWidth: "62%" },
  sub:    { fontSize: 13, color: "#aaa", marginBottom: 6, textDecoration: "none" },
  name:   { fontSize: 32, fontWeight: 700, color: "#1a1a1a", letterSpacing: "-1px", lineHeight: 1.1, textDecoration: "none" },
  body:   { fontSize: 12, color: "#888", lineHeight: 1.5, textDecoration: "none" },
  link:   { fontSize: 12, color: "#0067b8", marginTop: 5, textDecoration: "none" },
};