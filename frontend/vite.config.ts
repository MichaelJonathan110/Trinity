import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// Dev proxy target. Overridable so the app also works when the backend runs in
// another container (docker compose) rather than on the host.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/icon-192.png', 'icons/icon-512.png', 'icons/maskable-512.png'],
      manifest: {
        name: 'TRINITY - Fuel. Recover. Perform.',
        short_name: 'TRINITY',
        description: 'Integrated athlete performance platform: nutrition, recovery, training and daily activity.',
        theme_color: '#0E1116',
        background_color: '#0E1116',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,png,svg,woff2}'],
        navigateFallback: '/index.html',
        runtimeCaching: [
          {
            // Match the API on any origin so offline caching also works in
            // production (localhost:8000 in dev, the Render URL deployed).
            urlPattern: /\/api\/v1\/(nutrition|activity|recovery|training|insights|prep|profile|account|notifications)\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'trinity-api',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 120, maxAgeSeconds: 60 * 60 * 24 }
            }
          }
        ]
      }
    })
  ],
  server: {
    port: 5173,
    proxy: { '/api': { target: proxyTarget, changeOrigin: true } }
  },
  build: { target: 'es2020', sourcemap: false }
})
