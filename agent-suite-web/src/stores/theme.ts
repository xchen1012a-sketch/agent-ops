import { defineStore } from 'pinia';

export type ThemeMode = 'light' | 'dark';
export type ThemePreference = ThemeMode | 'system';

interface ThemeState {
  preference: ThemePreference;
  resolved: ThemeMode;
}

const STORAGE_KEY = 'agent-suite-web.theme';
const MEDIA_QUERY = '(prefers-color-scheme: dark)';

function readSystemTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia(MEDIA_QUERY).matches ? 'dark' : 'light';
}

function resolveTheme(preference: ThemePreference): ThemeMode {
  return preference === 'system' ? readSystemTheme() : preference;
}

function applyTheme(mode: ThemeMode): void {
  if (typeof document === 'undefined') return;
  document.documentElement.setAttribute('data-theme', mode);
  document.documentElement.style.colorScheme = mode;
}

export const useThemeStore = defineStore('theme', {
  state: (): ThemeState => ({
    preference: 'light',
    resolved: 'light',
  }),
  getters: {
    isDark: (state) => state.resolved === 'dark',
  },
  actions: {
    async initialize(): Promise<void> {
      const stored = this.readStoredPreference();
      this.preference = stored;
      this.resolved = resolveTheme(stored);
      applyTheme(this.resolved);

      if (typeof window !== 'undefined') {
        window.matchMedia(MEDIA_QUERY).addEventListener('change', this.handleSystemChange);
      }
    },
    setPreference(preference: ThemePreference): void {
      this.preference = preference;
      this.resolved = resolveTheme(preference);
      applyTheme(this.resolved);
      this.writeStoredPreference(preference);
    },
    toggle(): void {
      const next: ThemeMode = this.resolved === 'dark' ? 'light' : 'dark';
      this.setPreference(next);
    },
    dispose(): void {
      if (typeof window !== 'undefined') {
        window.matchMedia(MEDIA_QUERY).removeEventListener('change', this.handleSystemChange);
      }
    },
    handleSystemChange(): void {
      if (this.preference !== 'system') return;
      this.resolved = readSystemTheme();
      applyTheme(this.resolved);
    },
    readStoredPreference(): ThemePreference {
      if (typeof localStorage === 'undefined') {
        return (import.meta.env.VITE_DEFAULT_THEME as ThemePreference) ?? 'light';
      }
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw === 'light' || raw === 'dark' || raw === 'system') return raw;
      return (import.meta.env.VITE_DEFAULT_THEME as ThemePreference) ?? 'light';
    },
    writeStoredPreference(preference: ThemePreference): void {
      if (typeof localStorage === 'undefined') return;
      localStorage.setItem(STORAGE_KEY, preference);
    },
  },
  persist: {
    key: STORAGE_KEY,
    pick: ['preference'],
  },
});
