import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useThemeStore } from '@stores/theme';

describe('theme store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.stubGlobal('localStorage', {
      store: new Map<string, string>(),
      getItem(key: string) {
        return this.store.get(key) ?? null;
      },
      setItem(key: string, value: string) {
        this.store.set(key, value);
      },
      removeItem(key: string) {
        this.store.delete(key);
      },
      clear() {
        this.store.clear();
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('initializes with light preference by default', async () => {
    const theme = useThemeStore();
    await theme.initialize();
    expect(theme.preference).toBe('light');
    expect(theme.resolved).toBe('light');
    expect(theme.isDark).toBe(false);
  });

  it('toggles between light and dark', async () => {
    const theme = useThemeStore();
    await theme.initialize();
    theme.toggle();
    expect(theme.resolved).toBe('dark');
    theme.toggle();
    expect(theme.resolved).toBe('light');
  });

  it('persists preference to localStorage', async () => {
    const theme = useThemeStore();
    await theme.initialize();
    theme.setPreference('dark');
    expect(localStorage.getItem('agent-suite-web.theme')).toBe('dark');
  });
});
