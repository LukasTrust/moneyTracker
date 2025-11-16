import { create } from 'zustand';

/**
 * Zustand Store für UI State
 * 
 * Verwaltet globale UI States wie Modals, Toasts, Sidebars
 * 
 * FEATURES:
 * - Toast Notifications
 * - Modal Management
 * - Sidebar State
 * - Loading States
 * 
 * ERWEITERBARKEIT:
 * - Theme (Light/Dark Mode)
 * - Layout Preferences
 * - Accessibility Settings
 */

export const useUIStore = create((set, get) => ({
  // Toasts
  toasts: [],
  
  // Modals
  activeModal: null,
  modalData: null,

  // Sidebar
  sidebarOpen: true,

  // Global Loading
  globalLoading: false,

  // Actions

  /**
   * Show Toast Notification
   * @param {object} toast - { message, type, duration }
   */
  showToast: (toast) => {
    const id = Date.now() + Math.random();
    const newToast = {
      id,
      message: toast.message || 'Notification',
      type: toast.type || 'info', // 'success', 'error', 'warning', 'info'
      duration: toast.duration || 3000,
    };

    set((state) => ({
      toasts: [...state.toasts, newToast],
    }));

    // Auto-remove after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, newToast.duration);
    }

    return id;
  },

  /**
   * Show Success Toast
   * @param {string} message
   */
  showSuccess: (message) => {
    get().showToast({ message, type: 'success' });
  },

  /**
   * Show Error Toast
   * @param {string} message
   */
  showError: (message) => {
    get().showToast({ message, type: 'error', duration: 5000 });
  },

  /**
   * Show Warning Toast
   * @param {string} message
   */
  showWarning: (message) => {
    get().showToast({ message, type: 'warning' });
  },

  /**
   * Show Info Toast
   * @param {string} message
   */
  showInfo: (message) => {
    get().showToast({ message, type: 'info' });
  },

  /**
   * Remove Toast
   * @param {number} id
   */
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    }));
  },

  /**
   * Clear All Toasts
   */
  clearToasts: () => {
    set({ toasts: [] });
  },

  /**
   * Open Modal
   * @param {string} modalType - Type of modal
   * @param {object} data - Data for modal
   */
  openModal: (modalType, data = null) => {
    set({
      activeModal: modalType,
      modalData: data,
    });
  },

  /**
   * Close Modal
   */
  closeModal: () => {
    set({
      activeModal: null,
      modalData: null,
    });
  },

  /**
   * Toggle Sidebar
   */
  toggleSidebar: () => {
    set((state) => ({
      sidebarOpen: !state.sidebarOpen,
    }));
  },

  /**
   * Set Sidebar State
   * @param {boolean} open
   */
  setSidebar: (open) => {
    set({ sidebarOpen: open });
  },

  /**
   * Set Global Loading
   * @param {boolean} loading
   */
  setGlobalLoading: (loading) => {
    set({ globalLoading: loading });
  },
}));

/**
 * Toast Types
 */
export const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

/**
 * Modal Types
 */
export const MODAL_TYPES = {
  CREATE_ACCOUNT: 'createAccount',
  EDIT_ACCOUNT: 'editAccount',
  DELETE_ACCOUNT: 'deleteAccount',
  CREATE_CATEGORY: 'createCategory',
  EDIT_CATEGORY: 'editCategory',
  DELETE_CATEGORY: 'deleteCategory',
  UPLOAD_CSV: 'uploadCsv',
  CONFIRM: 'confirm',
  // ERWEITERBARKEIT:
  // CREATE_TAG: 'createTag',
  // CREATE_PROJECT: 'createProject',
  // EXPORT_DATA: 'exportData',
};
