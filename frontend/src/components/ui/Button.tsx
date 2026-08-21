import React, { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'glow';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  children: ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-marine-950 disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const sizeStyles = {
    sm: 'px-2.5 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-5 py-2.5 text-base gap-2.5'
  };

  const variantStyles = {
    primary: 'bg-gradient-to-r from-ocean-cyan to-blue-600 text-marine-950 font-semibold hover:from-cyan-300 hover:to-blue-500 shadow-md shadow-cyan-500/20 focus:ring-ocean-cyan',
    secondary: 'bg-marine-800 text-slate-100 hover:bg-marine-750 border border-marine-700 focus:ring-marine-600',
    outline: 'border border-marine-600 text-slate-200 hover:bg-marine-850 hover:border-ocean-cyan/50 focus:ring-ocean-cyan',
    danger: 'bg-ocean-coral/90 text-white hover:bg-rose-600 shadow-md shadow-rose-900/20 focus:ring-ocean-coral',
    ghost: 'text-slate-300 hover:text-white hover:bg-marine-800/60 focus:ring-marine-600',
    glow: 'bg-marine-900 text-ocean-cyan border border-ocean-cyan/60 hover:bg-ocean-cyan hover:text-marine-950 shadow-glow-cyan focus:ring-ocean-cyan'
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        leftIcon
      )}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};
