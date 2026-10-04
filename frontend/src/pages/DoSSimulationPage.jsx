import { useEffect } from "react";
import { useAuth } from "../useAuth";
import { MetricCard } from "../components/MetricCard";
import { StatusBadge } from "../components/StatusBadge";
import { EmptyState } from "../components/EmptyState";

export default function DoSSimulationPage() {
  const { profile } = useAuth();

  return (
    <div className="min-h-screen soc-page">
      <AppShell>
        <main className="min-h-64 flex items-center justify-center">
          <div className="text-center">
            <div className="icon-size-6 mb-4"><ShieldAlert size={48} /></div>
            <h2 className="soc-heading">DoS Simulation</h2>
            <p className="text-soc-muted mb-6">
              Safe simulation-only controls for training purposes. No real traffic generation or attack capability is enabled.
            </p>
            <div className="alert alert-warning soc-alert mb-6">
              <span className="icon"><ShieldAlert size={16} /></span>
              <strong>Simulation Mode Disabled:</strong> This feature is currently in simulation mode only. No actual denial-of-service testing is performed.
            </div>
            <button className="soc-btn soc-btn-secondary">View Simulation Guidelines</button>
          </div>
        </main>
      </AppShell>
    </div>
  );
}