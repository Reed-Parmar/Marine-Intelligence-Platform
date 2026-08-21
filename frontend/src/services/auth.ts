import { ApiClient } from './api';
import { UserProfile, AuthSession } from '../types/auth';
import { MOCK_USERS } from './mockData';

export const authService = {
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
    const normalizedUser: UserProfile = {
      id: String(rawUser.id || rawUser.user_id || ''),
      email: rawUser.email || email,
      fullName: rawUser.fullName || rawUser.full_name || 'Marine Researcher',
      role: (rawUser.role === 'admin' ? 'admin' : 'user'),
      department: rawUser.department || 'Marine Research Division',
      institution: rawUser.institution || rawUser.department || 'Centre for Marine Living Resources & Ecology (CMLRE)',
      avatarUrl: rawUser.avatarUrl || rawUser.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      createdAt: rawUser.createdAt || rawUser.created_at || new Date().toISOString()
    };

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

    return {
      id: String(rawUser.id || rawUser.user_id || ''),
      email: rawUser.email || '',
      fullName: rawUser.fullName || rawUser.full_name || 'Marine Researcher',
      role: (rawUser.role === 'admin' ? 'admin' : 'user'),
      department: rawUser.department || 'Marine Research Division',
      institution: rawUser.institution || rawUser.department || 'Centre for Marine Living Resources & Ecology (CMLRE)',
      avatarUrl: rawUser.avatarUrl || rawUser.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      createdAt: rawUser.createdAt || rawUser.created_at || new Date().toISOString()
    };
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
