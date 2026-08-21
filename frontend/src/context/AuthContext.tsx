import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserProfile, AuthSession } from '../types/auth';
import { authService } from '../services/auth';
import { ApiClient } from '../services/api';
import { MOCK_USERS } from '../services/mockData';

interface AuthContextType {
  user: UserProfile | null;
  session: AuthSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchDemoRole: (role: 'user' | 'admin') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Start unauthenticated. isLoading=true so ProtectedRoute shows spinner
  // while we check if a stored token exists and is still valid.
  const [user, setUser] = useState<UserProfile | null>(null);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // On mount: try to restore session from stored token.
    // If stored token is present and valid, /auth/me returns the profile.
    // If missing/expired/invalid → user stays null → redirect to /login.
    const checkAuth = async () => {
      const storedToken = ApiClient.getToken();
      if (!storedToken) {
        // No token stored at all — skip network call, go straight to login.
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
        setSession({
          accessToken: storedToken,
          tokenType: 'Bearer',
          expiresIn: 86400,
          user: currentUser
        });
      } catch {
        // Token invalid or expired — clear it and force re-login.
        ApiClient.setToken(null);
        setUser(null);
        setSession(null);
      } finally {
        setIsLoading(false);
      }
    };
    checkAuth();
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

  // switchDemoRole: hackathon convenience to flip display profile label only.
  // Does NOT change the underlying API token — all API calls still use the
  // real stored Bearer token from the actual login.
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
