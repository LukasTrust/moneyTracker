import React, { useState, useEffect } from 'react';
import { 
  getComparison, 
  getMultiYearComparison, 
  getQuarterlyComparison, 
  getBenchmarkAnalysis 
} from '../../services/comparisonService';
import LoadingSpinner from '../common/LoadingSpinner';
import Button from '../common/Button';
import ComparisonSummary from './ComparisonSummary';
import ComparisonCharts from './ComparisonCharts';
import CategoryHeatmap from './CategoryHeatmap';
import TopRecipientsComparison from './TopRecipientsComparison';
import BenchmarkAnalysis from './BenchmarkAnalysis';
import MultiYearComparison from './MultiYearComparison';
import QuarterlyComparison from './QuarterlyComparison';

/**
 * Period Comparison View - As Tab Component
 * Compare two time periods side-by-side with multiple comparison modes
 */
export default function ComparisonView({ accountId }) {

  // Comparison mode: 'standard', 'multi-year', 'quarterly', 'benchmark'
  const [comparisonMode, setComparisonMode] = useState('standard');
  
  // Standard comparison state
  const [comparisonType, setComparisonType] = useState('month');
  const [period1, setPeriod1] = useState('');
  const [period2, setPeriod2] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  
  // Multi-year comparison state
  const [selectedYears, setSelectedYears] = useState([]);
  const [multiYearData, setMultiYearData] = useState(null);
  
  // Quarterly comparison state
  const [quarterlyYear, setQuarterlyYear] = useState(new Date().getFullYear());
  const [compareToPreviousYear, setCompareToPreviousYear] = useState(false);
  const [quarterlyData, setQuarterlyData] = useState(null);
  
  // Benchmark state
  const [benchmarkYear, setBenchmarkYear] = useState(new Date().getFullYear());
  const [benchmarkMonth, setBenchmarkMonth] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize multi-year with last 3 years
  useEffect(() => {
    const currentYear = new Date().getFullYear();
    setSelectedYears([currentYear - 2, currentYear - 1, currentYear]);
  }, []);

  // Initialize with current and previous month
  useEffect(() => {
    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1);
    const previousMonth = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;

    setPeriod1(previousMonth);
    setPeriod2(currentMonth);
  }, []);

  // Update periods when comparison type changes
  useEffect(() => {
    const now = new Date();
    
    if (comparisonType === 'month') {
      const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
      const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1);
      const previousMonth = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;
      
      setPeriod1(previousMonth);
      setPeriod2(currentMonth);
    } else if (comparisonType === 'year') {
      const currentYear = String(now.getFullYear());
      const previousYear = String(now.getFullYear() - 1);
      
      setPeriod1(previousYear);
      setPeriod2(currentYear);
    }
  }, [comparisonType]);

  // Load comparison data
  const loadComparison = async () => {
    if (!period1 || !period2) {
      setError('Bitte wähle beide Zeiträume aus');
      return;
    }

    // Validate format matches comparison type
    if (comparisonType === 'year') {
      // Check if periods are in year format (YYYY)
      if (period1.includes('-') || period2.includes('-')) {
        // Invalid format for year comparison, skip loading silently
        // The periods will be updated shortly by the useEffect
        console.log('Skipping comparison load - waiting for period format to update');
        return;
      }
    } else if (comparisonType === 'month') {
      // Check if periods are in month format (YYYY-MM)
      if (!period1.includes('-') || !period2.includes('-')) {
        // Invalid format for month comparison, skip loading silently
        console.log('Skipping comparison load - waiting for period format to update');
        return;
      }
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

  // Load multi-year comparison
  const loadMultiYearComparison = async () => {
    if (selectedYears.length < 2) {
      setError('Wähle mindestens 2 Jahre aus');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await getMultiYearComparison(accountId, selectedYears);
      setMultiYearData(data);
    } catch (err) {
      console.error('Error loading multi-year comparison:', err);
      setError(err.response?.data?.detail || 'Fehler beim Laden der Mehrjahres-Daten');
    } finally {
      setLoading(false);
    }
  };

  // Load quarterly comparison
  const loadQuarterlyComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getQuarterlyComparison(accountId, quarterlyYear, compareToPreviousYear);
      setQuarterlyData(data);
    } catch (err) {
      console.error('Error loading quarterly comparison:', err);
      setError(err.response?.data?.detail || 'Fehler beim Laden der Quartalsdaten');
    } finally {
      setLoading(false);
    }
  };

  // Load benchmark analysis
  const loadBenchmarkAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getBenchmarkAnalysis(accountId, benchmarkYear, benchmarkMonth);
      setBenchmarkData(data);
    } catch (err) {
      console.error('Error loading benchmark analysis:', err);
      setError(err.response?.data?.detail || 'Fehler beim Laden der Benchmark-Daten');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (period1 && period2 && accountId && comparisonMode === 'standard') {
      loadComparison();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period1, period2, comparisonType, accountId, comparisonMode]);

  // Load data when mode or parameters change
  useEffect(() => {
    if (!accountId) return;

    if (comparisonMode === 'multi-year' && selectedYears.length >= 2) {
      loadMultiYearComparison();
    } else if (comparisonMode === 'quarterly') {
      loadQuarterlyComparison();
    } else if (comparisonMode === 'benchmark') {
      loadBenchmarkAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comparisonMode, selectedYears, quarterlyYear, compareToPreviousYear, benchmarkYear, benchmarkMonth, accountId]);

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

  // Generate year options for multi-year (last 10 years)
  const getAvailableYears = () => {
    const options = [];
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 10; i++) {
      options.push(currentYear - i);
    }
    return options;
  };

  const availableYears = getAvailableYears();

  // Toggle year selection
  const toggleYear = (year) => {
    if (selectedYears.includes(year)) {
      setSelectedYears(selectedYears.filter(y => y !== year));
    } else {
      if (selectedYears.length < 5) {
        setSelectedYears([...selectedYears, year].sort());
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-lg font-semibold text-neutral-900">Vergleichsmodus</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <button
            onClick={() => setComparisonMode('standard')}
            className={`px-4 py-3 rounded-lg border-2 transition-colors ${
              comparisonMode === 'standard'
                ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                : 'border-neutral-200 hover:border-neutral-300 text-neutral-700'
            }`}
          >
            Standard-Vergleich
          </button>
          <button
            onClick={() => setComparisonMode('multi-year')}
            className={`px-4 py-3 rounded-lg border-2 transition-colors ${
              comparisonMode === 'multi-year'
                ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                : 'border-neutral-200 hover:border-neutral-300 text-neutral-700'
            }`}
          >
            Mehrjahres-Vergleich
          </button>
          <button
            onClick={() => setComparisonMode('quarterly')}
            className={`px-4 py-3 rounded-lg border-2 transition-colors ${
              comparisonMode === 'quarterly'
                ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                : 'border-neutral-200 hover:border-neutral-300 text-neutral-700'
            }`}
          >
            Quartalsvergleich
          </button>
          <button
            onClick={() => setComparisonMode('benchmark')}
            className={`px-4 py-3 rounded-lg border-2 transition-colors ${
              comparisonMode === 'benchmark'
                ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                : 'border-neutral-200 hover:border-neutral-300 text-neutral-700'
            }`}
          >
            Benchmark
          </button>
        </div>
      </div>

      {/* Controls based on mode */}
      {comparisonMode === 'standard' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Comparison Type */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Vergleichstyp
              </label>
              <select
                value={comparisonType}
                onChange={(e) => setComparisonType(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="month">Monat</option>
                <option value="year">Jahr</option>
              </select>
            </div>

            {/* Period 1 */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Zeitraum 1
              </label>
              <select
                value={period1}
                onChange={(e) => setPeriod1(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Zeitraum 2
              </label>
              <select
                value={period2}
                onChange={(e) => setPeriod2(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
      )}

      {/* Multi-Year Controls */}
      {comparisonMode === 'multi-year' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">
            Jahre auswählen (2-5 Jahre)
          </h3>
          <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
            {availableYears.map((year) => (
              <button
                key={year}
                onClick={() => toggleYear(year)}
                className={`px-3 py-2 rounded-lg border-2 transition-colors ${
                  selectedYears.includes(year)
                    ? 'border-blue-500 bg-blue-50 text-blue-700 font-semibold'
                    : 'border-neutral-200 hover:border-neutral-300 text-neutral-700'
                }`}
              >
                {year}
              </button>
            ))}
          </div>
          {selectedYears.length < 2 && (
            <p className="text-sm text-amber-600 mt-2">
              Wähle mindestens 2 Jahre aus
            </p>
          )}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Quarterly Controls */}
      {comparisonMode === 'quarterly' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Jahr
              </label>
              <select
                value={quarterlyYear}
                onChange={(e) => setQuarterlyYear(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableYears.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Optionen
              </label>
              <label className="flex items-center gap-2 px-3 py-2 border border-neutral-300 rounded-md cursor-pointer hover:bg-neutral-50">
                <input
                  type="checkbox"
                  checked={compareToPreviousYear}
                  onChange={(e) => setCompareToPreviousYear(e.target.checked)}
                  className="rounded border-neutral-300"
                />
                <span className="text-sm text-neutral-700">
                  Mit Vorjahr vergleichen
                </span>
              </label>
            </div>
          </div>
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Benchmark Controls */}
      {comparisonMode === 'benchmark' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Jahr
              </label>
              <select
                value={benchmarkYear}
                onChange={(e) => setBenchmarkYear(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableYears.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Monat (optional)
              </label>
              <select
                value={benchmarkMonth || ''}
                onChange={(e) => setBenchmarkMonth(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Ganzes Jahr</option>
                {[...Array(12)].map((_, i) => {
                  const monthDate = new Date(2024, i, 1);
                  return (
                    <option key={i + 1} value={i + 1}>
                      {monthDate.toLocaleDateString('de-DE', { month: 'long' })}
                    </option>
                  );
                })}
              </select>
            </div>
          </div>
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="xl" text="Lade Vergleichsdaten..." />
        </div>
      ) : (
        <>
          {comparisonMode === 'standard' && comparisonData && (
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
          )}

          {comparisonMode === 'multi-year' && multiYearData && (
            <MultiYearComparison data={multiYearData} />
          )}

          {comparisonMode === 'quarterly' && quarterlyData && (
            <QuarterlyComparison data={quarterlyData} />
          )}

          {comparisonMode === 'benchmark' && benchmarkData && (
            <BenchmarkAnalysis data={benchmarkData} />
          )}

          {!loading && (
            (comparisonMode === 'standard' && !comparisonData) ||
            (comparisonMode === 'multi-year' && !multiYearData) ||
            (comparisonMode === 'quarterly' && !quarterlyData) ||
            (comparisonMode === 'benchmark' && !benchmarkData)
          ) && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-neutral-500">
                {comparisonMode === 'standard' && 'Wähle zwei Zeiträume aus, um sie zu vergleichen'}
                {comparisonMode === 'multi-year' && 'Wähle mindestens 2 Jahre für den Vergleich aus'}
                {comparisonMode === 'quarterly' && 'Lade Quartalsdaten...'}
                {comparisonMode === 'benchmark' && 'Lade Benchmark-Daten...'}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
