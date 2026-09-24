import React, { ReactNode } from 'react';

export interface CardProps {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  interactive = false,
  onClick
}) => {
  const panelClass = interactive ? 'glass-panel-interactive cursor-pointer' : 'glass-panel';
  return (
    <div
      onClick={onClick}
      className={`rounded-xl p-5 shadow-glow-card transition-all duration-200 ${panelClass} ${className}`}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  className?: string;
}> = ({ title, subtitle, action, className = '' }) => {
  return (
    <div className={`flex items-start justify-between gap-4 pb-4 border-b border-marine-800/80 mb-4 ${className}`}>
      <div>
        <h3 className="text-base font-semibold text-white tracking-wide flex items-center gap-2">{title}</h3>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
};
