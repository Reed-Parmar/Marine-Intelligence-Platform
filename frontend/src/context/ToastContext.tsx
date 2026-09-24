import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: ToastItem[];
  addToast: (type: ToastType, title: string, message?: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = (type: ToastType, title: string, message?: string, duration = 4000) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const newToast: ToastItem = { id, type, title, message, duration };
    setToasts((prev) => [...prev, newToast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none">
        {toasts.map((toast) => {
          const icons = {
            success: <CheckCircle2 className="w-5 h-5 text-ocean-teal flex-shrink-0" />,
            warning: <AlertTriangle className="w-5 h-5 text-ocean-amber flex-shrink-0" />,
            error: <XCircle className="w-5 h-5 text-ocean-coral flex-shrink-0" />,
            info: <Info className="w-5 h-5 text-ocean-cyan flex-shrink-0" />
          };

          const borderColors = {
            success: 'border-ocean-teal/40 bg-marine-900/95',
            warning: 'border-ocean-amber/40 bg-marine-900/95',
            error: 'border-ocean-coral/40 bg-marine-900/95',
            info: 'border-ocean-cyan/40 bg-marine-900/95'
          };

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex items-start gap-3 p-4 rounded-lg border shadow-xl backdrop-blur-md transition-all duration-300 animate-slide-up ${borderColors[toast.type]}`}
            >
              {icons[toast.type]}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-white">{toast.title}</h4>
                {toast.message && (
                  <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{toast.message}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
