/**
 * Unified Filter Component
 * 
 * Einheitliche Filter-Komponente für alle Views:
 * - Date Range mit Quick-Presets
 * - Category Filter
 * - Transaction Type (Income/Expense/All)
 * - Search
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

export default function UnifiedFilter({
  showDateRange = true,
  showCategory = true,
  showTransactionType = false,
  showSearch = false,
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
    setDateRange,
    applyDatePreset,
    setCategoryFilter,
    setTransactionType,
    setSearchQuery,
    resetFilters,
    hasActiveFilters,
    getActiveFilterCount,
  } = useFilterStore();

  const { categories } = useCategoryStore();

  const [showCustomDateRange, setShowCustomDateRange] = useState(false);

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
      </div>
    </div>
  );
}
