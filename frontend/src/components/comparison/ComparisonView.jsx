import React, { useState, useEffect } from 'react';
import { getComparison } from '../../services/comparisonService';
import LoadingSpinner from '../common/LoadingSpinner';
import Button from '../common/Button';
import ComparisonSummary from './ComparisonSummary';
import ComparisonCharts from './ComparisonCharts';
import CategoryHeatmap from './CategoryHeatmap';
import TopRecipientsComparison from './TopRecipientsComparison';

/**
 * Period Comparison View - As Tab Component
 * Compare two time periods side-by-side
 */
export default function ComparisonView({ accountId }) {

  // Comparison state
  const [comparisonType, setComparisonType] = useState('month');
  const [period1, setPeriod1] = useState('');
  const [period2, setPeriod2] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize with current and previous month
  useEffect(() => {
    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1);
    const previousMonth = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;

    setPeriod1(previousMonth);
    setPeriod2(currentMonth);
  }, []);

  // Load comparison data
  const loadComparison = async () => {
    if (!period1 || !period2) {
      setError('Bitte wähle beide Zeiträume aus');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getComparison(accountId, comparisonType, period1, period2);
      setComparisonData(data);
    } catch (err) {
      console.error('Error loading comparison:', err);
      setError(err.response?.data?.detail || 'Fehler beim Laden der Vergleichsdaten');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (period1 && period2 && accountId) {
      loadComparison();
    }
  }, [period1, period2, comparisonType, accountId]);

  // Generate month options (last 24 months)
  const getMonthOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 24; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const label = date.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
      options.push({ value, label });
    }
    return options;
  };

  // Generate year options (last 10 years)
  const getYearOptions = () => {
    const options = [];
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 10; i++) {
      const year = currentYear - i;
      options.push({ value: String(year), label: String(year) });
    }
    return options;
  };

  const periodOptions = comparisonType === 'month' ? getMonthOptions() : getYearOptions();

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Comparison Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vergleichstyp
              </label>
              <select
                value={comparisonType}
                onChange={(e) => setComparisonType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="month">Monat</option>
                <option value="year">Jahr</option>
              </select>
            </div>

            {/* Period 1 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zeitraum 1
              </label>
              <select
                value={period1}
                onChange={(e) => setPeriod1(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Bitte wählen...</option>
                {periodOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Period 2 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zeitraum 2
              </label>
              <select
                value={period2}
                onChange={(e) => setPeriod2(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Bitte wählen...</option>
                {periodOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Refresh Button */}
            <div className="flex items-end">
              <Button
                onClick={loadComparison}
                disabled={loading || !period1 || !period2}
                className="w-full"
              >
                {loading ? 'Lädt...' : 'Vergleichen'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
              {error}
            </div>
          )}
        </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="xl" text="Lade Vergleichsdaten..." />
        </div>
      ) : comparisonData ? (
        <div className="space-y-6">
          {/* Summary Cards */}
          <ComparisonSummary data={comparisonData} />

          {/* Charts */}
          <ComparisonCharts data={comparisonData} />

          {/* Category Heatmap */}
          <CategoryHeatmap data={comparisonData} />

          {/* Top Recipients */}
          <TopRecipientsComparison data={comparisonData} />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">
            Wähle zwei Zeiträume aus, um sie zu vergleichen
          </p>
        </div>
      )}
    </div>
  );
}
