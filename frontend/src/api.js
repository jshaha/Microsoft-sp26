// Thin fetch wrapper around the MSN sentiment-aware backend (app.py).
//
// During local dev, vite.config.js proxies `/api/*` -> http://localhost:8000,
// so component code always calls relative URLs. Override at build time with:
//
//     VITE_API_BASE=https://api.example.com npm run build
//
// Every endpoint here mirrors a handler in app.py. On network failure the
// helpers throw; components catch and fall back to cached/mock data so the
// dashboard is never blank.
 
const BASE = import.meta.env.VITE_API_BASE || "/api";
 
async function request(path, { method = "GET", body, params } = {}) {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) url.searchParams.set(k, v);
    }
  }
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url.toString().replace(window.location.origin, ""), opts);
  if (!res.ok) {
    throw new Error(`${method} ${path} → ${res.status} ${await res.text()}`);
  }
  return res.json();
}
 
export const api = {
  health:        ()                      => request("/health"),
 
  // Dashboard composite views
  welcome:       (userId)                => request("/feed/welcome", { params: { user_id: userId } }),
  headlines:     (userId, n = 4)         => request("/feed/headlines", { params: { user_id: userId, n } }),
  topTopics:     (userId, k = 3)         => request("/feed/top-topics", { params: { user_id: userId, k } }),
  mood:          (userId, mode)          => request("/feed/mood", { method: "POST", body: { user_id: userId, mode } }),
  stats:         (userId)                => request(`/users/${encodeURIComponent(userId)}/stats`),
  bias:          (userId)                => request(`/users/${encodeURIComponent(userId)}/bias`),
  summary:       (userId)                => request(`/users/${encodeURIComponent(userId)}/summary`),
 
  // Collections
  listCollections:   (userId, topic)         => request(`/users/${encodeURIComponent(userId)}/collections`, { params: { topic } }),
  createCollection:  (userId, name, topic)   => request(`/users/${encodeURIComponent(userId)}/collections`, { method: "POST", body: { name, topic } }),
  addToCollection:   (userId, cid, articleId) => request(`/users/${encodeURIComponent(userId)}/collections/${cid}/articles`, { method: "POST", body: { article_id: articleId } }),
 
  // Behavioural events
  ingestById:    (userId, articleId)    => request("/ingest/by-id", { method: "POST", body: { user_id: userId, article_id: articleId } }),
  share:         (userId, articleId)    => request(`/users/${encodeURIComponent(userId)}/shares`, { method: "POST", body: { article_id: articleId } }),
 
  // Map / search / chat
  mapMarkers:    ()                      => request("/map/markers"),
  search:        (q, k = 10)             => request("/search", { params: { q, k } }),
  chat:          (userId, message)       => request("/chat", { method: "POST", body: { user_id: userId, message } }),
 
  // Full ML pipeline (used only by advanced flows)
  classify:      (title, abstract, topK = 3) =>
                   request("/classify", { method: "POST", body: { title, abstract, top_k: topK } }),
  process:       (article) =>
                   request("/process", { method: "POST", body: article }),
  recommend:     (userId, candidates, topK = 10) =>
                   request("/recommend", { method: "POST", body: { user_id: userId, candidates, top_k: topK } }),
};
 
export default api;