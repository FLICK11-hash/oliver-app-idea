import { FormEvent, useEffect, useState } from "react";

type Props = {
  token: string;
};

const API_BASE = "https://oliver-app-idea-2.onrender.com/api";

type Member = {
  id: string;
  name: string;
  gender: "Male" | "Female";
  active: boolean;
  memberStatus?: string | null;
  dateAdded: string;
};

type PrayerSuggestion = {
  member: Member;
  priority: number;
  stats: {
    totalPrayerMentions: number;
    lastPrayedForDate: string | null;
    weeksSinceLastPrayedFor: number | null;
    neverPrayedFor: boolean;
  };
};

type PrayerRecord = {
  id: string;
  date: string;
  memberId: string;
  gender: string;
  notes?: string | null;
};

export default function PastoralPrayerPage({ token }: Props) {
  const [members, setMembers] = useState<Member[]>([]);
  const [records, setRecords] = useState<PrayerRecord[]>([]);
  const [suggestions, setSuggestions] = useState<{ male: PrayerSuggestion[]; female: PrayerSuggestion[] }>({
    male: [],
    female: [],
  });

  const [memberForm, setMemberForm] = useState({
    name: "",
    gender: "Male" as "Male" | "Female",
    active: true,
    memberStatus: "",
    dateAdded: new Date().toISOString().slice(0, 10),
  });

  const [logForm, setLogForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    maleMemberId: "",
    femaleMemberId: "",
    notes: "",
  });

  function loadAll() {
    fetch(`${API_BASE}/members`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(async (res) => setMembers(await res.json()));

    fetch(`${API_BASE}/pastoral-prayer-records?limit=100`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(async (res) => setRecords(await res.json()));

    fetch(`${API_BASE}/pastoral-prayer-suggestions?date=${logForm.date}`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(async (res) => setSuggestions(await res.json()));
  }

  useEffect(() => {
    loadAll();
  }, [token, logForm.date]);

  function submitMember(e: FormEvent) {
    e.preventDefault();

    fetch(`${API_BASE}/members`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(memberForm),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to add member.");
        return;
      }
      setMemberForm({
        name: "",
        gender: "Male",
        active: true,
        memberStatus: "",
        dateAdded: new Date().toISOString().slice(0, 10),
      });
      loadAll();
    });
  }

  function submitPrayerLog(e: FormEvent) {
    e.preventDefault();

    fetch(`${API_BASE}/pastoral-prayer-records`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(logForm),
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to log pastoral prayer.");
        return;
      }
      alert("Pastoral prayer saved.");
      loadAll();
    });
  }

  function deletePrayerRecord(recordId: string) {
    const confirmed = window.confirm("Delete this prayer record?");
    if (!confirmed) return;

    fetch(`${API_BASE}/pastoral-prayer-records/${recordId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to delete prayer record.");
        return;
      }
      loadAll();
    });
  }

  function deleteMember(memberId: string, memberName: string) {
    const confirmed = window.confirm(`Delete member ${memberName}? This will also remove their prayer history.`);
    if (!confirmed) return;

    fetch(`${API_BASE}/members/${memberId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to delete member.");
        return;
      }
      loadAll();
    });
  }

  function memberName(id: string) {
    return members.find((m) => m.id === id)?.name ?? id;
  }

  const maleMembers = members.filter((m) => m.gender === "Male" && m.active);
  const femaleMembers = members.filter((m) => m.gender === "Female" && m.active);

  return (
    <div className="page-grid">
      <section className="card">
        <h2>Add Member</h2>
        <form className="form-grid" onSubmit={submitMember}>
          <input
            value={memberForm.name}
            onChange={(e) => setMemberForm({ ...memberForm, name: e.target.value })}
            placeholder="Name"
            required
          />
          <select
            value={memberForm.gender}
            onChange={(e) => setMemberForm({ ...memberForm, gender: e.target.value as "Male" | "Female" })}
          >
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
          <input
            value={memberForm.memberStatus}
            onChange={(e) => setMemberForm({ ...memberForm, memberStatus: e.target.value })}
            placeholder="Optional member status"
          />
          <input
            type="date"
            value={memberForm.dateAdded}
            onChange={(e) => setMemberForm({ ...memberForm, dateAdded: e.target.value })}
          />
          <button type="submit">Add Member</button>
        </form>
      </section>

      <section className="card">
        <h2>Log Pastoral Prayer</h2>
        <form className="form-grid" onSubmit={submitPrayerLog}>
          <input
            type="date"
            value={logForm.date}
            onChange={(e) => setLogForm({ ...logForm, date: e.target.value })}
            required
          />
          <select
            value={logForm.maleMemberId}
            onChange={(e) => setLogForm({ ...logForm, maleMemberId: e.target.value })}
            required
          >
            <option value="">Select male member</option>
            {maleMembers.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
          <select
            value={logForm.femaleMemberId}
            onChange={(e) => setLogForm({ ...logForm, femaleMemberId: e.target.value })}
            required
          >
            <option value="">Select female member</option>
            {femaleMembers.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
          <input
            value={logForm.notes}
            onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
            placeholder="Optional notes"
          />
          <button type="submit">Save Prayer Record</button>
        </form>
      </section>

      <section className="card">
        <h2>Top Male Suggestions</h2>
        {suggestions.male.map((s) => (
          <div key={s.member.id} className="list-item">
            <div>
              <strong>{s.member.name}</strong>
              <div className="muted-text">Priority: {s.priority}</div>
            </div>
            <button type="button" onClick={() => setLogForm((prev) => ({ ...prev, maleMemberId: s.member.id }))}>
              Use
            </button>
          </div>
        ))}
      </section>

      <section className="card">
        <h2>Top Female Suggestions</h2>
        {suggestions.female.map((s) => (
          <div key={s.member.id} className="list-item">
            <div>
              <strong>{s.member.name}</strong>
              <div className="muted-text">Priority: {s.priority}</div>
            </div>
            <button type="button" onClick={() => setLogForm((prev) => ({ ...prev, femaleMemberId: s.member.id }))}>
              Use
            </button>
          </div>
        ))}
      </section>

      <section className="card full-width">
        <h2>Members</h2>
        {members.map((m) => (
          <div key={m.id} className="list-item">
            <div>
              <strong>{m.name}</strong>
              <span> — {m.gender}</span>
            </div>
            <button type="button" onClick={() => deleteMember(m.id, m.name)}>
              X
            </button>
          </div>
        ))}
      </section>

      <section className="card full-width">
        <h2>Prayer History</h2>
        {records.map((r) => (
          <div key={r.id} className="list-item">
            <div>
              <strong>{memberName(r.memberId)}</strong>
              <span> {r.date} — {r.gender}</span>
            </div>
            <button type="button" onClick={() => deletePrayerRecord(r.id)}>
              X
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}
