/**
 * Unified Filter Component
 * 
 * Einheitliche Filter-Komponente für alle Views:
 * - Date Range mit Quick-Presets
 * - Category Filter
 * - Transaction Type (Income/Expense/All)
 * - Search
 * - Advanced Filters (Amount Range, Recipient, Description)
 * - Reset Button
 * 
 * FEATURES:
 * - Flexibel konfigurierbar (welche Filter anzeigen)
 * - Konsistentes Design
 * - Globaler Filter-Store (Zustand)
 * - Active Filter Count Badge
 */

import React, { useState } from 'react';
import { useFilterStore, DATE_PRESETS } from '../../store/filterStore';
import { useCategoryStore } from '../../store/categoryStore';
import { parseAmount } from '../../utils/amount';

export default function UnifiedFilter({
  showDateRange = true,
  showCategory = true,
  showTransactionType = false,
  showSearch = false,
  showAdvancedFilters = true,
  compact = false,
  onChange,
}) {
  const {
    fromDate,
    toDate,
    datePreset,
    selectedCategoryIds,
    transactionType,
    searchQuery,
    minAmount,
    maxAmount,
    recipientQuery,
    purposeQuery,  // Changed from descriptionQuery
    setDateRange,
    applyDatePreset,
    setCategoryFilter,
    setTransactionType,
    setSearchQuery,
    setAmountRange,
    setRecipientQuery,
    setPurposeQuery,  // Changed from setDescriptionQuery
    resetFilters,
    hasActiveFilters,
    getActiveFilterCount,
  } = useFilterStore();

  const { categories } = useCategoryStore();

  const [showCustomDateRange, setShowCustomDateRange] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // NOTE: advanced inputs update the global filter store immediately on change

  const handleDatePresetChange = (presetKey) => {
    applyDatePreset(presetKey);
    setShowCustomDateRange(false);
    onChange?.();
  };

  const handleCustomDateChange = (from, to) => {
    setDateRange(from, to, 'CUSTOM');
    onChange?.();
  };

  const handleCategoryChange = (categoryId) => {
    const currentIds = selectedCategoryIds;
    let newIds;
    
    if (categoryId === 'all') {
      newIds = [];
    } else {
      if (currentIds.includes(categoryId)) {
        newIds = currentIds.filter(id => id !== categoryId);
      } else {
        newIds = [...currentIds, categoryId];
      }
    }
    
    setCategoryFilter(newIds);
    onChange?.();
  };

  const handleSearchChange = (query) => {
    setSearchQuery(query);
    onChange?.();
  };

  const handleReset = () => {
    resetFilters();
    setShowCustomDateRange(false);
    setShowAdvanced(false);
    // resetFilters() updates the store values (minAmount, maxAmount, ...)
    onChange?.();
  };

  const handleAmountChange = (min, max) => {
    const parsedMin = min !== '' && min !== null ? parseAmount(min) : null;
    const parsedMax = max !== '' && max !== null ? parseAmount(max) : null;
    setAmountRange(parsedMin, parsedMax);
    onChange?.();
  };

  const handleRecipientQueryChange = (query) => {
    setRecipientQuery(query);
    onChange?.();
  };

  const handlePurposeQueryChange = (query) => {
    setPurposeQuery(query);
    onChange?.();
  };

  const activeFilterCount = getActiveFilterCount();

  if (compact) {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        {/* Compact Filter Toggle */}
        <button
          onClick={() => setShowCustomDateRange(!showCustomDateRange)}
          className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filter
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold text-white bg-primary-600 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>

        {hasActiveFilters() && (
          <button
            onClick={handleReset}
            className="px-3 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100"
          >
            Zurücksetzen
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <h3 className="text-sm font-semibold text-gray-900">Filter</h3>
            {activeFilterCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold text-white bg-primary-600 rounded-full">
                {activeFilterCount}
              </span>
            )}
          </div>

          {hasActiveFilters() && (
            <button
              onClick={handleReset}
              className="text-sm font-medium text-red-600 hover:text-red-700"
            >
              Alle zurücksetzen
            </button>
          )}
        </div>

        {/* Date Range Filter */}
        {showDateRange && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Zeitraum
            </label>
            
            {/* Quick Presets */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
              {Object.entries(DATE_PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => handleDatePresetChange(key)}
                  className={`
                    px-3 py-2 text-xs font-medium rounded-lg border transition-colors
                    ${datePreset === key
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }
                  `}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {/* Custom Date Range */}
            {showCustomDateRange && (
              <div className="grid grid-cols-2 gap-3 mt-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Von</label>
                  <input
                    type="date"
                    value={fromDate ? fromDate.toISOString().split('T')[0] : ''}
                    onChange={(e) => handleCustomDateChange(new Date(e.target.value), toDate)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Bis</label>
                  <input
                    type="date"
                    value={toDate ? toDate.toISOString().split('T')[0] : ''}
                    onChange={(e) => handleCustomDateChange(fromDate, new Date(e.target.value))}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            )}

            <button
              onClick={() => setShowCustomDateRange(!showCustomDateRange)}
              className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium"
            >
              {showCustomDateRange ? '− Weniger' : '+ Eigener Zeitraum'}
            </button>
          </div>
        )}

        {/* Category Filter */}
        {showCategory && categories.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kategorie
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleCategoryChange('all')}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors
                  ${selectedCategoryIds.length === 0
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }
                `}
              >
                Alle
              </button>
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategoryChange(category.id)}
                  className={`
                    px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors flex items-center gap-1
                    ${selectedCategoryIds.includes(category.id)
                      ? 'text-white border-transparent'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }
                  `}
                  style={selectedCategoryIds.includes(category.id) ? { backgroundColor: category.color } : {}}
                >
                  {category.icon && <span>{category.icon}</span>}
                  {category.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Search Filter */}
        {showSearch && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suche
            </label>
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Empfänger, Verwendungszweck..."
                className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              {searchQuery && (
                <button
                  onClick={() => handleSearchChange('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="pt-3 border-t border-gray-200">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700 mb-3"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={showAdvanced ? "M19 9l-7 7-7-7" : "M9 5l7 7-7 7"} />
              </svg>
              {showAdvanced ? 'Erweiterte Filter ausblenden' : 'Erweiterte Filter anzeigen'}
            </button>

            {showAdvanced && (
              <div className="space-y-3">
                {/* Amount Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Betrag (€)
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Min"
                        value={minAmount !== null ? minAmount : ''}
                        onChange={(e) => handleAmountChange(e.target.value, maxAmount)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Max"
                        value={maxAmount !== null ? maxAmount : ''}
                        onChange={(e) => handleAmountChange(minAmount, e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Recipient Query */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Empfänger
                  </label>
                  <input
                    type="text"
                    placeholder="z.B. REWE, Amazon..."
                    value={recipientQuery || ''}
                    onChange={(e) => handleRecipientQueryChange(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                {/* Description Query */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Verwendungszweck
                  </label>
                  <input
                    type="text"
                    placeholder="Beschreibung durchsuchen..."
                    value={purposeQuery || ''}
                    onChange={(e) => handlePurposeQueryChange(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                {/* Apply Filters Button removed: filters apply immediately on input/change */}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
