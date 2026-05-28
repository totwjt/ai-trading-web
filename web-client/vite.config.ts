import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    open: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules')) {
            if (id.includes('ant-design-vue') || id.includes('@ant-design/icons')) return 'antd'
            if (id.includes('chart.js') || id.includes('lightweight-charts')) return 'charts'
            if (id.includes('dayjs') || id.includes('lodash') || id.includes('clsx')) return 'utils'
            return 'vendor'
          }
        },
      }
    },
    chunkSizeWarningLimit: 500,
  }
})
