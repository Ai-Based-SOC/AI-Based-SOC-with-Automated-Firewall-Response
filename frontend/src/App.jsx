import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import ThreatsPage from "./pages/ThreatsPage";
import SystemHealthPage from "./pages/SystemHealthPage";
import AttackLogsPage from "./pages/AttackLogsPage";
import FirewallPage from "./pages/FirewallPage";
import ReportsPage from "./pages/ReportsPage";
import AssistantPage from "./pages/AssistantPage";
import SettingsPage from "./pages/SettingsPage";
import AttackDetailsPage from "./pages/AttackDetailsPage";

import { meApi } from "./services/api";

export default function App() {
  const [loading, setLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);
  const [profile, setProfile] = useState(null);

  async function loadMe() {
    try {
      const response = await meApi();
      setProfile(response.data);
      setIsAuthed(true);
    } catch {
      setProfile(null);
      setIsAuthed(false);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMe();
  }, []);

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-[#020b1c] text-white">
        Loading AI SOC...
      </div>
    );
  }

  if (!isAuthed) {
    return (
      <Routes>
        <Route
          path="/signup"
          element={<SignupPage onSignupSuccess={loadMe} />}
        />
        <Route
          path="*"
          element={<LoginPage onLoginSuccess={loadMe} />}
        />
      </Routes>
    );
  }

  function logout() {
    localStorage.removeItem("soc_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("role");

    setProfile(null);
    setIsAuthed(false);
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route
        path="/dashboard"
        element={<DashboardPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/threats"
        element={<ThreatsPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/system-health"
        element={<SystemHealthPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/logs"
        element={<AttackLogsPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/firewall"
        element={<FirewallPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/reports"
        element={<ReportsPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/assistant"
        element={<AssistantPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/settings"
        element={<SettingsPage profile={profile} onLogout={logout} />}
      />

      <Route
        path="/attacks/:attackId"
        element={<AttackDetailsPage profile={profile} onLogout={logout} />}
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}