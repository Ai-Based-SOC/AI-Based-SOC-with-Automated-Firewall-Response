/** @type {import('tailwindcss').Config} */
export default {
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

      backgroundImage: {
        "soc-grid":
          "linear-gradient(rgba(34, 211, 238, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(34, 211, 238, 0.06) 1px, transparent 1px)",
        "soc-radial":
          "radial-gradient(circle at 50% 0%, rgba(8, 47, 73, 0.35), transparent 60%)",
      },

      backgroundSize: {
        "grid-sm": "24px 24px",
        "grid-md": "32px 32px",
      },

      borderRadius: {
        soc: "0.75rem",
      },

      transitionTimingFunction: {
        "soc-in": "cubic-bezier(0.22, 1, 0.36, 1)",
      },

      animation: {
        "soc-pulse": "soc-pulse-glow 2.4s ease-in-out infinite",
        "soc-data-in": "soc-data-in 260ms ease-out",
      },

      keyframes: {
        "soc-pulse-glow": {
          "0%, 100%": {
            boxShadow: "0 0 0 rgba(34, 211, 238, 0)",
          },
          "50%": {
            boxShadow: "0 0 24px rgba(34, 211, 238, 0.18)",
          },
        },

        "soc-data-in": {
          from: {
            opacity: "0",
            transform: "translateY(-5px)",
          },
          to: {
            opacity: "1",
            transform: "translateY(0)",
          },
        },
      },
    },
  },

  plugins: [],
};