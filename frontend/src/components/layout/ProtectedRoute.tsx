import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2 } from 'lucide-react';

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-marine-950 flex flex-col items-center justify-center text-slate-300">
        <Loader2 className="w-8 h-8 animate-spin text-ocean-cyan mb-3" />
        <p className="text-xs font-mono tracking-wider text-slate-400">AUTHENTICATING CMLRE SESSION...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
