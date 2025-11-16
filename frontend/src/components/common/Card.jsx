import React from 'react';
import clsx from 'clsx';

/**
 * Wiederverwendbare Card-Komponente
 * 
 * FEATURES:
 * - Verschiedene Padding-Größen
 * - Optional mit Header
 * - Optional mit Footer
 * - Hover-Effekte
 * - Clickable Cards
 * 
 * @example
 * <Card title="Card Title" footer={<Button>Action</Button>}>
 *   Content
 * </Card>
 */
export default function Card({ 
  children, 
  title = null,
  subtitle = null,
  footer = null,
  headerAction = null,
  padding = 'md',
  hoverable = false,
  clickable = false,
  onClick = null,
  className = '',
  ...props 
}) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  const baseClasses = `
    bg-white rounded-lg border border-gray-200 shadow-sm
    ${hoverable ? 'hover:shadow-md transition-shadow duration-200' : ''}
    ${clickable ? 'cursor-pointer hover:border-gray-300' : ''}
  `;

  const content = (
    <>
      {/* Header */}
      {(title || headerAction) && (
        <div className={clsx(
          'flex items-start justify-between',
          padding !== 'none' && 'pb-4 border-b border-gray-100'
        )}>
          <div className="flex-1">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="mt-1 text-sm text-gray-600">
                {subtitle}
              </p>
            )}
          </div>
          {headerAction && (
            <div className="ml-4 flex-shrink-0">
              {headerAction}
            </div>
          )}
        </div>
      )}

      {/* Content */}
      <div className={clsx(
        (title || headerAction) && padding !== 'none' && 'pt-4',
        footer && padding !== 'none' && 'pb-4'
      )}>
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div className={clsx(
          'pt-4 border-t border-gray-100',
          'flex items-center justify-between gap-3'
        )}>
          {footer}
        </div>
      )}
    </>
  );

  if (clickable && onClick) {
    return (
      <button
        onClick={onClick}
        className={clsx(
          baseClasses,
          paddingClasses[padding],
          'text-left w-full',
          className
        )}
        {...props}
      >
        {content}
      </button>
    );
  }

  return (
    <div
      className={clsx(
        baseClasses,
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {content}
    </div>
  );
}
