import { useEffect, useMemo, useState } from "react";
import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import { getAttacksApi, generateReportApi } from "../services/api";

export default function ReportsPage({ profile, onLogout }) {
  const [attacks, setAttacks] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await getAttacksApi(200);
        const rows = Array.isArray(data) ? data : [];
        setAttacks(rows);
        if (rows.length) setSelectedIncident(rows[0].id || "");
      } catch {
        setAttacks([]);
      }
    })();
  }, []);

  const highRisk = useMemo(() => attacks.filter((a) => (a.risk_score ?? 0) >= 70), [attacks]);

  const onGenerate = async () => {
    if (!selectedIncident) {
      setStatus("No incident_id selected.");
      return;
    }
    setBusy(true);
    setStatus("");
    try {
      const { data } = await generateReportApi(selectedIncident);
      setStatus(`Report generated: ${data?.report_name || data?.message || "success"}`);
      if (data?.report_path) {
        window.open(`http://127.0.0.1:8001/${data.report_path.replace(/^\/+/, "")}`, "_blank");
      }
    } catch (e) {
      const d = e?.response?.data;
      setStatus(`Generate failed: ${typeof d === "string" ? d : JSON.stringify(d)}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageShell title="MITRE ATT&CK Mapping & Threat Intelligence" profile={profile} onLogout={onLogout}>
      <div className="grid xl:grid-cols-3 gap-4">
        <Panel title="Top Incidents (pick one for report)" className="xl:col-span-2">
          {attacks.length === 0 ? (
            <div className="text-slate-400">No incidents available. Create attacks first.</div>
          ) : (
            <div className="space-y-2 max-h-72 overflow-auto">
              {attacks.slice(0, 30).map((a, i) => (
                <label key={a.id ?? `${a.source_ip}-${i}`} className="flex items-center gap-3 p-2 rounded border border-slate-700">
                  <input
                    type="radio"
                    name="incident"
                    checked={selectedIncident === a.id}
                    onChange={() => setSelectedIncident(a.id)}
                  />
                  <span className="text-sm">
                    <b>{a.attack_type}</b> | {a.source_ip} → {a.destination_ip} | Sev: {a.severity} | ID: {a.id}
                  </span>
                </label>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Threat Intelligence Feed">
          <ul className="space-y-2 text-sm text-slate-300 mb-4">
            <li>Total incidents: {attacks.length}</li>
            <li>High risk (&gt;=70): {highRisk.length}</li>
            <li>Selected incident: {selectedIncident || "None"}</li>
          </ul>

          <button onClick={onGenerate} disabled={busy} className="px-3 py-2 rounded bg-cyan-700 hover:bg-cyan-600 disabled:opacity-60">
            {busy ? "Generating..." : "Generate PDF Report"}
          </button>

          {status && <p className="mt-3 text-xs text-amber-300">{status}</p>}
        </Panel>
      </div>
    </PageShell>
  );
}