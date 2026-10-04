import Panel from "../components/Panel";
export default function SecurityLogsPage({ profile }) {
  return (
    <div className="min-h-screen bg-[#020b1c] text-white p-6">
      <h1 className="soc-heading mb-6">Security Logs</h1>
      <Panel title="Recent Log Entries">
        <div className="h-80 overflow-auto">
          {[
            { time: "02:45:12", source: "auth-server", event: "failed_login", detail: "Failed login attempt from 10.10.10.50", source_ip: "10.10.10.50" },
            { time: "02:44:58", source: "web-gateway", event: "malware_detected", detail: "Malware detected in download from 172.16.0.25", source_ip: "172.16.0.25" },
            { time: "02:44:12", source: "firewall", event: "rule_violation", detail: "Outbound connection to known C2 server blocked", source_ip: "192.168.1.50" },
            { time: "02:43:30", source: "endpoint", event: "privilege_escalation", detail: "Process escalation detected on 198.51.100.42", source_ip: "198.51.100.42" },
          ].map((l, i) => (
            <div key={i} className="flex items-start justify-between border-b border-slate-700/50 py-3">
              <div className="flex items-center gap-3 w-64">
                <span className="text-slate-500 text-sm">{l.time}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-mono text-slate-300 text-sm truncate">{l.event}</div>
                <div className="text-xs text-slate-500">{l.detail}</div>
              </div>
              <StatusBadge status="info" size="sm" />
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Log Statistics">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-slate-400">Total Events</div>
            <div className="text-xl font-medium text-cyan-400">1247</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Critical</div>
            <div className="text-xl font-medium text-red-400">47</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Warnings</div>
            <div className="text-xl font-medium text-amber-400">128</div>
          </div>
        </div>
      </Panel>
      <Panel title="Log Sources">
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div>
            <div className="soc-chip">Auth Server</div>
          </div>
          <div>
            <div className="soc-chip">Web Gateway</div>
          </div>
          <div>
            <div className="soc-chip">Firewall</div>
          </div>
          <div>
            <div className="soc-chip">Endpoints</div>
          </div>
        </div>
      </Panel>
      <div className="mt-8 pt-8 border-t border-slate-700/40">
        <h2 className="soc-heading mb-4">Actions</h2>
        <div className="space-y-2">
          <button className="soc-btn">Search Logs</button>
          <button className="soc-btn soc-btn-secondary">Export Logs</button>
        </div>
      </div>
    </div>
  );
}