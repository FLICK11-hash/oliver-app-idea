import { FormEvent, useState } from "react";

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
      const fakeAccount: Account = {
        id: "temp-user",
        username,
      };

      const fakeToken = "temp-token";

      alert(`${mode === "register" ? "Registered" : "Logged in"} successfully.`);
      onAuth(fakeToken, fakeAccount);
    } catch {
      alert("Could not continue.");
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
