import { useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import ScheduleBuilderPage from "./pages/ScheduleBuilderPage";
import VolunteersPage from "./pages/VolunteersPage";
import HistoryPage from "./pages/HistoryPage";
import CheckerPage from "./pages/CheckerPage";
import "./App.css";

type Page = "dashboard" | "schedule" | "volunteers" | "history" | "checker";

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="cross-mark" aria-hidden="true">
            <div className="cross-vertical"></div>
            <div className="cross-horizontal"></div>
          </div>

          <div>
            <h1>Church Volunteer Scheduling App</h1>
            <p>Suggest, validate, and track Sunday service roles.</p>
          </div>
        </div>
      </header>

      <nav className="nav-tabs">
        <button onClick={() => setPage("dashboard")}>Dashboard</button>
        <button onClick={() => setPage("schedule")}>Schedule Builder</button>
        <button onClick={() => setPage("volunteers")}>Volunteers</button>
        <button onClick={() => setPage("history")}>History</button>
        <button onClick={() => setPage("checker")}>Checker</button>
      </nav>

      <main className="main-content">
        {page === "dashboard" && <DashboardPage />}
        {page === "schedule" && <ScheduleBuilderPage />}
        {page === "volunteers" && <VolunteersPage />}
        {page === "history" && <HistoryPage />}
        {page === "checker" && <CheckerPage />}
      </main>
    </div>
  );
}