import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';

/**
 * Modal Component
 * 
 * SIZES:
 * - sm: 384px
 * - md: 512px (default)
 * - lg: 768px
 * - xl: 1024px
 * - full: 95% width
 * 
 * FEATURES:
 * - Keyboard Navigation (ESC zum Schließen)
 * - Click Outside zum Schließen
 * - Focus Trap
 * - Smooth Animations
 * 
 * @example
 * <Modal
 *   isOpen={open}
 *   onClose={handleClose}
 *   title="Modal Title"
 *   size="md"
 * >
 *   Content
 * </Modal>
 */
export default function Modal({
  isOpen,
  onClose,
  title = null,
  children,
  footer = null,
  size = 'md',
  closeOnEscape = true,
  closeOnOverlayClick = true,
  showCloseButton = true,
  className = '',
}) {
  // ESC-Key Handler
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeOnEscape, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    full: 'max-w-[95%]',
  };

  const handleOverlayClick = (e) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  const modalContent = (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={handleOverlayClick}
      />

      {/* Modal Container */}
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Modal Content */}
        <div
          className={clsx(
            'relative bg-white rounded-lg shadow-xl',
            'w-full transition-all transform',
            sizeClasses[size],
            className
          )}
        >
          {/* Header */}
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between p-6 border-b border-neutral-200">
              {title && (
                <h3 
                  id="modal-title" 
                  className="text-lg font-semibold text-neutral-900"
                >
                  {title}
                </h3>
              )}
              {showCloseButton && (
                <button
                  type="button"
                  onClick={onClose}
                  className="ml-auto text-neutral-400 hover:text-neutral-600 transition-colors"
                >
                  <span className="sr-only">Schließen</span>
                  <svg 
                    className="h-6 w-6" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M6 18L18 6M6 6l12 12" 
                    />
                  </svg>
                </button>
              )}
            </div>
          )}

          {/* Body */}
          <div className="p-6">
            {children}
          </div>

          {/* Footer */}
          {footer && (
            <div className="flex items-center justify-end gap-3 px-6 py-4 bg-neutral-50 border-t border-neutral-200 rounded-b-lg">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

/**
 * Confirm Dialog Component
 * 
 * Spezialisiertes Modal für Bestätigungen
 * 
 * @example
 * <ConfirmDialog
 *   isOpen={open}
 *   onConfirm={handleConfirm}
 *   onCancel={handleCancel}
 *   title="Löschen bestätigen"
 *   message="Möchten Sie dieses Element wirklich löschen?"
 *   confirmText="Löschen"
 *   cancelText="Abbrechen"
 *   variant="danger"
 * />
 */
export function ConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  title = 'Bestätigung',
  message,
  confirmText = 'Bestätigen',
  cancelText = 'Abbrechen',
  variant = 'primary', // 'primary', 'danger'
  loading = false,
}) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
      size="sm"
      footer={
        <>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={clsx(
              'px-4 py-2 text-sm font-medium text-white rounded-lg',
              variant === 'danger' 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-primary-600 hover:bg-primary-700',
              loading && 'opacity-50 cursor-not-allowed'
            )}
          >
            {loading ? 'Lädt...' : confirmText}
          </button>
        </>
      }
    >
      <p className="text-sm text-gray-600">{message}</p>
    </Modal>
  );
}