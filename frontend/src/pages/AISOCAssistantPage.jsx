import Panel from "../components/Panel";
export default function AISOCAssistantPage({ profile }) {
  return (
    <div className="min-h-screen bg-[#020b1c] text-white p-6">
      <h1 className="soc-heading mb-6">AI SOC Assistant</h1>
      <Panel title="Risk Assessment">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-sm text-slate-400">Severity</div>
            <div className="text-2xl font-medium text-red-400">Critical</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Confidence</div>
            <div className="text-2xl font-medium text-cyan-400">94%</div>
          </div>
        </div>
        <div className="mt-4 p-4 bg-slate-800 rounded border border-slate-700">
          <div className="font-medium text-slate-300">Based on telemetry analysis, the following risk factors were identified:</div>
          <ul className="mt-2 space-y-1 text-sm text-slate-400">
            <li>Unusual login time detected (02:45)</li>
            <li>Multiple failed authentication attempts</li>
            <li>Access from unfamiliar geolocation</li>
          </ul>
        </div>
      </Panel>
      <Panel title="Recommended Response">
        <ol className="list-decimal list-inside space-y-3 text-slate-300">
          <li>Immediately revoke active sessions for the affected user</li>
          <li>Reset the user's credentials and enforce MFA</li>
          <li>Block the source IP at the firewall level</li>
          <li> escalate to tier-2 for manual investigation</li>
          <li>Add IOC to threat intelligence feed</li>
        </ol>
      </Panel>
      <Panel title="AI Model Metrics">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-slate-400">Accuracy</div>
            <div className="text-2xl font-medium text-cyan-400">91%</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Precision</div>
            <div className="text-2xl font-medium text-cyan-400">87%</div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <div className="text-sm text-slate-400">Recall</div>
            <div className="text-2xl font-medium text-cyan-400">89%</div>
          </div>
          <div>
            <div className="text-sm text-slate-400">F1 Score</div>
            <div className="text-2xl font-medium text-cyan-400">88%</div>
          </div>
        </div>
      </Panel>
      <div className="mt-8 pt-8 border-t border-slate-700/40">
        <h2 className="soc-heading mb-4">Actions</h2>
        <div className="space-y-2">
          <button className="soc-btn">New Analysis</button>
          <button className="soc-btn soc-btn-secondary">Export Findings</button>
        </div>
      </div>
    </div>
  );
}