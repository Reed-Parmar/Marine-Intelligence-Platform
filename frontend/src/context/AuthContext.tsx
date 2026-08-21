import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserProfile, AuthSession } from '../types/auth';
import { authService } from '../services/auth';
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
  const [user, setUser] = useState<UserProfile | null>(MOCK_USERS.scientist);
  const [session, setSession] = useState<AuthSession | null>({
    accessToken: 'demo-token-scientist',
    tokenType: 'Bearer',
    expiresIn: 86400,
    user: MOCK_USERS.scientist
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check existing stored auth or initialize default scientist demo
    const checkAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (err: any) {
        // Fallback default
        setUser(MOCK_USERS.scientist);
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
      setError(err.message || 'Authentication failed. Please check your scientific credentials.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setSession(null);
    } finally {
      setIsLoading(false);
    }
  };

  const switchDemoRole = (role: 'user' | 'admin') => {
    const selectedUser = role === 'admin' ? MOCK_USERS.admin : MOCK_USERS.scientist;
    setUser(selectedUser);
    setSession({
      accessToken: `demo-token-${role}`,
      tokenType: 'Bearer',
      expiresIn: 86400,
      user: selectedUser
    });
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
