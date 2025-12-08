import { create } from 'zustand';
import { subMonths, startOfMonth, endOfMonth, startOfYear, endOfYear, subYears, format } from 'date-fns';

/**
 * Zustand Store für globale Filter
 * 
 * Verwaltet Filter-State über verschiedene Views hinweg
 * 
 * FEATURES:
 * - Date Range Filter (Quick Buttons + Custom)
 * - Account Filter
 * - Category Filter
 * - Recipient Filter
 * - Search Filter
 * - Persistenz in localStorage
 * 
 * ERWEITERBARKEIT:
 * - Tag Filter
 * - Projekt Filter
 * - Status Filter (Pending, Completed, etc.)
 * - Betrag Range Filter
 */

// Quick Date Range Presets
export const DATE_PRESETS = {
  THIS_MONTH: {
    label: 'Dieser Monat',
    getRange: () => ({
      fromDate: startOfMonth(new Date()),
      toDate: endOfMonth(new Date()),
    }),
  },
  LAST_MONTH: {
    label: 'Letzter Monat',
    getRange: () => {
      const lastMonth = subMonths(new Date(), 1);
      return {
        fromDate: startOfMonth(lastMonth),
        toDate: endOfMonth(lastMonth),
      };
    },
  },
  LAST_3_MONTHS: {
    label: 'Letzte 3 Monate',
    getRange: () => ({
      fromDate: subMonths(new Date(), 3),
      toDate: new Date(),
    }),
  },
  LAST_6_MONTHS: {
    label: 'Letzte 6 Monate',
    getRange: () => ({
      fromDate: subMonths(new Date(), 6),
      toDate: new Date(),
    }),
  },
  THIS_YEAR: {
    label: 'Dieses Jahr',
    getRange: () => ({
      fromDate: startOfYear(new Date()),
      toDate: endOfYear(new Date()),
    }),
  },
  LAST_YEAR: {
    label: 'Letztes Jahr',
    getRange: () => {
      const lastYear = subYears(new Date(), 1);
      return {
        fromDate: startOfYear(lastYear),
        toDate: endOfYear(lastYear),
      };
    },
  },
  ALL: {
    label: 'Alle',
    getRange: () => ({
      // Return null for both dates to indicate no date filtering
      fromDate: null,
      toDate: null,
    }),
  },
};

// Transaction Type Options
export const TRANSACTION_TYPES = {
  ALL: { value: 'all', label: 'Alle' },
  INCOME: { value: 'income', label: 'Einnahmen' },
  EXPENSE: { value: 'expense', label: 'Ausgaben' },
};

