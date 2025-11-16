import React from 'react';
import clsx from 'clsx';

export default function LoadingSpinner({ 
  size = 'md', 
  text = null,
  fullScreen = false,
  className = '' 
}) {
  const sizeClasses = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  const spinner = (
    <svg
      className={clsx('animate-spin text-blue-600', sizeClasses[size], className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-4">
          {spinner}
          {text && <p className="text-sm font-medium text-gray-700">{text}</p>}
        </div>
      </div>
    );
  }

  if (text) {
    return (
      <div className="flex items-center justify-center gap-3">
        {spinner}
        <p className="text-sm font-medium text-gray-700">{text}</p>
      </div>
    );
  }

  return spinner;
}

export function Skeleton({ className = '', ...props }) {
  return <div className={clsx('animate-pulse bg-gray-200 rounded', className)} {...props} />;
}

export function SkeletonLines({ count = 3, className = '' }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className={clsx('h-4 w-full', className)} />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <Skeleton className="h-6 w-1/3 mb-4" />
      <SkeletonLines count={3} />
    </div>
  );
}
