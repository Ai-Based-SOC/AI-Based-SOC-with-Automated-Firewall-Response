import { useState } from "react";
import { Link } from "react-router-dom";
import { signupApi } from "../services/api";

export default function SignupPage({ onSignupSuccess }) {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      await signupApi(form);
      await onSignupSuccess?.();
    } catch (requestError) {
      setError(
        requestError?.response?.data?.detail ||
          "Unable to create account."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[#020b1c] p-4">
      <form
        onSubmit={submit}
        className="w-full max-w-md rounded-2xl border border-cyan-900 bg-[#071426] p-8"
      >
        <h1 className="text-3xl font-bold text-white">Create Account</h1>
        <p className="mt-2 text-sm text-slate-400">
          Join the AI SOC platform
        </p>

        <div className="mt-6 space-y-4">
          <input
            required
            placeholder="Full name"
            value={form.full_name}
            onChange={(event) =>
              setForm({ ...form, full_name: event.target.value })
            }
            className="w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-3"
          />

          <input
            required
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(event) =>
              setForm({ ...form, email: event.target.value })
            }
            className="w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-3"
          />

          <input
            required
            minLength={8}
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(event) =>
              setForm({ ...form, password: event.target.value })
            }
            className="w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-3"
          />
        </div>

        {error && (
          <p className="mt-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </p>
        )}

        <button
          disabled={busy}
          className="mt-5 w-full rounded-lg bg-blue-600 py-3 font-semibold disabled:opacity-50"
        >
          {busy ? "Creating..." : "Create Account"}
        </button>

        <Link
          to="/login"
          className="mt-4 block text-center text-sm text-cyan-300"
        >
          Already have an account? Sign in
        </Link>
      </form>
    </main>
  );
}