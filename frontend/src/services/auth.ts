import { ApiClient } from './api';
import { UserProfile, AuthSession } from '../types/auth';
import { MOCK_USERS } from './mockData';

export const authService = {
  async login(email: string, _password: string): Promise<AuthSession> {
    // Check if it matches mock accounts or backend
    const normalizedEmail = email.toLowerCase().trim();
    let mockUser = MOCK_USERS.scientist;
    if (normalizedEmail.includes('admin')) {
      mockUser = MOCK_USERS.admin;
    }

    const fallbackSession: AuthSession = {
      accessToken: `cmlre_jwt_${mockUser.role}_${Date.now()}`,
      tokenType: 'Bearer',
      expiresIn: 86400,
      user: mockUser
    };

    const res = await ApiClient.post<any>(
      '/auth/login',
      { email, password: _password },
      fallbackSession
    );

    const data = res.data || {};
    const token = data.accessToken || data.access_token || fallbackSession.accessToken;
    if (token) {
      ApiClient.setToken(token);
    }

    const rawUser = data.user || mockUser;
    const normalizedUser: UserProfile = {
      id: String(rawUser.id || rawUser.user_id || mockUser.id),
      email: rawUser.email || mockUser.email,
      fullName: rawUser.fullName || rawUser.full_name || mockUser.fullName,
      role: (rawUser.role === 'admin' ? 'admin' : 'user'),
      department: rawUser.department || mockUser.department,
      institution: rawUser.institution || rawUser.department || 'Centre for Marine Living Resources & Ecology (CMLRE)',
      avatarUrl: rawUser.avatarUrl || rawUser.avatar_url || mockUser.avatarUrl,
      createdAt: rawUser.createdAt || rawUser.created_at || new Date().toISOString()
    };

    return {
      accessToken: token,
      tokenType: data.tokenType || data.token_type || 'Bearer',
      expiresIn: data.expiresIn || data.expires_in || 86400,
      user: normalizedUser
    };
  },

  async getCurrentUser(): Promise<UserProfile> {
    const token = ApiClient.getToken();
    const isRoleAdmin = token?.includes('admin');
    const fallbackUser = isRoleAdmin ? MOCK_USERS.admin : MOCK_USERS.scientist;

    const res = await ApiClient.get<any>('/auth/me', fallbackUser);
    const rawUser = res.data || fallbackUser;
    return {
      id: String(rawUser.id || rawUser.user_id || fallbackUser.id),
      email: rawUser.email || fallbackUser.email,
      fullName: rawUser.fullName || rawUser.full_name || fallbackUser.fullName,
      role: (rawUser.role === 'admin' ? 'admin' : 'user'),
      department: rawUser.department || fallbackUser.department,
      institution: rawUser.institution || rawUser.department || 'Centre for Marine Living Resources & Ecology (CMLRE)',
      avatarUrl: rawUser.avatarUrl || rawUser.avatar_url || fallbackUser.avatarUrl,
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
