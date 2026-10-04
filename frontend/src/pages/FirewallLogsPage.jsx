export default function FirewallLogsPage({ profile }) {
  return (
    <div className="min-h-screen bg-[#020b1c] text-white p-6">
      <h1 className="soc-heading mb-6">Firewall & Logs</h1>
      <Panel title="Firewall Rules">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-sm text-slate-400">Rule Name</div>
            <div className="text-cyan-400 font-mono">SSH-allow-22</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Status</div>
            <StatusBadge status="active" variant="good" size="sm" />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <div className="text-sm text-slate-400">Action</div>
            <div>Allow</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Protocol</div>
            <div>TCP</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Port</div>
            <div>22</div>
          </div>
        </div>
      </Panel>
      <Panel title="Recent Log Entries">
        <div className="h-64 overflow-auto">
          {[
            { time: "02:34", src: "10.10.10.50", dst: "172.16.0.1", rule: "SSH-allow-22", action: "blocked" },
            { time: "02:33", src: "192.168.1.100", dst: "10.0.0.5", rule: "HTTP-allow-80", action: "allowed" },
            { time: "02:32", src: "172.16.0.25", dst: "10.0.0.10", rule: "DNS-block", action: "blocked" },
          ].map((l, i) => (
            <div key={l.time} className="flex items-center justify-between border-b border-slate-700/50 py-2">
              <span className="text-slate-400 text-sm">{l.time}</span>
              <span className="font-mono text-cyan-400 text-sm">{l.src} → {l.dst}</span>
              <StatusBadge status={l.action === "blocked" ? "critical" : "info"} size="sm" />
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Firewall Statistics">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-slate-400">Total Rules</div>
            <div className="text-xl font-medium text-cyan-400">87</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Active</div>
            <div className="text-xl font-medium text-green-400">52</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Blocked Today</div>
            <div className="text-xl font-medium text-red-400">128</div>
          </div>
        </div>
      </Panel>
      <div className="mt-8 pt-8 border-t border-slate-700/40">
        <h2 className="soc-heading mb-4">Quick Actions</h2>
        <div className="space-y-2">
          <button className="soc-btn">Add Rule</button>
          <button className="soc-btn soc-btn-secondary">Import Logs</button>
        </div>
      </div>
    </div>
  );
}