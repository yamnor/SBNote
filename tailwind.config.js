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
        // 新しい色システム
        "color-primary": "var(--color-primary)",
        "color-primary-light": "var(--color-primary-light)",
        "color-primary-dark": "var(--color-primary-dark)",
        "color-secondary": "var(--color-secondary)",
        "color-success": "var(--color-success)",
        "color-warning": "var(--color-warning)",
        "color-error": "var(--color-error)",
        "color-info": "var(--color-info)",
        "color-accent": "var(--color-accent)",
        
        // 背景色
        "color-bg-base": "var(--color-bg-base)",
        "color-bg-neutral": "var(--color-bg-neutral)",
        "color-bg-neutral-light": "var(--color-bg-neutral-light)",
        "color-bg-neutral-lighter": "var(--color-bg-neutral-lighter)",
        "color-bg-elevated": "var(--color-bg-elevated)",
        "color-bg-subtle": "var(--color-bg-subtle)",
        "color-bg-primary": "var(--color-bg-primary)",
        "color-bg-primary-light": "var(--color-bg-primary-light)",
        "color-bg-secondary": "var(--color-bg-secondary)",
        "color-bg-error": "var(--color-bg-error)",
        "color-bg-warning": "var(--color-bg-warning)",
        "color-bg-success": "var(--color-bg-success)",
        "color-bg-popover": "var(--color-bg-popover)",
        "color-bg-backdrop": "var(--color-bg-backdrop)",
        
        // テキスト色
        "color-text-primary": "var(--color-text-primary)",
        "color-text-secondary": "var(--color-text-secondary)",
        "color-text-muted": "var(--color-text-muted)",
        "color-text-disabled": "var(--color-text-disabled)",
        "color-text-link": "var(--color-text-link)",
        "color-text-link-visited": "var(--color-text-link-visited)",
        "color-text-inverse": "var(--color-text-inverse)",
        
        // ボーダー色
        "color-border-primary": "var(--color-border-primary)",
        "color-border-light": "var(--color-border-light)",
        "color-border-lighter": "var(--color-border-lighter)",
        "color-border-focus": "var(--color-border-focus)",
        
        // ボタン色システム
        "color-button-primary-bg": "var(--color-button-primary-bg)",
        "color-button-primary-fg": "var(--color-button-primary-fg)",
        "color-button-primary-hover-bg": "var(--color-button-primary-hover-bg)",
        "color-button-secondary-bg": "var(--color-button-secondary-bg)",
        "color-button-secondary-fg": "var(--color-button-secondary-fg)",
        "color-button-secondary-border": "var(--color-button-secondary-border)",
        "color-button-secondary-hover-bg": "var(--color-button-secondary-hover-bg)",
        "color-button-secondary-grayed-bg": "var(--color-button-secondary-grayed-bg)",
        "color-button-secondary-grayed-fg": "var(--color-button-secondary-grayed-fg)",
        "color-button-secondary-grayed-border": "var(--color-button-secondary-grayed-border)",
        "color-button-secondary-grayed-hover-bg": "var(--color-button-secondary-grayed-hover-bg)",
        "color-button-tertiary-fg": "var(--color-button-tertiary-fg)",
        "color-button-tertiary-hover-bg": "var(--color-button-tertiary-hover-bg)",
        "color-button-quaternary-fg": "var(--color-button-quaternary-fg)",
        "color-button-quaternary-hover-bg": "var(--color-button-quaternary-hover-bg)",
        "color-button-quaternary-disabled-fg": "var(--color-button-quaternary-disabled-fg)",
        "color-button-danger-bg": "var(--color-button-danger-bg)",
        "color-button-danger-fg": "var(--color-button-danger-fg)",
        "color-button-danger-border": "var(--color-button-danger-border)",
        "color-button-danger-hover-bg": "var(--color-button-danger-hover-bg)",
        "color-button-danger-focus-border": "var(--color-button-danger-focus-border)",
        
        // 後方互換性のための既存クラス（一時的）
        "theme-brand": "var(--theme-brand)",
        "theme-brand-dark": "var(--theme-brand-dark)",
        "theme-brand-accent": "var(--theme-brand-accent)",
        "theme-background": "var(--theme-background)",
        "theme-background-surface": "var(--theme-background-surface)",
        "theme-background-subtle": "var(--theme-background-subtle)",
        "theme-background-elevated": "var(--theme-background-elevated)",
        "theme-button": "var(--theme-button)",
        "theme-button-hover": "var(--theme-button-hover)",
        "theme-text": "var(--theme-text)",
        "theme-text-muted": "var(--theme-text-muted)",
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
