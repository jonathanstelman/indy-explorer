import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    include: [
      '@deck.gl/core',
      '@deck.gl/layers',
      '@deck.gl/react',
      '@deck.gl/widgets',
      '@deck.gl/extensions',
      '@deck.gl/mesh-layers',
    ],
  },
  test: {
    environment: 'node',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
