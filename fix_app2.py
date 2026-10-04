content = """import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import DashboardPage from "./pages/DashboardPage";
import IncidentsPage from "./pages/IncidentsPage";
import ThreatIntelligencePage from "./pages/ThreatIntelligencePage";
import FirewallPage from "./pages/FirewallPage";
import SecurityLogsPage from "./pages/SecurityLogsPage";
import ReportsPage from "./pages/ReportsPage";
import AISOCAssistantPage from "./pages/AISOCAssistantPage";
import SystemHealthPage from "./pages/SystemHealthPage";
import SettingsPage from "./pages/SettingsPage";
import InvestigationPage from "./pages/InvestigationPage";
import DoSSimulationPage from "./pages/DoSSimulationPage";
import LiveMapPage from "./pages/LiveMapPage";

export default function App() {
  return (
    <Routes>
      {/* Public routes - always accessible */}

      <Route path="/login" element={<LoginPage />} />

      <Route path="/signup" element={<SignupPage />} />

      {/* Root and dashboard routes - always accessible */}

      <Route path="/" element={<DashboardPage />} />

      <Route path="/dashboard" element={<DashboardPage />} />

      {/* SOC pages - always accessible without authentication */}

      <Route path="/incidents" element={<IncidentsPage />} />

      <Route path="/threat-intelligence" element={<ThreatIntelligencePage />} />

      <Route path="/firewall" element={<FirewallPage />} />

      <Route path="/logs" element={<SecurityLogsPage />} />

      <Route path="/reports" element={<ReportsPage />} />

      <Route path="/ai-assistant" element={<AISOCAssistantPage />} />

      <Route path="/system-health" element={<SystemHealthPage />} />

      <Route path="/settings" element={<SettingsPage />} />

      {/* Contextual SOC pages */}

      <Route path="/investigation/:id" element={<InvestigationPage />} />

      <Route path="/dos-simulation" element={<DoSSimulationPage />} />

      <Route path="/live-map" element={<LiveMapPage />} />

      {/* Wildcard - redirect to dashboard */>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
"""
with open(r'C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\App.jsx', 'w') as f:
    f.write(content)
print('Done writing App.jsx')