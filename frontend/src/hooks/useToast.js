/**
 * useToast Hook
 * 
 * Convenience hook für Toast Notifications
 * Verwendet den globalen UI Store
 */

import { useUIStore } from '../store';

export const useToast = () => {
  const {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showToast: showToastRaw,
  } = useUIStore();

  /**
   * Show toast notification
   * @param {string} message - Toast message
   * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
   * @param {number} duration - Duration in milliseconds (default: 3000)
   */
  const showToast = (message, type = 'info', duration = 3000) => {
    return showToastRaw({ message, type, duration });
  };

  return {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
};

export default useToast;
