import { useEffect, useState } from "react";
import type { DashboardData } from "../types";

type Props = {
  token: string;
};

const API_BASE = "https://oliver-app-idea-3.onrender.com/api";

export default function DashboardPage({ token }: Props) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/dashboard`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (res) => {
        const result = await res.json();

        if (!res.ok) {
          throw new Error(result.error || "Failed to load dashboard");
        }

        return result;
      })
      .then((result) => {
        setData(result);
        setError("");
      })
      .catch((err) => setError(err.message || "Failed to load dashboard."));
  }, [token]);

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
    </div>
  );
}
