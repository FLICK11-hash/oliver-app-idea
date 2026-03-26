import { FormEvent, useState } from "react";

const API_BASE = "http://127.0.0.1:5000/api";

type Account = {
  id: string;
  username: string;
};

type Props = {
  onAuth: (token: string, account: Account) => void;
};

export default function LoginPage({ onAuth }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);

    try {
      const res = await fetch(`${API_BASE}/auth/${mode}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "Authentication failed.");
        return;
      }

      alert(`${mode === "register" ? "Registered" : "Logged in"} successfully.`);
      onAuth(data.token, data.account);
    } catch {
      alert("Could not connect to the server.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="card">
        <h2>{mode === "login" ? "Log In" : "Create Account"}</h2>

        <form className="form-grid" onSubmit={submit}>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          <div className="button-row">
            <button type="submit" disabled={busy}>
              {busy ? "Working..." : mode === "login" ? "Log In" : "Register"}
            </button>

            <button
              type="button"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              disabled={busy}
            >
              Switch to {mode === "login" ? "Register" : "Login"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}