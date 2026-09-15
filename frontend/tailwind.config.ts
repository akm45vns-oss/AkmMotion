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
        // Semantic brand accent: Burnt Orange / Warm Copper
        brand: {
          DEFAULT: "#E76536",
          hover: "#F07847",
          light: "#F5936B",
          subtle: "rgba(231, 101, 54, 0.12)",
          border: "rgba(231, 101, 54, 0.28)",
          dark: "#9E3C1B",
        },
        // Workstation surfaces: Deep Charcoal / Near-Black
        surface: {
          canvas: "#0D0E0E",
          DEFAULT: "#151616",
          elevated: "#1B1C1C",
          active: "#232424",
          border: "#292A29",
          "border-strong": "#383938",
        },
        // Functional indicators
        status: {
          success: "#4FAE7B",
          "success-subtle": "rgba(79, 174, 123, 0.12)",
          warning: "#C99545",
          "warning-subtle": "rgba(201, 149, 69, 0.12)",
          error: "#C95C5C",
          "error-subtle": "rgba(201, 92, 92, 0.12)",
          info: "#5C8BC9",
        },
        // Text & Neutral scale
        neutral: {
          50: "#FAF7F2",
          100: "#F5F1E8",
          200: "#D6D1C7",
          300: "#A9A49B",
          400: "#77746E",
          500: "#524F4A",
          600: "#383633",
          700: "#242322",
          800: "#151616",
          900: "#0D0E0E",
        },
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "10px",
        xl: "12px",
        "2xl": "14px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
