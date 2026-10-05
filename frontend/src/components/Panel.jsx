export default function Panel({
  title,
  icon,
  children,
  className = "",
}) {
  return (
    <section
      className={`overflow-hidden rounded-xl border border-cyan-900/70 bg-[#071426] shadow-[0_0_18px_rgba(0,120,255,0.08)] ${className}`}
    >
      {title && (
        <div className="flex items-center gap-2 border-b border-cyan-900/70 px-4 py-3">
          {icon && <span className="text-cyan-300">{icon}</span>}
          <h2 className="text-sm font-semibold text-white">{title}</h2>
        </div>
      )}

      <div className="p-4">{children}</div>
    </section>
  );
}