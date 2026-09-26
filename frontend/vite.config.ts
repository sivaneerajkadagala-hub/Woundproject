import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

const backendUrl = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

const apiProxy = {
  '/api': {
    target: backendUrl,
    changeOrigin: true,
  },
  '/storage': {
    target: backendUrl,
    changeOrigin: true,
  }
};

export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_PAGES ? '/Woundproject/' : '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: apiProxy,
  },
  preview: {
    port: 3000,
    host: true,
    proxy: apiProxy,
  }
});
