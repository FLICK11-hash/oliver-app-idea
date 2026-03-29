import { useEffect, useMemo, useState } from "react";
import type { Schedule, Volunteer } from "../types";

const API_BASE = "https://oliver-app-idea-2.onrender.com/api";

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

export default function CheckerPage() {
  const [selectedDate, setSelectedDate] = useState(todayString());
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/volunteers?includeArchived=true`)
      .then((res) => res.json())
      .then(setVolunteers);
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/schedules/${selectedDate}`)
      .then(async (res) => {
        const data = await res.json();
        setSchedule(data);
        setMessage("");
      })
      .catch(() => {
        setSchedule(null);
        setMessage("Could not load schedule for that date.");
      });
  }, [selectedDate]);

  const volunteerMap = useMemo(() => {
    const map: Record<string, Volunteer> = {};
    for (const volunteer of volunteers) {
      map[volunteer.id] = volunteer;
    }
    return map;
  }, [volunteers]);

  function volunteerName(id: string | null) {
    if (!id) return "—";
    return volunteerMap[id]?.name ?? id;
  }

  function volunteerNames(ids: string[]) {
    if (ids.length === 0) return "—";
    return ids.map((id) => volunteerMap[id]?.name ?? id).join(", ");
  }

  return (
    <div className="page-grid">
      <section className="card">
        <h2>Checker</h2>
        <label>
          Sunday Date
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </label>

        {message && <p className="error-text">{message}</p>}
      </section>

      <section className="card">
        <h2>Schedule for {selectedDate}</h2>

        {!schedule ? (
          <p>No schedule data loaded.</p>
        ) : (
          <div className="list-stack">
            <div className="list-item">
              <strong>Kids Teacher</strong>
              <span>{volunteerName(schedule.kidsTeacher)}</span>
            </div>

            <div className="list-item">
              <strong>Kids Assistants</strong>
              <span>{volunteerNames(schedule.kidsAssistants)}</span>
            </div>

            <div className="list-item">
              <strong>Setup</strong>
              <span>{volunteerNames(schedule.setup)}</span>
            </div>

            <div className="list-item">
              <strong>Coffee</strong>
              <span>{volunteerName(schedule.coffee)}</span>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
