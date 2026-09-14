import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    screens: {
      xs: "375px",
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      "2xl": "1440px",
    },
    container: {
      center: true,
      padding: "1.5rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Semantic brand accent: Warm Copper / Burnt Orange
        brand: {
          DEFAULT: "#E0693B",
          hover: "#EB794D",
          light: "#F49D77",
          subtle: "rgba(224, 105, 59, 0.12)",
          border: "rgba(224, 105, 59, 0.28)",
          dark: "#933917",
        },
        // Warm charcoal surfaces
        surface: {
          canvas: "#0C0D0E",
          DEFAULT: "#141517",
          elevated: "#1B1D21",
          active: "#23262C",
          border: "#24272E",
          "border-strong": "#333742",
        },
        // Muted status indicators
        status: {
          success: "#2EB88A",
          "success-subtle": "rgba(46, 184, 138, 0.12)",
          warning: "#E5A43B",
          "warning-subtle": "rgba(229, 164, 59, 0.12)",
          error: "#E55353",
          "error-subtle": "rgba(229, 83, 83, 0.12)",
          info: "#4F89E8",
        },
        // Neutral text and UI scale
        neutral: {
          50: "#FAF9F7",
          100: "#F2F2F3",
          200: "#D3D5DC",
          300: "#9FA3AD",
          400: "#646875",
          500: "#454852",
          600: "#2E313A",
          700: "#1E2026",
          800: "#141517",
          900: "#0C0D0E",
        },
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
        "3xl": "20px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
