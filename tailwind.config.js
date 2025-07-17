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
        // Semantic colors
        "color-primary": "var(--color-primary)",
        "color-primary-light": "var(--color-primary-light)",
        "color-primary-subtle": "var(--color-primary-subtle)",
        "color-primary-dark": "var(--color-primary-dark)",
        "color-secondary": "var(--color-secondary)",
        "color-complementary": "var(--color-complementary)",
        "color-accent": "var(--color-accent)",
        "color-analogous": "var(--color-analogous)",
        
        // Background colors
        "color-surface": "var(--color-surface)",
        "color-background": "var(--color-background)",
        "color-background-light": "var(--color-background-light)",
        "color-background-lighter": "var(--color-background-lighter)",
        
        // Text colors
        "color-text-base": "var(--color-text-base)",
        "color-text-light": "var(--color-text-light)",
        "color-text-lighter": "var(--color-text-lighter)",
        "color-text-link": "var(--color-text-link)",
        "color-text-link-visited": "var(--color-text-link-visited)",
        "color-text-inverse": "var(--color-text-inverse)",
        
        // Button color system
        "color-on-primary": "var(--color-on-primary)",
        "color-on-secondary": "var(--color-on-secondary)",
        "color-on-complementary": "var(--color-on-complementary)",
        "color-on-accent": "var(--color-on-accent)",
        
        // Border colors
        "color-border-base": "var(--color-border-base)",
        "color-border-light": "var(--color-border-light)",
        "color-border-lighter": "var(--color-border-lighter)",
        "color-border-focus": "var(--color-border-focus)",
        
        // Shadow colors
        "color-shadow-sm": "var(--color-shadow-sm)",
        "color-shadow-md": "var(--color-shadow-md)",
        "color-shadow-lg": "var(--color-shadow-lg)",
        
        // Label color system
        "color-label-private": "var(--color-label-private)",
        "color-label-limited": "var(--color-label-limited)",
        "color-label-public": "var(--color-label-public)",        
      },
      maxWidth: {
        "layout-note": "var(--layout-width-note)",
        "layout-grid": "var(--layout-width-grid)",
      },
      zIndex: {
        // 基本階層
        "base": "1",        // 基本コンテンツ
        "card": "5",        // カード/アイテム
        "dropdown": "25",   // ドロップダウン/ポップオーバー
        "toolbar": "30",    // ツールバー/パネル
        "navigation": "40", // ナビゲーション
        "modal": "50",      // モーダル/オーバーレイ
        "toast": "55",      // トースト通知
        "overlay": "60",    // 最前面要素
        
        // 数値クラス（後方互換性）
        "25": "25",
        "55": "55",
        "60": "60",
      },
    },
  },
  plugins: [],
};
