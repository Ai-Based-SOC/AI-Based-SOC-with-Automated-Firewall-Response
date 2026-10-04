function SocPanel({ title, icon, children, className = "" }) {
  return (
    <section
      className={`overflow-hidden rounded-md border border-cyan-800/80 bg-[#061a32] shadow-[0_0_14px_rgba(0,120,255,0.08)] ${className}`}
    >
      <div className="flex items-center gap-2 border-b border-cyan-900/70 px-3 py-2">
        <span className="text-cyan-400">{icon}</span>

        <h2 className="text-[11px] font-semibold text-slate-200">
          {title}
        </h2>
      </div>

      <div className="p-2.5">{children}</div>
    </section>
  );
}