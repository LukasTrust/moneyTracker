import React from 'react';
import clsx from 'clsx';

/**
 * Wiederverwendbare Button-Komponente
 * 
 * VARIANTS:
 * - primary: Hauptaktion (blau)
 * - secondary: Sekundäraktion (grau)
 * - danger: Gefährliche Aktion (rot)
 * - success: Erfolg (grün)
 * - ghost: Transparenter Button
 * - outline: Button mit Rahmen
 * 
 * SIZES:
 * - xs: Extra klein
 * - sm: Klein
 * - md: Normal (default)
 * - lg: Groß
 * - xl: Extra groß
 * 
 * @example
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   Click me
 * </Button>
 */
export default function Button({ 
  children, 
  variant = 'primary', 
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  leftIcon = null,
  rightIcon = null,
  className = '',
  onClick,
  type = 'button',
  ...props 
}) {
  const baseClasses = `
    inline-flex items-center justify-center gap-2
    font-medium rounded-lg
    transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${fullWidth ? 'w-full' : ''}
  `;
  
  const variantClasses = {
    primary: `
      bg-blue-600 text-white
      hover:bg-blue-700 active:bg-blue-800
      focus:ring-blue-500
      disabled:bg-blue-400
    `,
    secondary: `
      bg-gray-200 text-gray-900
      hover:bg-gray-300 active:bg-gray-400
      focus:ring-gray-500
      disabled:bg-gray-100
    `,
    danger: `
      bg-red-600 text-white
      hover:bg-red-700 active:bg-red-800
      focus:ring-red-500
      disabled:bg-red-400
    `,
    success: `
      bg-green-600 text-white
      hover:bg-green-700 active:bg-green-800
      focus:ring-green-500
      disabled:bg-green-400
    `,
    ghost: `
      bg-transparent text-gray-700
      hover:bg-gray-100 active:bg-gray-200
      focus:ring-gray-400
    `,
    outline: `
      bg-transparent border-2 border-gray-300 text-gray-700
      hover:border-gray-400 hover:bg-gray-50
      active:bg-gray-100
      focus:ring-gray-400
    `,
  };

  const sizeClasses = {
    xs: 'px-2.5 py-1 text-xs',
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
    xl: 'px-6 py-3 text-lg',
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <svg 
          className="animate-spin h-4 w-4" 
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
      ) : leftIcon}
      
      {children}
      
      {rightIcon && !loading && rightIcon}
    </button>
  );
}
