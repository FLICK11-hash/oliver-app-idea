import { FormEvent, useEffect, useState } from "react";
import type { Role, ServeRecord, Volunteer } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

const roleOptions: Role[] = [
  "KIDS_TEACHER",
  "KIDS_ASSISTANT",
  "SETUP",
  "COFFEE",
];

export default function HistoryPage() {
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [records, setRecords] = useState<ServeRecord[]>([]);
  const [form, setForm] = useState({
    date: "",
    volunteerId: "",
    role: "KIDS_TEACHER" as Role,
  });

  function loadAll() {
    fetch(`${API_BASE}/volunteers`)
      .then((res) => res.json())
      .then(setVolunteers);

    fetch(`${API_BASE}/serve-records`)
      .then((res) => res.json())
      .then(setRecords);
  }

  useEffect(() => {
    loadAll();
  }, []);

  function submitRecord(e: FormEvent) {
    e.preventDefault();

    fetch(`${API_BASE}/serve-records`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to add serve record.");
        return;
      }
      setForm({ date: "", volunteerId: "", role: "KIDS_TEACHER" });
      loadAll();
    });
  }

  function volunteerName(id: string) {
    return volunteers.find((v) => v.id === id)?.name ?? id;
  }

  return (
    <div className="page-grid">
      <section className="card">
        <h2>Add Serve Record</h2>
        <form className="form-grid" onSubmit={submitRecord}>
          <label>
            Sunday Date
            <input
              type="date"
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
              required
            />
          </label>

          <label>
            Volunteer
            <select
              value={form.volunteerId}
              onChange={(e) => setForm({ ...form, volunteerId: e.target.value })}
              required
            >
              <option value="">Select volunteer</option>
              {volunteers.map((volunteer) => (
                <option key={volunteer.id} value={volunteer.id}>
                  {volunteer.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Role
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </label>

          <button type="submit">Add Record</button>
        </form>
      </section>

      <section className="card">
        <h2>Serve History</h2>
        <div className="list-stack">
          {records.map((record) => (
            <div key={record.id} className="list-item">
              <div>
                <strong>{volunteerName(record.volunteerId)}</strong>
                <div className="muted-text">
                  {record.date} — {record.role}
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  const confirmed = window.confirm("Delete this serve record?");
                  if (!confirmed) return;

                  fetch(`${API_BASE}/serve-records/${record.id}`, {
                    method: "DELETE",
                  }).then(async (res) => {
                    const data = await res.json();
                    if (!res.ok) {
                      alert(data.error || "Failed to delete serve record.");
                      return;
                    }
                    loadAll();
                  });
                }}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
