import { defineStore } from 'pinia';

import { authClient } from '@api/auth';
import type { AuthSession, LoginCredentials, PasswordChangeInput, UserProfile } from '@/types/auth';

const ACCESS_TOKEN_KEY = 'agent-suite-web.access_token';
const PROFILE_KEY = 'agent-suite-web.profile';

interface AuthState {
  accessToken: string | null;
  refreshInProgress: Promise<void> | null;
  profile: UserProfile | null;
  session: AuthSession | null;
}

function readStoredToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function readStoredProfile(): UserProfile | null {
  if (typeof localStorage === 'undefined') return null;
  const raw = localStorage.getItem(PROFILE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: readStoredToken(),
    refreshInProgress: null,
    profile: readStoredProfile(),
    session: null,
  }),
  getters: {
    isAuthenticated(state): boolean {
      return Boolean(state.accessToken);
    },
    role(state): 'admin' | 'user' {
      return state.profile?.role ?? 'user';
    },
    isAdmin(state): boolean {
      return state.profile?.role === 'admin';
    },
    displayName(state): string {
      return state.profile?.display_name ?? state.profile?.email ?? '当前用户';
    },
    initials(state): string {
      const name = state.profile?.display_name ?? state.profile?.email ?? '';
      const trimmed = name.trim();
      if (!trimmed) return 'U';
      const chars = Array.from(trimmed);
      return chars.slice(0, 1).join('').toUpperCase();
    },
  },
  actions: {
    async login(credentials: LoginCredentials): Promise<UserProfile> {
      const session = await authClient.login(credentials);
      this.applySession(session);
      const profile = await authClient.fetchProfile();
      this.profile = profile;
      this.persistProfile();
      return profile;
    },
    async refresh(): Promise<void> {
      if (this.refreshInProgress) {
        return this.refreshInProgress!;
      }
      this.refreshInProgress = (async () => {
        try {
          const session = await authClient.refresh();
          this.applySession(session);
        } finally {
          this.refreshInProgress = null;
        }
      })();
      return this.refreshInProgress;
    },
    async logout(): Promise<void> {
      try {
        await authClient.logout();
      } finally {
        this.clearSession();
      }
    },
    async changePassword(payload: PasswordChangeInput): Promise<void> {
      await authClient.changePassword(payload);
      this.clearSession();
    },
    applySession(session: AuthSession): void {
      this.accessToken = session.access_token;
      this.session = {
        access_token: session.access_token,
        expires_at: session.expires_at,
      };
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(ACCESS_TOKEN_KEY, session.access_token);
      }
    },
    persistProfile(): void {
      if (typeof localStorage === 'undefined') return;
      if (this.profile) {
        localStorage.setItem(PROFILE_KEY, JSON.stringify(this.profile));
      } else {
        localStorage.removeItem(PROFILE_KEY);
      }
    },
    clearSession(): void {
      this.accessToken = null;
      this.profile = null;
      this.session = null;
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(PROFILE_KEY);
      }
    },
  },
});
