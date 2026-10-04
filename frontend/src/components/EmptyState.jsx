import React from "react";

export function EmptyState({ title, description, icon,CTA }) {
  return (
    <div className="soc-empty-state text-center py-16">
      <div className="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor" className="mx-auto mb-4">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l8-4 8 4v-18c0-1.1-.9-2-2-2zm-6 15.5a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7zM9 10h6v2H9v-2zm3.5 5.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z" />
        </svg>
      </div>
      <h3 className="text-xl font-bold text-slate-100 mb-2">{title}</h3>
      <p className="text-slate-500 text-base">{description}</p>
      {CTA && (
        <div className="mt-6">
          {CTA}
        </div>
      )}
    </div>
  );
}