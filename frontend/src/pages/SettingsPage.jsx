import { useEffect } from "react";
import { useAuth } from "../useAuth";
import { MetricCard } from "../components/MetricCard";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";

export default function SettingsPage() {
  const { profile } = useAuth();
  const [form, setForm] = useState({
    notifications: true,
    api_enabled: false,
  });

  useEffect(() => {
    // Load settings
  }, []);

  const handleSave = () => {
    // Save settings
  };

  return (
    <div className="min-h-screen soc-page">
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/profile" replace />} />
          <Route path="/profile" element={<ProfileSection />} />
          <Route path="/notifications" element={<NotificationSettings />} />
          <Route path="/api" element={<APIConfig />} />
          <Route path="/firewall-simulation" element={<FirewallSimulation />} />
        </Routes>
      </AppShell>
    </div>
  );
}

function ProfileSection() {
  return (
    <div className="p-6">
      <h2 className="soc-heading mb-4">Profile</h2>
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label className="soc-label">Name</label>
          <input className="soc-input" readOnly />
        </div>
        <div>
          <label className="soc-label">Role</label>
          <select className="soc-input">
            <option>Analyst</option>
            <option>Admin</option>
          </select>
        </div>
      </div>
      <button className="soc-btn soc-btn-secondary w-full">Save Changes</button>
    </div>
  );
}

function NotificationSettings() {
  return (
    <div className="p-6">
      <h2 className="soc-heading mb-4">Notifications</h2>
      <div className="space-y-4">
        <div>
          <label className="soc-label">Email alerts</label>
          <label className="soc-switch">
            <input type="checkbox" checked defaultChecked />
            <span className="soc-switch-slider"></span>
          </label>
        </div>
        <div>
          <label className="soc-label">Push notifications</label>
          <label className="soc-switch">
            <input type="checkbox" checked defaultChecked />
            <span className="soc-switch-slider"></span>
          </label>
        </div>
      </div>
    </div>
  );
}

function APIConfig() {
  return (
    <div className="p-6">
      <h2 className="soc-heading mb-4">API Integration</h2>
      <p className="text-soc-muted mb-4">Configure integration endpoints here.</p>
      <button className="soc-btn soc-btn-primary">Save Configuration</button>
    </div>
  );
}

function FirewallSimulation() {
  return (
    <div className="p-6">
      <h2 className="soc-heading mb-4">Firewall Simulation Controls</h2>
      <div className="alert alert-warning soc-alert mb-4">
        <span className="icon"><ShieldAlert size={16} /></span>
        <strong>Simulation Mode:</strong> This is a simulation-only feature. No real firewall rules will be modified.
      </div>
      <button className="soc-btn soc-btn-danger">Initialize Simulation</button>
      <p className="text-soc-muted mt-4">Simulated actions for training purposes only.</p>
    </div>
  );
}