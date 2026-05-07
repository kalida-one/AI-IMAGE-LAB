import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  base: './',
  resolve: {
    alias: {
      'onnxruntime-web/webgpu': path.resolve(__dirname, 'node_modules/onnxruntime-web/dist/ort.webgpu.bundle.min.mjs')
    }
  },
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    assetsDir: 'assets'
  },
  optimizeDeps: {
    exclude: ['onnxruntime-web']
  },
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp'
    }
  }
})
