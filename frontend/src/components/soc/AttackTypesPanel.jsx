import Panel from "../Panel";

export default function AttackTypesPanel({ data }) {
  const maxValue = Math.max(1, ...data.map((item) => item.value));

  return (
    <Panel title="Attack Types" className="bg-[#071a2f] border-cyan-900/60">
      <div className="space-y-3">
        {data.length === 0 ? (
          <p className="text-xs text-slate-400">No attack type data yet.</p>
        ) : (
          data.map((item) => (
            <div key={item.name}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-slate-200">{item.name}</span>
                <span className="text-cyan-300">{item.value}</span>
              </div>
              <div className="h-2 rounded bg-slate-800">
                <div
                  className="h-2 rounded bg-gradient-to-r from-cyan-400 to-blue-500"
                  style={{ width: `${Math.max(8, (item.value / maxValue) * 100)}%` }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
