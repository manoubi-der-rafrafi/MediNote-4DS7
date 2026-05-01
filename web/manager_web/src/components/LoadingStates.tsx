import React from 'react';

/**
 * Skeleton Loader Component
 * Used while data is loading
 */
export const SkeletonLoader: React.FC<{ count?: number; height?: string }> = ({
  count = 3,
  height = '20px',
}) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
        style={{ height }}
      />
    ))}
  </div>
);

/**
 * Loading Spinner Component
 */
export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizeClass = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }[size];

  return (
    <div className={`${sizeClass} border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin`} />
  );
};

/**
 * Error Message Component
 */
export const ErrorMessage: React.FC<{
  error?: Error | null;
  message?: string;
  onRetry?: () => void;
}> = ({ error, message, onRetry }) => (
  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
    <h3 className="text-red-800 dark:text-red-200 font-semibold">Error Loading Data</h3>
    <p className="text-red-700 dark:text-red-300 text-sm mt-1">
      {message || error?.message || 'An unexpected error occurred'}
    </p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="mt-3 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition"
      >
        Try Again
      </button>
    )}
  </div>
);

/**
 * Query Result Wrapper Component
 * Handles loading, error, and empty states
 */
export interface QueryWrapperProps<T = any> {
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  data: T;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  isEmpty?: boolean;
  onRetry?: () => void;
}

export const QueryWrapper: React.FC<QueryWrapperProps> = ({
  isLoading,
  isError,
  error,
  data,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  isEmpty = !data || (Array.isArray(data) && data.length === 0),
  onRetry,
}) => {
  if (isLoading) {
    return (
      <>
        {loadingComponent || (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        )}
      </>
    );
  }

  if (isError) {
    return (
      <>
        {errorComponent || (
          <div className="py-12">
            <ErrorMessage error={error as Error} onRetry={onRetry} />
          </div>
        )}
      </>
    );
  }

  if (isEmpty) {
    return (
      <>
        {emptyComponent || (
          <div className="text-center py-12 text-gray-500">
            <p>No data available</p>
          </div>
        )}
      </>
    );
  }

  return <>{children}</>;
};

/**
 * Skleton Card for Dashboard
 */
export const SkeletonCard: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div className="grid gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4 animate-pulse" />
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-2 animate-pulse" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 animate-pulse" />
      </div>
    ))}
  </div>
);

/**
 * Skeleton Table
 */
export const SkeletonTable: React.FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 5 }) => (
  <div className="overflow-x-auto">
    <table className="w-full">
      <tbody>
        {Array.from({ length: rows }).map((_, i) => (
          <tr key={i} className="border-b border-gray-200 dark:border-gray-700">
            {Array.from({ length: cols }).map((_, j) => (
              <td key={j} className="px-4 py-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
