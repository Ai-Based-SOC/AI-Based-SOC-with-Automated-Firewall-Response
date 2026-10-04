import Panel from "../components/Panel";
export default function ThreatIntelligencePage({ profile }) {
  return (
    <div className="min-h-screen bg-[#020b1c] text-white p-6">
      <h1 className="soc-heading mb-6">Threat Intelligence</h1>
      <Panel title="IOC Lookup">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <input
              type="text"
              placeholder="Enter IP or hash"
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 outline-none focus:border-cyan-500"
            />
          </div>
          <button className="soc-btn">Check</button>
        </div>
      </Panel>
      <Panel title="IOC Statistics">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-slate-400">Total IOCs</div>
            <div className="text-xl font-medium text-cyan-400">{totalIOCs}</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Malicious</div>
            <div className="text-xl font-medium text-red-400">{maliciousIOCs}</div>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <div className="text-sm text-slate-400">By Type</div>
            <div className="text-muted-foreground">IP: 890</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">By Type</div>
            <div className="text-muted-foreground">Hash: 412</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">By Type</div>
            <div className="text-muted-foreground">Domain: 240</div>
          </div>
        </div>
      </Panel>
      <Panel title="Threat Feed">
        <ul className="space-y-2 text-sm text-slate-300">
          <li>New IOCs last 24h: {newIOCs}</li>
          <li>Botnet takedowns: {botnetTakedowns}</li>
          <li>New C2 domains: {newC2Domains}</li>
        </ul>
      </Panel>
      <div className="mt-8 pt-8 border-t border-slate-700/40">
        <h2 className="soc-heading mb-4">Sources</h2>
        <div className="space-y-2">
          <span className="soc-chip">AbuseIPDB</span>
          <span className="soc-chip">VirusTotal</span>
          <span className="soc-chip">AlienVault</span>
          <span className="soc-chip">OpenCTI</span>
        </div>
      </div>
    </div>
  );
}