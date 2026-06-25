import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/boardgames': 'http://127.0.0.1:8000',
      '/accounts': 'http://127.0.0.1:8000',
      '/community': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000'
    }
  }
})
