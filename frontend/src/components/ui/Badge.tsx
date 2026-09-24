import React, { ReactNode } from 'react';

export type BadgeVariant = 'cyan' | 'teal' | 'amber' | 'coral' | 'blue' | 'purple' | 'slate';

export interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'slate',
  size = 'md',
  className = '',
  dot = false
}) => {
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px] font-medium tracking-wider uppercase',
    md: 'px-2.5 py-1 text-xs font-medium'
  };

  const variantStyles = {
    cyan: 'bg-ocean-cyan/15 text-ocean-cyan border border-ocean-cyan/30',
    teal: 'bg-ocean-teal/15 text-ocean-teal border border-ocean-teal/30',
    amber: 'bg-ocean-amber/15 text-ocean-amber border border-ocean-amber/30',
    coral: 'bg-ocean-coral/15 text-ocean-coral border border-ocean-coral/30',
    blue: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
    purple: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
    slate: 'bg-slate-800/80 text-slate-300 border border-slate-700'
  };

  const dotColors = {
    cyan: 'bg-ocean-cyan',
    teal: 'bg-ocean-teal',
    amber: 'bg-ocean-amber',
    coral: 'bg-ocean-coral',
    blue: 'bg-blue-400',
    purple: 'bg-purple-400',
    slate: 'bg-slate-400'
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};
