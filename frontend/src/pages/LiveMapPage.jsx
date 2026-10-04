import { useEffect } from "react";
import { MetricCard } from "../components/MetricCard";
import { DataTable } from "../components/DataTable";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingState } from "../components/LoadingState";

export default function LiveMapPage() {
  const [loading, setLoading] = useState(true);
  const [attacks, setAttacks] = useState([]);

  useEffect(() => {
    // Load live attack data
    setLoading(false);
  }, []);

  if (loading) return <LoadingState />

  return (
    <div className="min-h-screen soc-page">
      <AppShell>
        <main className="min-h-[500px]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="soc-heading mb-3">Live Attack Map</h3>
              {/* Map container - would integrate with mapping service */}
              <div className="soc-panel h-[400px] border-t border-border bg-card">
                Map visualization area
              </div>
            </div>
            <div>
              <h3 className="soc-heading mb-3">Attack Statistics</h3>
              <DataTable
                data={attacks}
                columns={[
                  { header: "Time", cell: (d) => d.time },
                  { header: "Source", cell: (d) => d.source },
                  { header: "Type", cell: (d) => d.type },
                  { header: "Severity", cell: (d) => <StatusBadge kind={d.severity} /> },
                ]}
                rows={attacks.length}
                emptyState={<EmptyState title="No active attacks" />}
              />
            </div>
          </div>
        </main>
      </AppShell>
    </div>
  );
}