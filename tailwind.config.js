/** @type {import('tailwindcss').Config} */

import colors from "tailwindcss/colors";

export default {
  content: ["client/**/*.{html,js,vue}"],
  theme: {
    fontFamily: {
      sans: ["Noto Sans JP", "Poppins", "sans-serif"],
    },
    screens: {
      sm: "640px",
      md: "768px",
      lg: "1024px",
    },
    extend: {
      colors: {
        // Dynamic
        "theme-brand": "var(--theme-brand)",
        "theme-brand-dark": "var(--theme-brand-dark)",
        "theme-brand-accent": "var(--theme-brand-accent)",
        "theme-background": "var(--theme-background)",
        "theme-background-surface": "var(--theme-background-surface)",
        "theme-background-subtle": "var(--theme-background-subtle)",
        "theme-background-elevated": "var(--theme-background-elevated)",
        "theme-text": "var(--theme-text)",
        "theme-text-muted": "var(--theme-text-muted)",
        "theme-shadow-sm": "var(--theme-shadow-sm)",
        "theme-shadow-md": "var(--theme-shadow-md)",
        "theme-shadow-lg": "var(--theme-shadow-lg)",
        "theme-border": "var(--theme-border)",
        // Static
        "theme-success": colors.emerald[600],
        "theme-danger": colors.rose[600],
      },
      maxWidth: {
        "layout-note": "var(--layout-width-note)",
        "layout-grid": "var(--layout-width-grid)",
      },
    },
  },
  plugins: [],
};
