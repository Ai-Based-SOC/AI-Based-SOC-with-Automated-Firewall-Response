function MetricCard({
  title,
  value,
  subtitle,
  icon,
  valueClass = "text-white",
  trend,
  trendClass = "text-green-400",
}) {
  return (
    <div className="relative overflow-hidden rounded-md border border-cyan-800/80 bg-[#061a32] px-3 py-2.5 shadow-[0_0_12px_rgba(0,120,255,0.08)]">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="truncate text-[8px] font-semibold uppercase tracking-wide text-slate-400">
            {title}
          </p>

          <p className={`mt-1 text-2xl font-bold leading-none ${valueClass}`}>
            {value}
          </p>

          <p className="mt-1 truncate text-[8px] text-slate-500">
            {subtitle}
          </p>
        </div>

        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-slate-800/80 text-sm">
          {icon}
        </div>
      </div>

      <div className="mt-1 flex justify-end text-[9px]">
        <span className={trendClass}>↗ {trend}</span>
      </div>

      <div className="absolute bottom-0 left-0 h-px w-full bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent" />
    </div>
  );
}