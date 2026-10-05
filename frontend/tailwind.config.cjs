/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soc: {
          canvas: "#020b1c",
          sidebar: "#03152b",
          topbar: "#041326",
          panel: "#071426",
          panelSoft: "#0a1d35",
          cyan: "#22d3ee",
          blue: "#2563eb",
          border: "#164e63",
          muted: "#64748b",
        },
      },
      boxShadow: {
        "soc-panel":
          "0 0 18px rgba(0, 120, 255, 0.08)",
        "soc-glow":
          "0 0 22px rgba(34, 211, 238, 0.18)",
        "soc-blue":
          "0 0 24px rgba(37, 99, 235, 0.22)",
      },
    },
  },
  plugins: [],
};