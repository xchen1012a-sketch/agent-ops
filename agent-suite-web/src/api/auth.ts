import { authApi } from '@lib/config';
import type { AuthSession, LoginCredentials, PasswordChangeInput, UserProfile } from '@/types/auth';

export const authClient = {
  async login(credentials: LoginCredentials): Promise<AuthSession> {
    const { data } = await authApi.post<AuthSession>('/login', credentials);
    return data;
  },

  async refresh(): Promise<AuthSession> {
    const { data } = await authApi.post<AuthSession>('/refresh');
    return data;
  },

  async logout(): Promise<void> {
    await authApi.post('/logout');
  },

  async changePassword(payload: PasswordChangeInput): Promise<void> {
    await authApi.post('/change-password', payload);
  },

  async fetchProfile(): Promise<UserProfile> {
    const { data } = await authApi.get<UserProfile>('/me');
    return data;
  },
};
