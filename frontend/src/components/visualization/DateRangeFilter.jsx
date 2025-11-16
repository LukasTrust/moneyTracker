import React, { useState, useCallback, useMemo, useRef } from 'react';
import { format } from 'date-fns';
import { useFilterStore, DATE_PRESETS } from '../../store';
import Button from '../common/Button';
import clsx from 'clsx';

/**
 * Date Range Filter Komponente
 * 
 * Connected to global filter store
 * Displays quick buttons and custom date inputs
 * 
 * FEATURES:
 * - Quick date presets (This Month, Last 3 Months, etc.)
 * - Custom date range selection
 * - Validation
 * - Connected to global filter store
 * 
 * @example
 * <DateRangeFilter />
 */
export default function DateRangeFilter({ showCustomInputs = true }) {
  const { fromDate, toDate, datePreset, applyDatePreset, setDateRange } = useFilterStore();
  const [error, setError] = useState('');
  
  // Refs for custom date inputs
  const fromInputRef = useRef(null);
  const toInputRef = useRef(null);
  
  // Convert store dates to input format (yyyy-MM-dd)
  const customFrom = fromDate ? format(fromDate, 'yyyy-MM-dd') : '';
  const customTo = toDate ? format(toDate, 'yyyy-MM-dd') : '';

  /**
   * Quick Buttons Configuration
   */
  const quickButtons = useMemo(() => [
    { key: 'THIS_MONTH', ...DATE_PRESETS.THIS_MONTH },
    { key: 'LAST_MONTH', ...DATE_PRESETS.LAST_MONTH },
    { key: 'LAST_3_MONTHS', ...DATE_PRESETS.LAST_3_MONTHS },
    { key: 'LAST_6_MONTHS', ...DATE_PRESETS.LAST_6_MONTHS },
    { key: 'THIS_YEAR', ...DATE_PRESETS.THIS_YEAR },
    { key: 'LAST_YEAR', ...DATE_PRESETS.LAST_YEAR },
    { key: 'ALL', ...DATE_PRESETS.ALL },
  ], []);

  /**
   * Apply Quick Preset
   */
  const handleQuickButton = useCallback((presetKey) => {
    applyDatePreset(presetKey);
    setError('');
  }, [applyDatePreset]);

  /**
   * Apply Custom Date Range
   */
  const handleApplyCustom = useCallback((fromValue, toValue) => {
    if (!fromValue || !toValue) {
      setError('Bitte beide Daten auswählen');
      return;
    }

    const from = new Date(fromValue);
    const to = new Date(toValue);

    if (from > to) {
      setError('Startdatum muss vor dem Enddatum liegen');
      return;
    }

    setDateRange(from, to, 'CUSTOM');
    setError('');
  }, [setDateRange]);

  /**
   * Format current range for display
   */
  const currentRangeText = useMemo(() => {
    if (!fromDate || !toDate) return 'Alle Daten';
    return `${format(fromDate, 'dd.MM.yyyy')} - ${format(toDate, 'dd.MM.yyyy')}`;
  }, [fromDate, toDate]);

  return (
    <div className="space-y-4">
      {/* Current Selection Display */}
      <div className="text-sm text-gray-600">
        <span className="font-medium">Zeitraum:</span> {currentRangeText}
      </div>

      {/* Quick Buttons */}
      <div className="flex flex-wrap gap-2">
        {quickButtons.map((btn) => (
          <Button
            key={btn.key}
            size="sm"
            variant={datePreset === btn.key ? 'primary' : 'secondary'}
            onClick={() => handleQuickButton(btn.key)}
          >
            {btn.label}
          </Button>
        ))}
      </div>

      {/* Custom Date Inputs */}
      {showCustomInputs && (
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Benutzerdefinierten Zeitraum wählen
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Von</label>
              <input
                ref={fromInputRef}
                type="date"
                value={customFrom}
                onChange={(e) => {
                  const newFrom = e.target.value;
                  const newTo = toInputRef.current?.value;
                  if (newFrom && newTo) {
                    handleApplyCustom(newFrom, newTo);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Bis</label>
              <input
                ref={toInputRef}
                type="date"
                value={customTo}
                onChange={(e) => {
                  const newTo = e.target.value;
                  const newFrom = fromInputRef.current?.value;
                  if (newFrom && newTo) {
                    handleApplyCustom(newFrom, newTo);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}
        </div>
      )}
    </div>
  );
}
