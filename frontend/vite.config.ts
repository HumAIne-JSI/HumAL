import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub Pages serves the app under the repo subpath (https://humaine-jsi.github.io/HumAL/).
// The Pages workflow sets VITE_BASE_URL; local dev keeps the default "/".
const base = process.env.VITE_BASE_URL || '/'

// https://vite.dev/config/
export default defineConfig({
  base,
  plugins: [
    vue()
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
