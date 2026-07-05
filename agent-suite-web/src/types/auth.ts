export type UserRole = 'admin' | 'user';

export interface UserProfile {
  user_id: string;
  public_id: string;
  email: string;
  display_name: string;
  role: UserRole;
  status: 'active' | 'disabled';
  created_at: string;
  updated_at: string;
}

export interface AuthSession {
  access_token: string;
  expires_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  captcha?: string;
}

export interface PasswordChangeInput {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface AuthErrorResponse {
  error_code: string;
  message: string;
  retry_after_seconds?: number;
}
