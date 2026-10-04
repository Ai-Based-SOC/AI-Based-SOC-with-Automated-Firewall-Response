import React from "react";

export function LoadingState({ title = "Loading", description = "Please wait..." }) {
  return (
    <div className="soc-loading-state text-center py-16">
      <div className="loading-spinner mx-auto mb-4 animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500" />
      <h3 className="text-xl font-bold text-slate-100 mb-2">{title}</h3>
      <p className="text-slate-500 text-base">{description}</p>
    </div>
  );
}