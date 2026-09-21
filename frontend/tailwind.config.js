/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        beige: {
          DEFAULT: "#F2EFE7",
          soft: "#FBFAF6",
          deep: "#E8E2D3",
        },
        teal: {
          DEFAULT: "#4B6B7C",
          dark: "#34505F",
          light: "#A9C1CB",
          tint: "#E4EDF0",
        },
        sky: {
          DEFAULT: "#C8D9E6",
          dark: "#7FA8C2",
          light: "#E3EDF4",
          tint: "#F1F6F9",
        },
        ink: {
          DEFAULT: "#2E3A40",
          soft: "#5C6B70",
          faint: "#94A3A8",
        },
        clay: {
          DEFAULT: "#C97B5B",
          dark: "#A85F42",
          light: "#EBC3AE",
          tint: "#FBEEE7",
        },
        amber: {
          DEFAULT: "#D9A441",
          dark: "#B3832A",
          light: "#EFD6A0",
          tint: "#FBF2DE",
        },
        moss: {
          DEFAULT: "#4E9C82",
          dark: "#397A64",
          light: "#BFE0D2",
          tint: "#E9F6F1",
        },
        signal: {
          positive: "#4E9C82",
          negative: "#C97B5B",
          neutral: "#D9A441",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "'Georgia'", "serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'Space Grotesk'", "monospace"],
      },
      boxShadow: {
        card: "0 2px 14px rgba(46, 58, 64, 0.07)",
        pop: "0 8px 24px rgba(75, 107, 124, 0.22)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      letterSpacing: {
        widest2: "0.18em",
      },
      backgroundImage: {
        "brand-glow": "linear-gradient(135deg, #4B6B7C 0%, #7FA8C2 55%, #C8D9E6 100%)",
      },
    },
  },
  plugins: [],
};
