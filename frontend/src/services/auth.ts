import { ApiClient } from './api';
import { UserProfile, AuthSession, RegisterData } from '../types/auth';

function normalizeProfile(rawUser: any, fallbackEmail: string = ''): UserProfile {
  return {
    id: String(rawUser.id || rawUser.user_id || ''),
    email: rawUser.email || fallbackEmail,
    fullName: rawUser.fullName || rawUser.full_name || 'Marine Researcher',
    role: (rawUser.role === 'admin' ? 'admin' : 'user'),
    institution: rawUser.institution || undefined,
    department: rawUser.department || undefined,
    designation: rawUser.designation || undefined,
    avatarUrl: rawUser.avatarUrl || rawUser.avatar_url || undefined,
    createdAt: rawUser.createdAt || rawUser.created_at || new Date().toISOString()
  };
}

export const authService = {
  async register(data: RegisterData): Promise<AuthSession> {
    const res = await ApiClient.post<any>(
      '/auth/register',
      {
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        institution: data.institution || undefined,
        department: data.department,
        designation: data.designation
      }
    );

    const resData = res.data;
    if (!resData) {
      throw new Error('Registration failed: No session returned from server.');
    }

    const token = resData.accessToken || resData.access_token;
    if (token) {
      ApiClient.setToken(token);
    }

    const rawUser = resData.user || {};
    const normalizedUser = normalizeProfile(rawUser, data.email);

    return {
      accessToken: token || '',
      tokenType: resData.tokenType || resData.token_type || 'Bearer',
      expiresIn: resData.expiresIn || resData.expires_in || 86400,
      user: normalizedUser
    };
  },

  async login(email: string, _password: string): Promise<AuthSession> {
    const res = await ApiClient.post<any>(
      '/auth/login',
      { email, password: _password }
    );

    const data = res.data;
    if (!data) {
      throw new Error('Authentication failed: No session returned from server.');
    }

    const token = data.accessToken || data.access_token;
    if (token) {
      ApiClient.setToken(token);
    }

    const rawUser = data.user || {};
    const normalizedUser = normalizeProfile(rawUser, email);

    return {
      accessToken: token || '',
      tokenType: data.tokenType || data.token_type || 'Bearer',
      expiresIn: data.expiresIn || data.expires_in || 86400,
      user: normalizedUser
    };
  },

  async getCurrentUser(): Promise<UserProfile> {
    const res = await ApiClient.get<any>('/auth/me');
    const rawUser = res.data;
    if (!rawUser) {
      throw new Error('Session expired or user unauthorized.');
    }

    return normalizeProfile(rawUser);
  },

  async logout(): Promise<void> {
    try {
      await ApiClient.post('/auth/logout', {}, {});
    } catch {
      // ignore
    } finally {
      ApiClient.setToken(null);
    }
  }
};
