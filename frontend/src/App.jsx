import { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import TopTopics from "./components/TopTopics";
import WelcomeCard from "./components/WelcomeCard";
import Headlines from "./components/Headlines";
import MoodCards from "./components/MoodCards";
import Collections from "./components/Collections";
import SourceBias from "./components/SourceBias";
import GlobalMap from "./components/GlobalMap";
import ChatBar from "./components/ChatBar";

export default function App() {
  const [active, setActive] = useState("dashboard");

  return (
    <div style={s.app}>
      <Sidebar active={active} setActive={setActive} />

      <div style={s.main}>
        <TopBar />

        <div style={s.content}>
          {/* Row 1 — topic stats */}
          <TopTopics />

          {/* Row 2 — welcome + headlines */}
          <div style={s.midRow}>
            <WelcomeCard />
            <Headlines />
          </div>

          {/* Row 3 — mood | collections | source bias + global map */}
          <div style={s.bottomRow}>

            {/* Left: mood (half size) + source bias */}
            <div style={s.leftCol}>
              <MoodCards />
              <SourceBias />
            </div>

            {/* Center: collections / stats */}
            <Collections />

            {/* Right: global map (bigger) */}
            <div style={s.mapCol}>
              <GlobalMap />
            </div>

          </div>
        </div>

        <ChatBar />
      </div>
    </div>
  );
}

const s = {
  app: { display: "flex", width: "100vw", height: "100vh", background: "#f3f0eb", overflow: "hidden" },
  main: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0, height: "100vh", overflow: "hidden" },
  content: { flex: 1, overflowY: "auto", padding: "14px 22px", display: "flex", flexDirection: "column", gap: 12, minHeight: 0 },
  midRow: { display: "grid", gridTemplateColumns: "minmax(0,1.5fr) minmax(0,1fr)", gap: 12 },
  bottomRow: { display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1.1fr) minmax(0,1.6fr)", gap: 12, flex: 1, minHeight: 0 },
  leftCol: { display: "flex", flexDirection: "column", gap: 10 },
  mapCol: { display: "flex", flexDirection: "column", minHeight: 0 },
};