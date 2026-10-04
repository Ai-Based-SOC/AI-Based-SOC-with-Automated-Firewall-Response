import { useEffect, useState } from "react";
import { useAuth } from "../useAuth";
import { MetricCard } from "../components/MetricCard";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";

export default function InvestigationPage() {
  const { profile } = useAuth();
  const [loading, setLoading] = useState(true);
  const [incident, setIncident] = useState(null);

  useEffect(() => {
    // Load incident data
    setLoading(false);
  }, []);

  if (loading) return <LoadingState />

  if (!incident) return <EmptyState title="Select an incident" CTA="Search incidents" />

  return (
    <div className="min-h-screen soc-page">
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to={`/investigation/${incident.id}`} replace />} />
          <Route path="/:id" element={<IncidentDetail />} />
        </Routes>
      </AppShell>
    </div>
  )
}

function IncidentDetail() {
  const params = useParams()
  const [timeline, setTimeline] = useState([])

  return (
    <div className="p-6">
      <h2 className="soc-heading mb-4">Investigation</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <MetricCard title="AI Verdict" value="Pending" kind="critical" />
          <MetricCard title="Status" value="Open" kind="good" />
        </div>
        <div>
          <MetricCard title="Assets Affected" value="3" kind="warning" />
          <MetricCard title="Evidence" value="7 items" kind="info" />
        </div>
      </div>
      <div className="space-y-4">
        <h3>Timeline</h3>
        <DataTable data={timeline} columns={[]} />
        <h3>AI Assessment</h3>
        <p className="text-soc-muted">The AI has flagged this incident with medium severity based on pattern matching.</p>
        <h3>Analyst Decision</h3>
        <p className="text-soc-muted">Pending analyst review and classification.</p>
      </div>
    </div>
  )
}