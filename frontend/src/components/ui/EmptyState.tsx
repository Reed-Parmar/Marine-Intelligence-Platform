import React, { ReactNode } from 'react';
import { Database, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = <Database className="w-10 h-10 text-slate-500" />,
  title,
  description,
  actionLabel,
  onAction,
  className = ''
}) => {
  return (
    <div className={`glass-panel rounded-2xl p-10 text-center flex flex-col items-center justify-center border-dashed border-marine-700/60 ${className}`}>
      <div className="p-4 rounded-2xl bg-marine-900/80 border border-marine-800 mb-4 inline-flex items-center justify-center">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-white tracking-wide">{title}</h3>
      <p className="text-xs text-slate-400 max-w-md mt-1.5 leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <Button onClick={onAction} size="sm" variant="primary" className="mt-5">
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to Load Scientific Records',
  message = 'An unexpected error occurred while communicating with the CMLRE data pipeline.',
  onRetry,
  className = ''
}) => {
  return (
    <div className={`glass-panel rounded-2xl p-8 text-center flex flex-col items-center justify-center border-ocean-coral/30 bg-rose-950/20 ${className}`}>
      <div className="p-3 rounded-full bg-ocean-coral/10 border border-ocean-coral/30 mb-3 text-ocean-coral">
        <AlertCircle className="w-7 h-7" />
      </div>
      <h4 className="text-sm font-semibold text-white">{title}</h4>
      <p className="text-xs text-rose-200/80 max-w-sm mt-1 mb-4">{message}</p>
      {onRetry && (
        <Button onClick={onRetry} size="sm" variant="outline" leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          Retry Query
        </Button>
      )}
    </div>
  );
};
