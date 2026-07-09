import { createApp } from 'vue';
import { createPinia } from 'pinia';
import persistedsate from 'pinia-plugin-persistedstate';

import App from './App.vue';
import { router } from '@router/index';
import { useThemeStore } from '@stores/theme';

import '@styles/global.css';

async function bootstrap() {
  const app = createApp(App);
  const pinia = createPinia();
  pinia.use(persistedsate);

  app.use(pinia);

  const themeStore = useThemeStore(pinia);
  await themeStore.initialize();

  app.use(router);

  app.mount('#app');
}

bootstrap().catch((error) => {
  console.error('[bootstrap] application failed to start', error);
  const root = document.getElementById('app');
  if (root) {
    root.innerHTML =
      '<div style="padding:24px;font-family:system-ui;color:#a94f37;background:#f8f8f6">' +
      '<h1>\u5e94\u7528\u542f\u52a8\u5931\u8d25</h1>' +
      '<p>\u8bf7\u68c0\u67e5\u7f51\u7edc\u8fde\u63a5\u6216\u7a0d\u540e\u91cd\u8bd5\u3002</p>' +
      '</div>';
  }
});
