import { config } from '@vue/test-utils';
import { vi } from 'vitest';

config.global.mocks = {
  $t: (key: string) => key,
};

if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

if (typeof global !== 'undefined' && !global.ResizeObserver) {
  global.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  };
}

vi.stubEnv('VITE_API_BASE_URL', 'http://localhost');
vi.stubEnv('VITE_API_AUTH_PREFIX', '/api/auth');
vi.stubEnv('VITE_API_LEGAL_PREFIX', '/api/legal/v1');
vi.stubEnv('VITE_API_RECRUITMENT_PREFIX', '/api/recruitment/v1');
vi.stubEnv('VITE_API_DATA_PREFIX', '/api/data/v1');
vi.stubEnv('VITE_SESS_TIMEOUT_MINUTES', '30');
vi.stubEnv('VITE_DEFAULT_THEME', 'light');
