import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Download,
  FileBarChart,
  FileText,
  RefreshCw,
} from "lucide-react";

import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import {
  generateReportApi,
  getAttacksApi,
} from "../services/api";
import { connectAttackSocket } from "../services/socket";

function normalizeAttacks(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.attacks)) return payload.attacks;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;

  return [];
}

function getAttackKey(attack) {
  return (
    attack?.id ||
    attack?._id ||
    [
      attack?.source_ip || "",
      attack?.timestamp || attack?.created_at || "",
      attack?.attack_type || "",
    ].join("|")
  );
}

function mergeAttacks(incoming, current) {
  const seen = new Set();

  return [...incoming, ...current]
    .filter((attack) => {
      const key = getAttackKey(attack);

      if (seen.has(key)) {
        return false;
      }

      seen.add(key);
      return true;
    })
    .slice(0, 1000);
}

function getApiOrigin() {
  const apiUrl =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000/api/v1";

  return apiUrl.replace(/\/api\/v1\/?$/, "");
}

export default function ReportsPage({
  profile,
  onLogout,
}) {
  const [attacks, setAttacks] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState("");
  const [reportType, setReportType] = useState("incident");
  const [dateRange, setDateRange] = useState("30d");
  const [reportEvents, setReportEvents] = useState([]);
  const [realtimeStatus, setRealtimeStatus] = useState(
    "Connecting"
  );
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const loadAttacks = useCallback(async () => {
    try {
      const response = await getAttacksApi(500);
      const rows = normalizeAttacks(response?.data ?? response);

      setAttacks((current) => mergeAttacks(rows, current));

      setSelectedIncident((current) => {
        if (current || !rows.length) {
          return current;
        }

        return rows[0]?.id || "";
      });
    } catch (requestError) {
      console.error("Reports loading error:", requestError);
      setError("Unable to load report incidents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAttacks();

    const timer = window.setInterval(loadAttacks, 10000);

    return () => {
      window.clearInterval(timer);
    };
  }, [loadAttacks]);

  useEffect(() => {
    const disconnect = connectAttackSocket({
      onOpen: () => {
        setRealtimeStatus("Live");
      },

      onClose: () => {
        setRealtimeStatus("Polling");
      },

      onError: () => {
        setRealtimeStatus("Polling");
      },

      onMessage: (message) => {
        if (message?.event === "new_attack") {
          const attack =
            message.data ||
            message.attack ||
            message.item;

          if (attack) {
            setAttacks((current) =>
              mergeAttacks([attack], current)
            );
          }

          return;
        }

        if (message?.event === "report_generated") {
          const report = message.data || message.payload;

          if (!report) return;

          setReportEvents((current) => [
            report,
            ...current,
          ].slice(0, 30));

          setStatus(
            `Report generated: ${
              report.report_name || "new report"
            }`
          );

          return;
        }

        if (message?.event === "report_failed") {
          const failure = message.data || message.payload;

          setError(
            failure?.message ||
              "Report generation failed."
          );
        }
      },
    });

    return () => {
      disconnect?.();
    };
  }, []);

  const selectedAttack = useMemo(() => {
    return attacks.find(
      (attack) =>
        String(attack?.id) === String(selectedIncident)
    );
  }, [attacks, selectedIncident]);

  const highRiskCount = useMemo(() => {
    return attacks.filter(
      (attack) => Number(attack?.risk_score || 0) >= 70
    ).length;
  }, [attacks]);

  const criticalCount = useMemo(() => {
    return attacks.filter(
      (attack) =>
        String(attack?.severity || "").toLowerCase()
        === "critical"
    ).length;
  }, [attacks]);

  async function generateReport() {
    if (!selectedIncident) {
      setError("Select an incident first.");
      return;
    }

    setBusy(true);
    setError("");
    setStatus("");

    try {
      const response = await generateReportApi(
        selectedIncident
      );

      const report = response.data;

      setStatus(
        `Report generated: ${
          report?.report_name || "incident report"
        }`
      );

      if (report?.report_path) {
        const cleanPath = String(report.report_path).replace(
          /^\/+/,
          ""
        );

        window.open(
          `${getApiOrigin()}/${cleanPath}`,
          "_blank",
          "noopener,noreferrer"
        );
      }
    } catch (requestError) {
      setError(
        requestError?.response?.data?.detail ||
          requestError?.response?.data?.error?.message ||
          "Report generation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  function downloadJsonReport() {
    if (!selectedAttack) {
      setError("Select an incident first.");
      return;
    }

    const blob = new Blob(
      [JSON.stringify(selectedAttack, null, 2)],
      {
        type: "application/json",
      }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `incident-${
      selectedAttack.id || "report"
    }.json`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);

    setStatus("JSON report downloaded.");
  }

  return (
    <PageShell
      title="Reports"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto max-w-[1600px] space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">Reports</h2>
            <p className="text-sm text-slate-400">
              Generate and manage security reports
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`rounded-full border px-3 py-1 text-[10px] ${
                realtimeStatus === "Live"
                  ? "border-green-500/30 bg-green-500/10 text-green-300"
                  : "border-yellow-500/30 bg-yellow-500/10 text-yellow-300"
              }`}
            >
              ● Reports {realtimeStatus}
            </span>

            <button
              type="button"
              onClick={loadAttacks}
              className="flex items-center gap-2 rounded-lg border border-cyan-900 px-3 py-2 text-xs text-cyan-300 hover:bg-cyan-950"
            >
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {status && (
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-300">
            {status}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              Total Incidents
            </p>
            <p className="mt-2 text-2xl font-bold text-cyan-300">
              {attacks.length}
            </p>
          </div>

          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              High Risk
            </p>
            <p className="mt-2 text-2xl font-bold text-orange-300">
              {highRiskCount}
            </p>
          </div>

          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              Critical
            </p>
            <p className="mt-2 text-2xl font-bold text-red-300">
              {criticalCount}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <Panel
            title="Report Configuration"
            icon={<FileBarChart size={16} />}
          >
            <div className="space-y-4">
              <label className="block text-sm text-slate-400">
                Report Type

                <select
                  value={reportType}
                  onChange={(event) =>
                    setReportType(event.target.value)
                  }
                  className="mt-1 w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
                >
                  <option value="incident">
                    Incident Report
                  </option>
                  <option value="threat">
                    Threat Analysis Report
                  </option>
                  <option value="firewall">
                    Firewall Activity Report
                  </option>
                  <option value="system">
                    System Health Report
                  </option>
                </select>
              </label>

              <label className="block text-sm text-slate-400">
                Time Range

                <select
                  value={dateRange}
                  onChange={(event) =>
                    setDateRange(event.target.value)
                  }
                  className="mt-1 w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
                >
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                  <option value="all">
                    All Available Data
                  </option>
                </select>
              </label>

              <label className="block text-sm text-slate-400">
                Incident

                <select
                  value={selectedIncident}
                  onChange={(event) =>
                    setSelectedIncident(event.target.value)
                  }
                  className="mt-1 w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
                >
                  <option value="">
                    Select incident
                  </option>

                  {attacks.map((attack, index) => (
                    <option
                      key={
                        attack?.id ||
                        `${attack?.source_ip}-${index}`
                      }
                      value={attack?.id || ""}
                    >
                      {attack?.attack_type ||
                        "Security Event"}{" "}
                      — {attack?.source_ip || "Unknown"}
                    </option>
                  ))}
                </select>
              </label>

              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={generateReport}
                  disabled={busy || loading}
                  className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold hover:bg-blue-500 disabled:opacity-50"
                >
                  <FileText size={15} />
                  {busy ? "Generating..." : "Generate PDF"}
                </button>

                <button
                  type="button"
                  onClick={downloadJsonReport}
                  disabled={!selectedAttack}
                  className="flex items-center justify-center gap-2 rounded-lg border border-cyan-800 px-3 py-2 text-sm text-cyan-300 hover:bg-cyan-950 disabled:opacity-50"
                >
                  <Download size={15} />
                  JSON Export
                </button>
              </div>
            </div>
          </Panel>

          <Panel
            title="Selected Incident"
            className="xl:col-span-2"
          >
            {!selectedAttack ? (
              <div className="flex min-h-[240px] items-center justify-center text-sm text-slate-500">
                Select an incident to view report details.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs text-slate-500">
                    Attack Type
                  </p>
                  <p className="mt-1 text-lg font-semibold">
                    {selectedAttack.attack_type ||
                      "Security Event"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Severity
                  </p>
                  <p className="mt-1 capitalize text-red-300">
                    {selectedAttack.severity || "low"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Source IP
                  </p>
                  <p className="mt-1 font-mono text-cyan-300">
                    {selectedAttack.source_ip || "--"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Risk Score
                  </p>
                  <p className="mt-1 text-orange-300">
                    {selectedAttack.risk_score ?? "--"}
                  </p>
                </div>

                <div className="md:col-span-2">
                  <p className="text-xs text-slate-500">
                    Detection Reason
                  </p>
                  <p className="mt-1 text-sm leading-6 text-slate-300">
                    {selectedAttack.reason ||
                      selectedAttack.description ||
                      "No reason provided."}
                  </p>
                </div>
              </div>
            )}
          </Panel>
        </div>

        <Panel title="Live Report Activity">
          {reportEvents.length === 0 ? (
            <p className="text-sm text-slate-500">
              Waiting for report events...
            </p>
          ) : (
            <div className="space-y-2">
              {reportEvents.map((report, index) => (
                <div
                  key={`${report.report_name}-${index}`}
                  className="rounded-lg border border-cyan-900 bg-[#041326] p-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-slate-200">
                      {report.report_name ||
                        "Generated report"}
                    </p>

                    <span className="text-xs text-green-300">
                      Generated
                    </span>
                  </div>

                  <p className="mt-1 text-xs text-slate-500">
                    Incident: {report.incident_id || "Unknown"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Recent Incidents">
          <div className="overflow-x-auto">
            <table className="min-w-[850px] w-full text-left text-xs">
              <thead className="border-b border-cyan-900/70 text-slate-500">
                <tr>
                  <th className="px-3 py-3">Incident</th>
                  <th className="px-3 py-3">Source IP</th>
                  <th className="px-3 py-3">Type</th>
                  <th className="px-3 py-3">Severity</th>
                  <th className="px-3 py-3">Risk</th>
                  <th className="px-3 py-3">Action</th>
                </tr>
              </thead>

              <tbody>
                {attacks.slice(0, 30).map((attack, index) => (
                  <tr
                    key={
                      attack?.id ||
                      `${attack?.source_ip}-${index}`
                    }
                    className="border-b border-cyan-950 hover:bg-cyan-950/40"
                  >
                    <td className="px-3 py-3 text-slate-300">
                      {attack?.id || `INC-${index + 1}`}
                    </td>

                    <td className="px-3 py-3 font-mono text-cyan-300">
                      {attack?.source_ip || "--"}
                    </td>

                    <td className="px-3 py-3 text-slate-300">
                      {attack?.attack_type || "--"}
                    </td>

                    <td className="px-3 py-3 capitalize text-red-300">
                      {attack?.severity || "low"}
                    </td>

                    <td className="px-3 py-3 text-orange-300">
                      {attack?.risk_score ?? "--"}
                    </td>

                    <td className="px-3 py-3 text-green-300">
                      {attack?.action_taken || "Detected"}
                    </td>
                  </tr>
                ))}

                {!attacks.length && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-3 py-10 text-center text-slate-500"
                    >
                      No incidents available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </PageShell>
  );
}