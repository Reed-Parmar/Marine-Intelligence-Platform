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

    const res = await ApiClient.post<AuthSession>(
      '/auth/login',
      { email, password: _password },
      fallbackSession
    );

    if (res.data?.accessToken) {
      ApiClient.setToken(res.data.accessToken);
    }
    return res.data;
  },

  async getCurrentUser(): Promise<UserProfile> {
    const token = ApiClient.getToken();
    const isRoleAdmin = token?.includes('admin');
    const fallbackUser = isRoleAdmin ? MOCK_USERS.admin : MOCK_USERS.scientist;

    const res = await ApiClient.get<UserProfile>('/auth/me', fallbackUser);
    return res.data;
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
