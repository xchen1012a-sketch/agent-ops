declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_API_AUTH_PREFIX: string;
  readonly VITE_API_LEGAL_PREFIX: string;
  readonly VITE_API_RECRUITMENT_PREFIX: string;
  readonly VITE_API_DATA_PREFIX: string;
  readonly VITE_SESS_TIMEOUT_MINUTES: string;
  readonly VITE_DEFAULT_THEME: 'light' | 'dark' | 'system';
  readonly VITE_PROXY_AUTH_TARGET?: string;
  readonly VITE_PROXY_LEGAL_TARGET?: string;
  readonly VITE_PROXY_RECRUITMENT_TARGET?: string;
  readonly VITE_PROXY_DATA_TARGET?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
