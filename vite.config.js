import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const devApiUrl = "http://127.0.0.1:9000";

export default defineConfig({
  plugins: [
    vue()
  ],
  root: "client",
  base: "",
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            if (id.includes('vue')) {
              return 'vue-vendor';
            }
            if (id.includes('@headlessui') || id.includes('@heroicons')) {
              return 'ui-vendor';
            }
            if (id.includes('@toast-ui/editor')) {
              return 'editor-vendor';
            }
            // Remove CodeMirror from separate chunk to avoid initialization issues
            if (id.includes('primevue')) {
              return 'primevue-vendor';
            }
            if (id.includes('katex')) {
              return 'katex-vendor';
            }
            if (id.includes('lucide-vue-next')) {
              return 'icons-vendor';
            }
            if (id.includes('pinia')) {
              return 'pinia-vendor';
            }
            if (id.includes('axios')) {
              return 'http-vendor';
            }
            if (id.includes('mousetrap')) {
              return 'keyboard-vendor';
            }
            if (id.includes('marked') || id.includes('prismjs') || id.includes('highlight.js')) {
              return 'markdown-vendor';
            }
            if (id.includes('tailwindcss')) {
              return 'tailwind-vendor';
            }
            // Other vendor libraries
            return 'vendor';
          }
          
          // Feature chunks based on views
          if (id.includes('/views/Note.vue')) {
            return 'note-view';
          }
          if (id.includes('/views/Search.vue')) {
            return 'search-view';
          }
          if (id.includes('/views/Home.vue')) {
            return 'home-view';
          }
          if (id.includes('/views/LogIn.vue')) {
            return 'login-view';
          }
          if (id.includes('/views/Code.vue')) {
            return 'code-view';
          }
        },
      },
      onwarn(warning, warn) {
        // Suppress eval warnings from external libraries
        if (warning.code === 'EVAL' && 
            (warning.id?.includes('3dmol'))) {
          return;
        }
        warn(warning);
      }
    },
    chunkSizeWarningLimit: 1000, // Set limit to 1MB for realistic warnings
  },
  server: {
    // Note: The SBNOTE_PATH_PREFIX environment variable is not supported by the dev server
    port: 3000,
    watch: {
      usePolling: true,
      interval: 1000,
    },
    proxy: {
      "/api/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/files/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/a/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/xyz/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/pkl/": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/docs": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/openapi.json": {
        target: devApiUrl,
        changeOrigin: true,
      },
      "/health": {
        target: devApiUrl,
        changeOrigin: true,
      },
    },
  },
});