export const useFilterStore = create((set, get) => ({
  // Date Range
  fromDate: subMonths(new Date(), 1),
  toDate: new Date(),
  datePreset: 'LAST_MONTH',

  // Filters
  selectedAccountIds: [], // [] = alle, [id] = spezifisch
  selectedCategoryIds: [], // [] = alle
  selectedRecipients: [], // [] = alle
  searchQuery: '',
  transactionType: 'all', // 'all', 'income', 'expense'
  
  // NEW: Advanced Filters
  minAmount: null, // Minimum transaction amount
  maxAmount: null, // Maximum transaction amount
  recipientQuery: '', // Recipient search query
  purposeQuery: '', // Purpose/description search query (renamed from descriptionQuery)
  showUncategorizedOnly: false, // Show only transactions without category

  // UI State
  showFilters: false,

  // Actions

  /**
   * Set Date Range
   * @param {Date} fromDate
   * @param {Date} toDate
   * @param {string} preset - Key from DATE_PRESETS
   */
  setDateRange: (fromDate, toDate, preset = 'CUSTOM') => {
    set({
      fromDate,
      toDate,
      datePreset: preset,
    });
  },

  /**
   * Apply Date Preset
   * @param {string} presetKey - Key from DATE_PRESETS
   */
  applyDatePreset: (presetKey) => {
    const preset = DATE_PRESETS[presetKey];
    if (!preset) return;

    const { fromDate, toDate } = preset.getRange();
    set({
      fromDate,
      toDate,
      datePreset: presetKey,
    });
  },

  /**
   * Set Transaction Type Filter
   * @param {string} type - 'all', 'income', 'expense'
   */
  setTransactionType: (type) => {
    set({ transactionType: type });
  },

  /**
   * Set Account Filter
   * @param {number[]} accountIds - [] für alle
   */
  setAccountFilter: (accountIds) => {
    set({ selectedAccountIds: Array.isArray(accountIds) ? accountIds : [accountIds] });
  },

  /**
   * Toggle Account in Filter
   * @param {number} accountId
   */
  toggleAccount: (accountId) => {
    set((state) => {
      const ids = state.selectedAccountIds;
      if (ids.includes(accountId)) {
        return { selectedAccountIds: ids.filter((id) => id !== accountId) };
      }
      return { selectedAccountIds: [...ids, accountId] };
    });
  },

  /**
   * Set Category Filter
   * @param {number[]} categoryIds - [] für alle
   */
  setCategoryFilter: (categoryIds) => {
    set({ selectedCategoryIds: Array.isArray(categoryIds) ? categoryIds : [categoryIds] });
  },

  /**
   * Toggle Category in Filter
   * @param {number} categoryId
   */
  toggleCategory: (categoryId) => {
    set((state) => {
      const ids = state.selectedCategoryIds;
      if (ids.includes(categoryId)) {
        return { selectedCategoryIds: ids.filter((id) => id !== categoryId) };
      }
      return { selectedCategoryIds: [...ids, categoryId] };
    });
  },

  /**
   * Set Recipient Filter
   * @param {string[]} recipients
   */
  setRecipientFilter: (recipients) => {
    set({ selectedRecipients: Array.isArray(recipients) ? recipients : [recipients] });
  },

  /**
   * Toggle Recipient in Filter
   * @param {string} recipient
   */
  toggleRecipient: (recipient) => {
    set((state) => {
      const recipients = state.selectedRecipients;
      if (recipients.includes(recipient)) {
        return { selectedRecipients: recipients.filter((r) => r !== recipient) };
      }
      return { selectedRecipients: [...recipients, recipient] };
    });
  },

  /**
   * Set Search Query
   * @param {string} query
   */
  setSearchQuery: (query) => {
    set({ searchQuery: query });
  },

  /**
   * Set Transaction Type Filter
   * @param {string} type - 'all', 'income', 'expense'
   */
  setTransactionType: (type) => {
    if (!['all', 'income', 'expense'].includes(type)) {
      console.warn(`Invalid transaction type: ${type}`);
      return;
    }
    set({ transactionType: type });
  },

  /**
   * Set Amount Range Filter
   * @param {number|null} min
   * @param {number|null} max
   */
  setAmountRange: (min, max) => {
    set({ minAmount: min, maxAmount: max });
  },

  /**
   * Set Recipient Query Filter
   * @param {string} query
   */
  setRecipientQuery: (query) => {
    set({ recipientQuery: query });
  },

  /**
   * Set Purpose/Description Query Filter
   * @param {string} query
   */
  setPurposeQuery: (query) => {
    set({ purposeQuery: query });
  },

  /**
   * Set Show Uncategorized Only Filter
   * @param {boolean} value
   */
  setShowUncategorizedOnly: (value) => {
    set({ showUncategorizedOnly: value });
  },

  /**
   * Toggle Filter Panel
   */
  toggleFilters: () => {
    set((state) => ({ showFilters: !state.showFilters }));
  },

  /**
   * Reset All Filters
   */
  resetFilters: () => {
    set({
      fromDate: subMonths(new Date(), 1),
      toDate: new Date(),
      datePreset: 'LAST_MONTH',
      selectedAccountIds: [],
      selectedCategoryIds: [],
      selectedRecipients: [],
      searchQuery: '',
      transactionType: 'all',
      minAmount: null,
      maxAmount: null,
      recipientQuery: '',
      purposeQuery: '',
      showUncategorizedOnly: false,
    });
  },

  /**
   * Get active filters as query params
   * @returns {object}
   */
  getQueryParams: () => {
    const state = get();
    const params = {};

    // Only add date filters if they are set (not null)
    if (state.fromDate !== null) {
      params.fromDate = format(state.fromDate, 'yyyy-MM-dd');
    }
    if (state.toDate !== null) {
      params.toDate = format(state.toDate, 'yyyy-MM-dd');
    }
    if (state.selectedAccountIds.length > 0) {
      params.accountIds = state.selectedAccountIds.join(',');
    }
    if (state.selectedCategoryIds.length > 0) {
      params.categoryIds = state.selectedCategoryIds.join(',');
    }
    if (state.selectedRecipients.length > 0) {
      params.recipients = state.selectedRecipients.join(',');
    }
    if (state.searchQuery) {
      params.search = state.searchQuery;
    }
    if (state.transactionType && state.transactionType !== 'all') {
      params.transactionType = state.transactionType;
    }
    if (state.minAmount !== null) {
      params.minAmount = state.minAmount;
    }
    if (state.maxAmount !== null) {
      params.maxAmount = state.maxAmount;
    }
    if (state.recipientQuery) {
      params.recipient = state.recipientQuery;
    }
    if (state.purposeQuery) {
      params.purpose = state.purposeQuery;  // Changed from description to purpose
    }
    if (state.showUncategorizedOnly) {
      params.uncategorized = 'true';
    }

    return params;
  },

  /**
   * Check if any filter is active
   * @returns {boolean}
   */
  hasActiveFilters: () => {
    const state = get();
    return (
      state.selectedAccountIds.length > 0 ||
      state.selectedCategoryIds.length > 0 ||
      state.selectedRecipients.length > 0 ||
      state.searchQuery !== '' ||
      state.minAmount !== null ||
      state.maxAmount !== null ||
      state.recipientQuery !== '' ||
      state.purposeQuery !== '' ||
      state.showUncategorizedOnly
    );
  },

  /**
   * Get active filter count
   * @returns {number}
   */
  getActiveFilterCount: () => {
    const state = get();
    let count = 0;
    
    if (state.selectedAccountIds.length > 0) count++;
    if (state.selectedCategoryIds.length > 0) count++;
    if (state.selectedRecipients.length > 0) count++;
    if (state.searchQuery !== '') count++;
    if (state.minAmount !== null) count++;
    if (state.maxAmount !== null) count++;
    if (state.recipientQuery !== '') count++;
    if (state.purposeQuery !== '') count++;
    if (state.showUncategorizedOnly) count++;
    
    return count;
  },
}));
