import { useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import ScheduleBuilderPage from "./pages/ScheduleBuilderPage";
import VolunteersPage from "./pages/VolunteersPage";
import HistoryPage from "./pages/HistoryPage";
import CheckerPage from "./pages/CheckerPage";
import LoginPage from "./pages/LoginPage";
import PastoralPrayerPage from "./pages/PastoralPrayerPage";
import HymnsPage from "./pages/HymnsPage";
import "./App.css";

type Page =
  | "dashboard"
  | "schedule"
  | "volunteers"
  | "history"
  | "checker"
  | "pastoralPrayer"
  | "hymns";

type Account = {
  id: string;
  username: string;
};

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [account, setAccount] = useState<Account | null>(() => {
    const raw = localStorage.getItem("account");
    return raw ? JSON.parse(raw) : null;
  });

  function handleAuth(newToken: string, newAccount: Account) {
    setToken(newToken);
    setAccount(newAccount);
    localStorage.setItem("token", newToken);
    localStorage.setItem("account", JSON.stringify(newAccount));
  }

  function logout() {
    setToken(null);
    setAccount(null);
    localStorage.removeItem("token");
    localStorage.removeItem("account");
  }

  if (!token || !account) {
    return <LoginPage onAuth={handleAuth} />;
  }

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
            <p>Signed in as: {account.username}</p>
          </div>

          <button onClick={logout}>Log Out</button>
        </div>
      </header>

      <nav className="nav-tabs">
        <button onClick={() => setPage("dashboard")}>Dashboard</button>
        <button onClick={() => setPage("schedule")}>Schedule Builder</button>
        <button onClick={() => setPage("volunteers")}>Volunteers</button>
        <button onClick={() => setPage("history")}>History</button>
        <button onClick={() => setPage("checker")}>Checker</button>
        <button onClick={() => setPage("pastoralPrayer")}>Pastoral Prayer</button>
        <button onClick={() => setPage("hymns")}>Hymns</button>
      </nav>

      <main className="main-content">
        {page === "dashboard" && <DashboardPage token={token} />}
        {page === "schedule" && <ScheduleBuilderPage token={token} />}
        {page === "volunteers" && <VolunteersPage token={token} />}
        {page === "history" && <HistoryPage token={token} />}
        {page === "checker" && <CheckerPage token={token} />}
        {page === "pastoralPrayer" && <PastoralPrayerPage token={token} />}
        {page === "hymns" && <HymnsPage token={token} />}
      </main>
    </div>
  );
}