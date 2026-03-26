import { FormEvent, useEffect, useState } from "react";
import type { Gender, Volunteer } from "../types";

const API_BASE = "/api";

const emptyForm = {
  name: "",
  gender: "Male" as Gender,
  active: true,
  canTeachKids: false,
  canAssistKids: false,
  canSetup: false,
  canCoffee: false,
  kidsCoupleGroup: "",
  phone: "",
  email: "",
};

export default function VolunteersPage() {
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(true);
  const [form, setForm] = useState(emptyForm);

  function loadVolunteers() {
    fetch(`${API_BASE}/volunteers?includeArchived=${showArchived}`)
      .then((res) => res.json())
      .then(setVolunteers);
  }

  useEffect(() => {
    loadVolunteers();
  }, [showArchived]);

  function resetForm() {
    setForm(emptyForm);
    setEditingId(null);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();

    const method = editingId ? "PUT" : "POST";
    const url = editingId
      ? `${API_BASE}/volunteers/${editingId}`
      : `${API_BASE}/volunteers`;

    fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        kidsCoupleGroup: form.kidsCoupleGroup.trim() || null,
        phone: form.phone.trim() || null,
        email: form.email.trim() || null,
      }),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to save volunteer.");
        return;
      }
      resetForm();
      loadVolunteers();
    });
  }

  function startEdit(volunteer: Volunteer) {
    setEditingId(volunteer.id);
    setForm({
      name: volunteer.name,
      gender: volunteer.gender,
      active: volunteer.active,
      canTeachKids: volunteer.canTeachKids,
      canAssistKids: volunteer.canAssistKids,
      canSetup: volunteer.canSetup,
      canCoffee: volunteer.canCoffee,
      kidsCoupleGroup: volunteer.kidsCoupleGroup ?? "",
      phone: volunteer.phone ?? "",
      email: volunteer.email ?? "",
    });
  }

  return (
    <div className="page-grid">
      <section className="card">
        <h2>{editingId ? "Edit Volunteer" : "Add Volunteer"}</h2>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Name
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </label>

          <label>
            Gender
            <select
              value={form.gender}
              onChange={(e) => setForm({ ...form, gender: e.target.value as Gender })}
            >
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>
          </label>

          <label>
            Phone
            <input
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              placeholder="Optional"
            />
          </label>

          <label>
            Email
            <input
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="Optional"
            />
          </label>

          <label>
            Couple Group
            <input
              value={form.kidsCoupleGroup}
              onChange={(e) => setForm({ ...form, kidsCoupleGroup: e.target.value })}
              placeholder="example: couple-a"
            />
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.active}
              onChange={(e) => setForm({ ...form, active: e.target.checked })}
            />
            Active
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.canTeachKids}
              onChange={(e) => setForm({ ...form, canTeachKids: e.target.checked })}
            />
            Can Teach Kids
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.canAssistKids}
              onChange={(e) => setForm({ ...form, canAssistKids: e.target.checked })}
            />
            Can Assist Kids
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.canSetup}
              onChange={(e) => setForm({ ...form, canSetup: e.target.checked })}
            />
            Can Setup
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.canCoffee}
              onChange={(e) => setForm({ ...form, canCoffee: e.target.checked })}
            />
            Can Coffee
          </label>

          <div className="button-row">
            <button type="submit">{editingId ? "Update" : "Create"}</button>
            <button type="button" onClick={resetForm}>
              Clear
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <div className="list-header">
          <h2>Volunteers</h2>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            Show Archived
          </label>
        </div>

        <div className="list-stack">
          {volunteers.map((volunteer) => (
            <div key={volunteer.id} className="list-item">
              <div>
                <strong>{volunteer.name}</strong> — {volunteer.gender} —{" "}
                {volunteer.archived ? "Archived" : volunteer.active ? "Active" : "Inactive"}

                <div className="muted-text">
                  Phone: {volunteer.phone || "—"} | Email: {volunteer.email || "—"}
                </div>

                <div className="muted-text">
                  Teach: {volunteer.canTeachKids ? "Y" : "N"} | Assist:{" "}
                  {volunteer.canAssistKids ? "Y" : "N"} | Setup:{" "}
                  {volunteer.canSetup ? "Y" : "N"} | Coffee:{" "}
                  {volunteer.canCoffee ? "Y" : "N"}
                </div>
              </div>

              <div className="button-row">
                <button type="button" onClick={() => startEdit(volunteer)}>
                  Edit
                </button>

                {!volunteer.archived && (
                  <button
                    type="button"
                    onClick={() => {
                      const confirmed = window.confirm(
                        `Archive volunteer ${volunteer.name}? Their history will be kept.`
                      );
                      if (!confirmed) return;

                      fetch(`${API_BASE}/volunteers/${volunteer.id}`, {
                        method: "DELETE",
                      }).then(async (res) => {
                        const data = await res.json();
                        if (!res.ok) {
                          alert(data.error || "Failed to archive volunteer.");
                          return;
                        }
                        if (editingId === volunteer.id) {
                          resetForm();
                        }
                        loadVolunteers();
                      });
                    }}
                  >
                    Archive
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}