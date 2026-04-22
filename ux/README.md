# MSN News Dashboard — Microsoft Copilot UI Prototype

A high-fidelity UI prototype redesigning the MSN News integration within Microsoft Copilot, built as contract work for a Microsoft AI pitch. The goal was to modernize the news experience to drive engagement with a younger demographic through personalization, political transparency, and seamless AI-assisted news discovery.

---

## Background

MSN News reaches millions of users through Microsoft Copilot, but the existing interface lacks the personalization and transparency that younger audiences expect from a modern news product. This prototype reimagines the dashboard as an interactive, data-rich experience — giving users visibility into what they read, where news is breaking, and how their feed leans politically, all within the familiar Copilot aesthetic.

---

## Product Goals

- **Increase engagement** among 18–34 demographic through personalized, discovery-driven UX
- **Build trust** by surfacing political bias and source diversity transparently
- **Drive habitual use** through reading stats, saved collections, and mood-based discovery
- **Extend Copilot** as a natural interface for querying and exploring news

---

## Features

### Personalized Top Topics
Three topic cards tailored to the user's reading history. Each card surfaces a live article preview with image, publisher, headline, and a direct link — replacing static metrics with content that invites action.

### Top Headlines Today
Real, timestamped articles from today's news cycle. Each headline links directly to the source article and displays the publisher name styled in its brand font and color for instant recognition.

### Global News Map
An interactive Leaflet world map with story bubbles sized by article count per region. Clicking a bubble opens a panel of real articles from that location, each linking to the original source — turning geography into a navigation tool.

### Source Political Bias Arc
A left-to-right gradient arc visualizing the political lean of the user's sources, with a needle indicating current skew and a breakdown of left, center, and right source counts. Designed to give readers transparency rather than leaving algorithmic bias invisible.

### Collections
A saved articles system with folders organized by topic (Finance, Technology, Science, Politics). Users can filter collections by topic, see article counts, and view creation dates. A "+5 more collections" footer suggests depth without overwhelming the interface.

### Your Stats
A reading metrics panel showing articles read this week, articles shared this week, all-time totals, and a bar chart tracking weekly reading volume across the past month — designed to reward habitual engagement.

### Mood-Based Discovery
Two compact cards — Cheer Me Up and Feeling Lucky — for serendipitous, non-algorithmic news discovery based on user likes.

### Copilot Chat Bar
A full-width chat interface spanning the footer, allowing users to query the news naturally using Copilot — bridging passive reading with active AI-assisted exploration.

---

## Design Philosophy

The visual language mirrors Microsoft Copilot's warm off-white palette, rounded card system, and clean sans-serif typography. Every design decision prioritizes clarity and trust — publisher branding is explicit, political lean is visible, and reading behavior is surfaced rather than hidden. The experience is built to feel native to the Copilot ecosystem while pushing the product forward for a new generation of news consumers.

---

## Stack

| Layer | Technology |
|---|---|
| Framework | React + Vite |
| Mapping | Leaflet / React-Leaflet |
| Icons | Lucide React |
| Styling | Inline React styles |
| Deployment | Vercel |

---

## Live Demo

[https://msn-news-dashboard.vercel.app](https://msn-news-dashboard.vercel.app)

---

## Repository

[https://github.com/anoushkashah/msn-dashboard-prototype](https://github.com/anoushkashah/msn-dashboard-prototype)

---

## Getting Started

```bash
git clone https://github.com/anoushkashah/msn-dashboard-prototype.git
cd msn-dashboard-prototype
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Project Structure
- `src/`
  - `main.jsx` — Entry point
  - `App.jsx` — Root layout and grid
  - `data.js` — Mock data (articles, collections, map markers)
  - `index.css` — Global reset
  - `components/`
    - `Sidebar.jsx` — Navigation sidebar
    - `TopBar.jsx` — Search and breadcrumb bar
    - `TopTopics.jsx` — Personalized topic cards with article previews
    - `WelcomeCard.jsx` — User welcome hero card
    - `Headlines.jsx` — Top headlines with publisher branding
    - `MoodCards.jsx` — Cheer me up / Feeling lucky
    - `Collections.jsx` — Saved collections with stats tab
    - `SourceBias.jsx` — Political bias arc visualization
    - `GlobalMap.jsx` — Interactive world news map
    - `ChatBar.jsx` — Copilot chat footer
---

## Deployment

Deployed on Vercel with automatic redeployment on every push to `main`.

```bash
git add .
git commit -m "your update"
git push
```
