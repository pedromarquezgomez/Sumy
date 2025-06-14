// ui/vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 3000,
    cors: true,
    proxy: {
      '/api': {
        target: 'https://sumiller-service-597742621765.europe-west1.run.app',
        changeOrigin: true,
        secure: true,
        timeout: 60000, // 60 segundos timeout
        proxyTimeout: 60000, // 60 segundos proxy timeout
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Proxy request to:', options.target + req.url);
          });
          proxy.on('error', (err, req, res) => {
            console.error('Proxy error:', err);
          });
        }
      }
    }
  }
})