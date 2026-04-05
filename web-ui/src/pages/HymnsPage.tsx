import { FormEvent, useEffect, useMemo, useState } from "react";

type Props = {
  token: string;
};

const API_BASE = "/api";

type Hymn = {
  id: string;
  title: string;
  alternateTitle?: string | null;
  hymnNumber?: string | null;
  notes?: string | null;
  active: boolean;
};

type HymnUsageRecord = {
  id: string;
  date: string;
  hymnId: string;
  serviceType?: string | null;
  notes?: string | null;
};

export default function HymnsPage({ token }: Props) {
  const [hymns, setHymns] = useState<Hymn[]>([]);
  const [usage, setUsage] = useState<HymnUsageRecord[]>([]);
  const [search, setSearch] = useState("");

  const [hymnForm, setHymnForm] = useState({
    title: "",
    alternateTitle: "",
    hymnNumber: "",
    notes: "",
    active: true,
  });

  const [usageForm, setUsageForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    hymnId: "",
    serviceType: "",
    notes: "",
  });

  function loadAll() {
    fetch(`${API_BASE}/hymns`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(async (res) => setHymns(await res.json()));

    fetch(`${API_BASE}/hymn-usage-records`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(async (res) => setUsage(await res.json()));
  }

  useEffect(() => {
    loadAll();
  }, [token]);

  function submitHymn(e: FormEvent) {
    e.preventDefault();

    fetch(`${API_BASE}/hymns`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(hymnForm),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to add hymn.");
        return;
      }
      setHymnForm({
        title: "",
        alternateTitle: "",
        hymnNumber: "",
        notes: "",
        active: true,
      });
      loadAll();
    });
  }

  function submitUsage(e: FormEvent) {
    e.preventDefault();

    fetch(`${API_BASE}/hymn-usage-records`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(usageForm),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to log hymn usage.");
        return;
      }
      setUsageForm({
        date: new Date().toISOString().slice(0, 10),
        hymnId: "",
        serviceType: "",
        notes: "",
      });
      loadAll();
    });
  }

  function deleteHymn(hymnId: string) {
    const confirmed = window.confirm("Delete this hymn and all its usage history?");
    if (!confirmed) return;

    fetch(`${API_BASE}/hymns/${hymnId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to delete hymn.");
        return;
      }
      loadAll();
    });
  }

  function deleteUsageRecord(recordId: string) {
    const confirmed = window.confirm("Delete this hymn usage record?");
    if (!confirmed) return;

    fetch(`${API_BASE}/hymn-usage-records/${recordId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to delete hymn usage record.");
        return;
      }
      loadAll();
    });
  }

  function hymnById(id: string) {
    return hymns.find((h) => h.id === id);
  }

  const filteredHymns = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return hymns;
    return hymns.filter((h) =>
      h.title.toLowerCase().includes(q) ||
      (h.alternateTitle || "").toLowerCase().includes(q) ||
      (h.hymnNumber || "").toLowerCase().includes(q) ||
      (h.notes || "").toLowerCase().includes(q)
    );
  }, [hymns, search]);

  return (
    <div className="page-grid">
      <section className="card">
        <h2>Add Hymn</h2>
        <form className="form-grid" onSubmit={submitHymn}>
          <input
            value={hymnForm.title}
            onChange={(e) => setHymnForm({ ...hymnForm, title: e.target.value })}
            placeholder="Title"
            required
          />
          <input
            value={hymnForm.alternateTitle}
            onChange={(e) => setHymnForm({ ...hymnForm, alternateTitle: e.target.value })}
            placeholder="Alternate title"
          />
          <input
            value={hymnForm.hymnNumber}
            onChange={(e) => setHymnForm({ ...hymnForm, hymnNumber: e.target.value })}
            placeholder="Hymn number"
          />
          <input
            value={hymnForm.notes}
            onChange={(e) => setHymnForm({ ...hymnForm, notes: e.target.value })}
            placeholder="Notes"
          />
          <button type="submit">Add Hymn</button>
        </form>
      </section>

      <section className="card">
        <h2>Log Hymn Usage</h2>
        <form className="form-grid" onSubmit={submitUsage}>
          <input
            type="date"
            value={usageForm.date}
            onChange={(e) => setUsageForm({ ...usageForm, date: e.target.value })}
            required
          />
          <select
            value={usageForm.hymnId}
            onChange={(e) => setUsageForm({ ...usageForm, hymnId: e.target.value })}
            required
          >
            <option value="">Select hymn</option>
            {hymns.map((h) => (
              <option key={h.id} value={h.id}>
                {h.title}
                {h.alternateTitle ? ` (${h.alternateTitle})` : ""}
              </option>
            ))}
          </select>
          <input
            value={usageForm.serviceType}
            onChange={(e) => setUsageForm({ ...usageForm, serviceType: e.target.value })}
            placeholder="Service type"
          />
          <input
            value={usageForm.notes}
            onChange={(e) => setUsageForm({ ...usageForm, notes: e.target.value })}
            placeholder="Notes"
          />
          <button type="submit">Save Usage</button>
        </form>
      </section>

      <section className="card full-width">
        <h2>Hymn Database</h2>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search hymns"
        />
        {filteredHymns.map((h) => (
          <div key={h.id} className="list-item">
            <div>
              <strong>{h.title}</strong>
              {h.alternateTitle && (
                <div className="muted-text">Alternate title: {h.alternateTitle}</div>
              )}
              <div className="muted-text">Hymn number: {h.hymnNumber || "No number"}</div>
              <div className="muted-text">Notes: {h.notes || "—"}</div>
            </div>
            <button type="button" onClick={() => deleteHymn(h.id)}>
              X
            </button>
          </div>
        ))}
      </section>

      <section className="card full-width">
        <h2>Hymn Usage History</h2>
        {usage.map((u) => {
          const hymn = hymnById(u.hymnId);

          return (
            <div key={u.id} className="list-item">
              <div>
                <strong>{hymn?.title || u.hymnId}</strong>
                {hymn?.alternateTitle && (
                  <div className="muted-text">Alternate title: {hymn.alternateTitle}</div>
                )}
                <div className="muted-text">
                  Date: {u.date}
                  {u.serviceType ? ` — ${u.serviceType}` : ""}
                </div>
                <div className="muted-text">Hymn notes: {hymn?.notes || "—"}</div>
                <div className="muted-text">Usage notes: {u.notes || "—"}</div>
              </div>
              <button type="button" onClick={() => deleteUsageRecord(u.id)}>
                X
              </button>
            </div>
          );
        })}
      </section>
    </div>
  );
}