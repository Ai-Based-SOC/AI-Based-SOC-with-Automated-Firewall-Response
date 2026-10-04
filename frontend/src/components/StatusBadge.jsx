import React from "react";

export function StatusBadge({ status, variant = "info", size = "sm" }) {
  const variants = {
    info: "bg-cyan-600/20 text-cyan-400 border-cyan-500",
    warning: "bg-amber-600/20 text-amber-400 border-amber-500",
    good: "bg-green-600/20 text-green-400 border-green-500",
    critical: "bg-red-600/20 text-red-400 border-red-500",
  };

  const sizeStyles = {
    sm: "h-6 w-6 text-xs",
    md: "h-8 w-8 text-sm",
    lg: "h-10 w-10 text-base",
  };

  return (
    <span
      className={`
        inline-flex items-center justify-center ${variants[variant] || variants.info}
        rounded ${sizeStyles[size] || sizeStyles.sm}
      `}
    >
      {status}
    </span>
  );
}