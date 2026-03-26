import { useEffect, useMemo, useState } from "react";
import type { Candidate, Role, Schedule, ValidationResult, Volunteer } from "../types";

const API_BASE = "http://127.0.0.1:5000/api";

const roleLabels: Record<Role, string> = {
  KIDS_TEACHER: "Kids Teacher",
  KIDS_ASSISTANT: "Kids Assistant",
  SETUP: "Setup",
  COFFEE: "Coffee",
};

function nextSundayString() {
  const today = new Date();
  const day = today.getDay();
  const daysUntilSunday = day === 0 ? 0 : 7 - day;
  const nextSunday = new Date(today);
  nextSunday.setDate(today.getDate() + daysUntilSunday);
  return nextSunday.toISOString().slice(0, 10);
}

export default function ScheduleBuilderPage() {
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [schedule, setSchedule] = useState<Schedule>({
    date: nextSundayString(),
    kidsTeacher: null,
    kidsAssistants: [],
    setup: [],
    coffee: null,
  });
  const [validation, setValidation] = useState<ValidationResult>({ errors: [], warnings: [] });
  const [suggestions, setSuggestions] = useState<Record<string, Candidate[]>>({
    KIDS_TEACHER: [],
    KIDS_ASSISTANT: [],
    SETUP: [],
    COFFEE: [],
  });

  useEffect(() => {
    fetch(`${API_BASE}/volunteers`)
      .then((res) => res.json())
      .then(setVolunteers);
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/schedules/${schedule.date}`)
      .then((res) => res.json())
      .then((data: Schedule) => {
        setSchedule({
          date: data.date,
          kidsTeacher: data.kidsTeacher,
          kidsAssistants: data.kidsAssistants ?? [],
          setup: data.setup ?? [],
          coffee: data.coffee,
        });
      });
  }, [schedule.date]);

  useEffect(() => {
    fetch(`${API_BASE}/validate-schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schedule),
    })
      .then((res) => res.json())
      .then(setValidation);
  }, [schedule]);

  useEffect(() => {
    const roles: Role[] = ["KIDS_TEACHER", "KIDS_ASSISTANT", "SETUP", "COFFEE"];
    roles.forEach((role) => {
      fetch(`${API_BASE}/suggestions/${role}?date=${schedule.date}&limit=5`)
        .then((res) => res.json())
        .then((data) =>
          setSuggestions((prev) => ({
            ...prev,
            [role]: data,
          }))
        );
    });
  }, [schedule.date]);

  const activeVolunteers = useMemo(
    () => volunteers.filter((v) => v.active && !v.archived),
    [volunteers]
  );

  const eligibleTeachers = useMemo(
    () => activeVolunteers.filter((v) => v.canTeachKids),
    [activeVolunteers]
  );

  const eligibleAssistants = useMemo(
    () => activeVolunteers.filter((v) => v.canAssistKids),
    [activeVolunteers]
  );

  const eligibleSetup = useMemo(
    () => activeVolunteers.filter((v) => v.canSetup && v.gender === "Male"),
    [activeVolunteers]
  );

  const eligibleCoffee = useMemo(
    () => activeVolunteers.filter((v) => v.canCoffee),
    [activeVolunteers]
  );

  function saveSchedule() {
    fetch(`${API_BASE}/schedules/${schedule.date}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schedule),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to save schedule.");
        return;
      }
      setValidation(data.validation);
      alert("Schedule saved.");
    });
  }

  function toggleMultiSelect(
    list: string[],
    volunteerId: string,
    maxSize: number,
    setter: (next: string[]) => void
  ) {
    if (list.includes(volunteerId)) {
      setter(list.filter((id) => id !== volunteerId));
      return;
    }
    if (list.length >= maxSize) {
      return;
    }
    setter([...list, volunteerId]);
  }

  return (
    <div className="page-grid">
      <section className="card">
        <h2>Schedule Builder</h2>

        <label>
          Sunday Date
          <input
            type="date"
            value={schedule.date}
            onChange={(e) =>
              setSchedule((prev) => ({
                ...prev,
                date: e.target.value,
              }))
            }
          />
        </label>

        <label>
          Kids Teacher
          <select
            value={schedule.kidsTeacher ?? ""}
            onChange={(e) =>
              setSchedule((prev) => ({
                ...prev,
                kidsTeacher: e.target.value || null,
              }))
            }
          >
            <option value="">Select teacher</option>
            {eligibleTeachers.map((volunteer) => (
              <option key={volunteer.id} value={volunteer.id}>
                {volunteer.name}
              </option>
            ))}
          </select>
        </label>

        <div className="multi-block">
          <h3>Kids Assistants (pick 2)</h3>
          {eligibleAssistants.map((volunteer) => (
            <label key={volunteer.id} className="checkbox-row">
              <input
                type="checkbox"
                checked={schedule.kidsAssistants.includes(volunteer.id)}
                onChange={() =>
                  toggleMultiSelect(schedule.kidsAssistants, volunteer.id, 2, (next) =>
                    setSchedule((prev) => ({ ...prev, kidsAssistants: next }))
                  )
                }
              />
              {volunteer.name}
            </label>
          ))}
        </div>

        <div className="multi-block">
          <h3>Setup Team (pick 2)</h3>
          {eligibleSetup.map((volunteer) => (
            <label key={volunteer.id} className="checkbox-row">
              <input
                type="checkbox"
                checked={schedule.setup.includes(volunteer.id)}
                onChange={() =>
                  toggleMultiSelect(schedule.setup, volunteer.id, 2, (next) =>
                    setSchedule((prev) => ({ ...prev, setup: next }))
                  )
                }
              />
              {volunteer.name}
            </label>
          ))}
        </div>

        <label>
          Coffee
          <select
            value={schedule.coffee ?? ""}
            onChange={(e) =>
              setSchedule((prev) => ({
                ...prev,
                coffee: e.target.value || null,
              }))
            }
          >
            <option value="">Select coffee volunteer</option>
            {eligibleCoffee.map((volunteer) => (
              <option key={volunteer.id} value={volunteer.id}>
                {volunteer.name}
              </option>
            ))}
          </select>
        </label>

        <button onClick={saveSchedule}>Save Schedule</button>
      </section>

      <section className="card">
        <h2>Validation</h2>

        <h3>Errors</h3>
        {validation.errors.length === 0 ? (
          <p className="success-text">No hard errors.</p>
        ) : (
          <ul>
            {validation.errors.map((error) => (
              <li key={error} className="error-text">
                {error}
              </li>
            ))}
          </ul>
        )}

        <h3>Warnings</h3>
        {validation.warnings.length === 0 ? (
          <p className="success-text">No warnings.</p>
        ) : (
          <ul>
            {validation.warnings.map((warning) => (
              <li key={warning} className="warning-text">
                {warning}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card full-width">
        <h2>Top Suggestions</h2>
        <div className="suggestions-grid">
          {(Object.keys(suggestions) as Role[]).map((role) => (
            <div key={role} className="card compact-card">
              <h3>{roleLabels[role]}</h3>
              {suggestions[role].map((candidate) => (
                <div key={candidate.volunteer.id} className="suggestion-row">
                  <strong>{candidate.volunteer.name}</strong>
                  <span>{candidate.priority}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}