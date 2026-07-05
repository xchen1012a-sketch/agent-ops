import { fileURLToPath, URL } from 'node:url';

import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import AutoImport from 'unplugin-auto-import/vite';
import Components from 'unplugin-vue-components/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';

import { createDevAuthPlugin } from './dev-auth-plugin';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const authPrefix = env.VITE_API_AUTH_PREFIX || '/api/auth';
  const enableDevAuth = env.VITE_ENABLE_DEV_AUTH === 'true';

  return {
    plugins: [
      ...(enableDevAuth ? [createDevAuthPlugin(authPrefix)] : []),
      vue(),
      AutoImport({
        imports: ['vue', 'vue-router', 'pinia'],
        resolvers: [ElementPlusResolver()],
        dts: 'auto-imports.d.ts',
        eslintrc: { enabled: true },
      }),
      Components({
        resolvers: [ElementPlusResolver()],
        dts: 'components.d.ts',
        dirs: ['src/components'],
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        '@app': fileURLToPath(new URL('./src/app', import.meta.url)),
        '@components': fileURLToPath(new URL('./src/components', import.meta.url)),
        '@views': fileURLToPath(new URL('./src/views', import.meta.url)),
        '@router': fileURLToPath(new URL('./src/router', import.meta.url)),
        '@stores': fileURLToPath(new URL('./src/stores', import.meta.url)),
        '@api': fileURLToPath(new URL('./src/api', import.meta.url)),
        '@lib': fileURLToPath(new URL('./src/lib', import.meta.url)),
        '@features': fileURLToPath(new URL('./src/features', import.meta.url)),
        '@types': fileURLToPath(new URL('./src/types', import.meta.url)),
        '@styles': fileURLToPath(new URL('./src/styles', import.meta.url)),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
        },
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      proxy: {
        ...(enableDevAuth
          ? {}
          : {
              [authPrefix]: {
                target: env.VITE_PROXY_AUTH_TARGET || 'http://localhost:8081',
                changeOrigin: true,
              },
            }),
        [env.VITE_API_LEGAL_PREFIX || '/api/legal/v1']: {
          target: env.VITE_PROXY_LEGAL_TARGET || 'http://localhost:8101',
          changeOrigin: true,
        },
        [env.VITE_API_RECRUITMENT_PREFIX || '/api/recruitment/v1']: {
          target: env.VITE_PROXY_RECRUITMENT_TARGET || 'http://localhost:8102',
          changeOrigin: true,
        },
        [env.VITE_API_DATA_PREFIX || '/api/data/v1']: {
          target: env.VITE_PROXY_DATA_TARGET || 'http://localhost:8103',
          changeOrigin: true,
        },
      },
    },
    build: {
      target: 'es2022',
      outDir: 'dist',
      sourcemap: false,
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            element: ['element-plus'],
            echarts: ['echarts'],
            markdown: ['marked', 'dompurify'],
          },
        },
      },
    },
  };
});
