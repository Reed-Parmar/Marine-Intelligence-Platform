import { ApiClient } from './api';
import { supabase } from './supabase';
import { UserProfile, AuthSession, RegisterData } from '../types/auth';

function normalizeProfile(rawUser: any, metadata: any = {}, fallbackEmail: string = ''): UserProfile {
  const meta = metadata || rawUser?.user_metadata || {};
  return {
    id: String(rawUser?.id || rawUser?.user_id || ''),
    email: rawUser?.email || fallbackEmail,
    fullName: rawUser?.fullName || rawUser?.full_name || meta.full_name || meta.name || 'Marine Researcher',
    role: (rawUser?.role === 'admin' || meta.role === 'admin' ? 'admin' : 'user'),
    institution: rawUser?.institution || meta.institution || 'Centre for Marine Living Resources & Ecology (CMLRE)',
    department: rawUser?.department || meta.department || undefined,
    designation: rawUser?.designation || meta.designation || undefined,
    avatarUrl: rawUser?.avatarUrl || rawUser?.avatar_url || meta.avatar_url || undefined,
    createdAt: rawUser?.createdAt || rawUser?.created_at || new Date().toISOString()
  };
}

export const authService = {
  async register(data: RegisterData): Promise<AuthSession> {
    const { data: authData, error } = await supabase.auth.signUp({
      email: data.email,
      password: data.password,
      options: {
        data: {
          full_name: data.fullName,
          institution: data.institution || 'Centre for Marine Living Resources & Ecology (CMLRE)',
          department: data.department,
          designation: data.designation,
          role: 'user'
        }
      }
    });

    if (error) {
      throw new Error(error.message || 'Registration failed via Supabase Auth.');
    }

    if (!authData.user) {
      throw new Error('Registration failed: No user returned by authentication service.');
    }

    const session = authData.session;
    const token = session?.access_token || '';
    if (token) {
      ApiClient.setToken(token);
    }

    const normalizedUser = normalizeProfile(authData.user, authData.user.user_metadata, data.email);

    return {
      accessToken: token,
      tokenType: session?.token_type || 'Bearer',
      expiresIn: session?.expires_in || 86400,
      user: normalizedUser
    };
  },

  async login(email: string, password: string): Promise<AuthSession> {
    const { data: authData, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });

    if (error) {
      throw new Error(error.message || 'Invalid email or password.');
    }

    if (!authData.session || !authData.user) {
      throw new Error('Authentication failed: No active session returned by Supabase Auth.');
    }

    const token = authData.session.access_token;
    ApiClient.setToken(token);

    // Attempt to load rich profile from FastAPI backend if available, otherwise normalize Supabase profile
    let profile = normalizeProfile(authData.user, authData.user.user_metadata, email);
    try {
      const backendRes = await ApiClient.get<any>('/auth/me');
      if (backendRes.data) {
        profile = normalizeProfile(backendRes.data, {}, email);
      }
    } catch {
      // Backend /auth/me is supplementary; keep Supabase profile if unavailable
    }

    return {
      accessToken: token,
      tokenType: authData.session.token_type || 'Bearer',
      expiresIn: authData.session.expires_in || 86400,
      user: profile
    };
  },

  async getCurrentUser(): Promise<UserProfile> {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error || !session || !session.user) {
      throw new Error('Session expired or user unauthorized.');
    }

    ApiClient.setToken(session.access_token);

    try {
      const backendRes = await ApiClient.get<any>('/auth/me');
      if (backendRes.data) {
        return normalizeProfile(backendRes.data, {}, session.user.email);
      }
    } catch {
      // fallback to session user
    }

    return normalizeProfile(session.user, session.user.user_metadata, session.user.email);
  },

  async logout(): Promise<void> {
    try {
      await supabase.auth.signOut();
    } catch {
      // ignore
    } finally {
      ApiClient.setToken(null);
    }
  }
};
