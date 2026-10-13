/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#04060d",
          900: "#060912",
          850: "#080d1b",
          800: "#0b1122",
          700: "#111a33",
          600: "#1a2547",
        },
        accent: {
          DEFAULT: "#4f8cff",
          soft: "#7aa7ff",
          deep: "#2f6fe0",
        },
        violet: {
          DEFAULT: "#8b5cf6",
          soft: "#a78bfa",
        },
        cyan: {
          DEFAULT: "#22d3ee",
        },
        mist: {
          DEFAULT: "#9fb0d0",
          soft: "#6f7f9e",
          bright: "#e7edff",
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      opacity: {
        6: "0.06",
        7: "0.07",
        8: "0.08",
        12: "0.12",
        15: "0.15",
        35: "0.35",
        65: "0.65",
      },
      maxWidth: {
        shell: "76rem",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(79,140,255,.18), 0 18px 60px -20px rgba(47,111,224,.55)",
        card: "0 24px 60px -40px rgba(0,0,0,.9)",
      },
      backgroundImage: {
        "grid-fade":
          "radial-gradient(circle at 1px 1px, rgba(122,167,255,.16) 1px, transparent 0)",
      },
      keyframes: {
        float: {
          "0%,100%": { transform: "translate3d(0,0,0)" },
          "50%": { transform: "translate3d(0,-10px,0)" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translate3d(0,18px,0)" },
          "100%": { opacity: "1", transform: "translate3d(0,0,0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        float: "float 9s ease-in-out infinite",
        "fade-up": "fade-up .7s cubic-bezier(.22,1,.36,1) both",
        shimmer: "shimmer 6s linear infinite",
      },
    },
  },
  plugins: [],
};
