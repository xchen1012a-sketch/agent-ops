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
      '<div style="padding:24px;font-family:system-ui;color:#b00020">' +
      '<h1>平台启动失败</h1>' +
      '<p>请检查网络或联系系统管理员。</p>' +
      '</div>';
  }
});
