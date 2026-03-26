import { useEffect, useState } from "react";
import type { Candidate, DashboardData, Role } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

const roleLabels: Record<Role, string> = {
  KIDS_TEACHER: "Kids Teacher",
  KIDS_ASSISTANT: "Kids Assistant",
  SETUP: "Setup",
  COFFEE: "Coffee",
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/dashboard`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Failed to load dashboard");
        }
        return res.json();
      })
      .then(setData)
      .catch(() => setError("Failed to load dashboard."));
  }, []);

  const renderCandidates = (candidates: Candidate[]) => (
    <div className="candidate-list">
      {candidates.map((candidate) => (
        <div key={candidate.volunteer.id} className="card compact-card">
          <strong>{candidate.volunteer.name}</strong>
          <div>Priority: {candidate.priority}</div>
          <div>Total serves: {candidate.stats.totalServes}</div>
          <div>This month: {candidate.stats.servesThisMonth}</div>
          <div>Served last Sunday: {candidate.stats.servedLastSunday ? "Yes" : "No"}</div>
        </div>
      ))}
    </div>
  );

  if (error) {
    return <div className="card error-box">{error}</div>;
  }

  if (!data) {
    return <div className="card">Loading dashboard...</div>;
  }

  return (
    <div className="page-stack">
      <div className="stats-grid">
        <div className="card stat-card">
          <h3>Total Volunteers</h3>
          <div className="big-number">{data.totalVolunteers}</div>
        </div>
        <div className="card stat-card">
          <h3>Active Volunteers</h3>
          <div className="big-number">{data.activeVolunteers}</div>
        </div>
        <div className="card stat-card">
          <h3>Total Serve Records</h3>
          <div className="big-number">{data.totalServeRecords}</div>
        </div>
      </div>

      {(Object.keys(data.topCandidates) as Role[]).map((role) => (
        <section key={role} className="card">
          <h2>{roleLabels[role]} Suggestions</h2>
          {renderCandidates(data.topCandidates[role])}
        </section>
      ))}
    </div>
  );
}
