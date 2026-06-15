import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Editorial Atelier — warm paper, ink, terracotta seal accent
        paper: "#F4F0E7",
        "paper-deep": "#ECE6D9",
        surface: "#FCFAF5",
        "surface-2": "#F2EDE2",
        ink: "#211E19",
        "ink-soft": "#615A4E",
        muted: "#938A7B",
        line: "#E3DBCC",
        "line-soft": "#EDE7DA",
        accent: "#A8512E",
        "accent-deep": "#8E4426",
        "accent-soft": "#C98A63",
        "accent-wash": "#F3E7DC",
        sage: "#5F6F57",
        clay: "#B0843F",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Songti SC", "Georgia", "serif"],
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"PingFang SC"',
          '"Microsoft YaHei"',
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(33,30,25,0.04), 0 6px 20px -12px rgba(33,30,25,0.14)",
        card: "0 1px 0 rgba(33,30,25,0.02), 0 10px 34px -20px rgba(33,30,25,0.22)",
        lift: "0 18px 50px -22px rgba(33,30,25,0.34)",
      },
      borderRadius: {
        xl2: "16px",
      },
      letterSpacing: {
        tightish: "-0.012em",
      },
    },
  },
  plugins: [],
};

export default config;
