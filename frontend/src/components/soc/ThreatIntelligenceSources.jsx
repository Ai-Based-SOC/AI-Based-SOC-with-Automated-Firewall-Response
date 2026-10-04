import Panel from "../Panel";

const SOURCE_NAMES = ["Internal IDS", "OSINT Feed", "YARA Engine", "ML Detector", "SIEM Correlation"];

export default function ThreatIntelligenceSources({ attacks }) {
  const counts = SOURCE_NAMES.map((name, index) => ({
    name,
    value: attacks.filter((item) => (item?.id ? Number(String(item.id).length % SOURCE_NAMES.length) : 0) === index).length,
  }));

  return (
    <Panel title="Threat Intelligence Sources" className="bg-[#071a2f] border-cyan-900/60">
      <div className="space-y-2 text-xs">
        {counts.map((item) => (
          <div key={item.name} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/40 px-3 py-2">
            <span className="text-slate-300">{item.name}</span>
            <span className="text-cyan-300">{item.value}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
