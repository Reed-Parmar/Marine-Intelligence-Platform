import React from 'react';

export const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div
      className={`animate-pulse rounded-lg bg-marine-800/60 border border-marine-700/30 ${className}`}
    />
  );
};

export const CardSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => {
  return (
    <div className="glass-panel rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-4 w-16" />
      </div>
      <div className="space-y-2 pt-2">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className={`h-4 ${i === 0 ? 'w-full' : i === 1 ? 'w-5/6' : 'w-4/6'}`} />
        ))}
      </div>
    </div>
  );
};
