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
        // Base color values
        "color-blue-50": "var(--color-blue-50)",
        "color-blue-100": "var(--color-blue-100)",
        "color-blue-200": "var(--color-blue-200)",
        "color-blue-300": "var(--color-blue-300)",
        "color-blue-350": "var(--color-blue-350)",
        "color-blue-400": "var(--color-blue-400)",
        "color-blue-500": "var(--color-blue-500)",
        "color-blue-600": "var(--color-blue-600)",
        "color-blue-700": "var(--color-blue-700)",
        "color-gray-100": "var(--color-gray-100)",
        "color-gray-200": "var(--color-gray-200)",
        "color-gray-300": "var(--color-gray-300)",
        "color-gray-400": "var(--color-gray-400)",
        "color-gray-500": "var(--color-gray-500)",
        "color-gray-600": "var(--color-gray-600)",
        "color-gray-700": "var(--color-gray-700)",
        "color-gray-800": "var(--color-gray-800)",
        "color-yellow-200": "var(--color-yellow-200)",
        "color-yellow-400": "var(--color-yellow-400)",
        "color-yellow-600": "var(--color-yellow-600)",
        "color-yellow-800": "var(--color-yellow-800)",
        "color-purple-50": "var(--color-purple-50)",
        "color-purple-200": "var(--color-purple-200)",
        "color-purple-400": "var(--color-purple-400)",
        "color-pink-50": "var(--color-pink-50)",
        "color-pink-100": "var(--color-pink-100)",
        "color-pink-300": "var(--color-pink-300)",
        "color-pink-500": "var(--color-pink-500)",
        
        // Semantic colors
        "color-primary": "var(--color-primary)",
        "color-primary-light": "var(--color-primary-light)",
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
        
        // 後方互換性のための既存クラス（一時的）
        "color-background": "var(--color-background)",
        "color-background-light": "var(--color-background-light)",
        "color-background-elevated": "var(--color-background-elevated)",
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
