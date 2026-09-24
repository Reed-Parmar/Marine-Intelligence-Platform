import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserProfile, AuthSession, RegisterData } from '../types/auth';
import { authService } from '../services/auth';
import { supabase } from '../services/supabase';
import { ApiClient } from '../services/api';
import { MOCK_USERS } from '../services/mockData';

interface AuthContextType {
  user: UserProfile | null;
  session: AuthSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  switchDemoRole: (role: 'user' | 'admin') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 1. Initial session load
    const checkAuth = async () => {
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        if (currentSession?.access_token) {
          ApiClient.setToken(currentSession.access_token);
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
          setSession({
            accessToken: currentSession.access_token,
            tokenType: currentSession.token_type || 'Bearer',
            expiresIn: currentSession.expires_in || 86400,
            user: currentUser
          });
        } else {
          ApiClient.setToken(null);
          setUser(null);
          setSession(null);
        }
      } catch {
        ApiClient.setToken(null);
        setUser(null);
        setSession(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();

    // 2. Realtime auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, newSession) => {
      if (newSession?.access_token) {
        ApiClient.setToken(newSession.access_token);
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
          setSession({
            accessToken: newSession.access_token,
            tokenType: newSession.token_type || 'Bearer',
            expiresIn: newSession.expires_in || 86400,
            user: currentUser
          });
        } catch {
          // fallback
        }
      } else {
        ApiClient.setToken(null);
        setUser(null);
        setSession(null);
      }
      setIsLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const authSession = await authService.login(email, password);
      setSession(authSession);
      setUser(authSession.user);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);
    try {
      const authSession = await authService.register(data);
      setSession(authSession);
      setUser(authSession.user);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setSession(null);
      setIsLoading(false);
    }
  };

  const switchDemoRole = (role: 'user' | 'admin') => {
    const selectedUser = role === 'admin' ? MOCK_USERS.admin : MOCK_USERS.scientist;
    setUser(selectedUser);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        switchDemoRole
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
