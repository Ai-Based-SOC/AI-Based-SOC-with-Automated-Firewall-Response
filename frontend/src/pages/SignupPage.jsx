import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginApi, signupApi, meApi } from "../services/api";

export default function SignupPage({ onSuccess }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    setError("");
    setLoading(true);

    try {
      const { data } = await signupApi(email, password, passwordConfirm, fullName);
      const token = data?.access_token;

      if (!token) throw new Error("No access token received");

      localStorage.setItem("soc_token", token);
      localStorage.setItem("access_token", token);

      let profile = {
        id: "dev-user",
        email,
        full_name: fullName || email.split("@")[0],
        role: data?.role || "user",
      };

      try {
        const meRes = await meApi();
        if (meRes?.data) profile = meRes.data;
      } catch {
        // ignore and keep fallback profile
      }

      localStorage.setItem("user", JSON.stringify(profile));
      onSuccess?.(profile);
      navigate("/", { replace: true });
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Signup failed";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900/70 p-8">
        <h1 className="text-2xl font-bold mb-4">AI SOC Firewall</h1>
        <p className="text-slate-400 mb-6">Create an account</p>

        {error ? (
          <div className="rounded-md border border-red-700 bg-red-950/40 text-red-300 px-3 py-2 mb-4">
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slate-300 block mb-1">Email</label>
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 outline-none focus:border-cyan-500"
              placeholder="admin@soc.local"
            />
          </div>

          <div>
            <label className="text-sm text-slate-300 block mb-1">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 outline-none focus:border-cyan-500"
              placeholder="SOC User"
            />
          </div>

          <div>
            <label className="text-sm text-slate-300 block mb-1">Password</label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 outline-none focus:border-cyan-500"
              placeholder="********"
            />
          </div>

          <div>
            <label className="text-sm text-slate-300 block mb-1">Confirm Password</label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 outline-none focus:border-cyan-500"
              placeholder="********"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-cyan-700 hover:bg-cyan-600 disabled:opacity-60 px-4 py-2 font-medium">
            {loading ? "Creating..." : "Sign Up"}
          </button>
        </form>

        <div className="mt-6 text-sm text-slate-400">
          Already have an account? <span className="cursor-pointer text-cyan-400" onClick={() => navigate("/login")}>Login</span>
        </div>
      </div>
    </div>
  );
}