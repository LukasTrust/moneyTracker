import React, { useMemo } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import UnifiedFilter from '../common/UnifiedFilter';
import { useDashboardData } from '../../hooks/useDataFetch';
import { useFilterStore } from '../../store/filterStore';
import { format } from 'date-fns';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

/**
 * DashboardGraphOverview - Gesamt-Übersicht über alle Accounts
 * 
 * FEATURES:
 * - Aggregierte KPIs (Einnahmen, Ausgaben, Saldo, Transaktionsanzahl)
 * - Line Chart: Saldoentwicklung über Zeit
 * - Pie Chart: Top-Kategorien nach Ausgaben
 * - DateRangeFilter mit Quick-Buttons (globaler Store)
 * - Responsive Layout
 * 
 * WIEDERVERWENDBARKEIT:
 * - Nutzt dieselben Komponenten wie Account-Tabs (DateRangeFilter, Charts)
 * - useDashboardData Hook kapselt Datenfetch-Logik
 * - Memoization für Performance
 * 
 * ERWEITERBARKEIT:
 * - Drilldown: Klick auf Kategorie zeigt Transaktionen
 * - Account-Filter: Nur bestimmte Accounts anzeigen
 * - Export: CSV/PDF-Export der Übersicht
 * - Vergleich: Jahr-über-Jahr oder Monat-über-Monat
 */
function DashboardGraphOverview() {
  // Get date range from global filter store
  const { fromDate, toDate, setDateRange, applyDatePreset } = useFilterStore();
  
  // Convert Date objects to ISO strings for API
  const dateRange = useMemo(() => ({
    fromDate: fromDate ? format(fromDate, 'yyyy-MM-dd') : '',
    toDate: toDate ? format(toDate, 'yyyy-MM-dd') : '',
  }), [fromDate, toDate]);

  // Fetch Dashboard Data
  const { summary, categories, balanceHistory, recipients, senders, loading, error, refetch } = useDashboardData(dateRange);

  /**
   * Format currency
   */
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR'
    }).format(value);
  };

  /**
   * Prepare Line Chart Data
   */
  const lineChartData = useMemo(() => {
    if (!balanceHistory || !balanceHistory.labels || balanceHistory.labels.length === 0) {
      return [];
    }

    const result = balanceHistory.labels.map((label, index) => ({
      month: label,
      Einnahmen: balanceHistory.income[index] || 0,
      Ausgaben: Math.abs(balanceHistory.expenses[index] || 0), // Positiv darstellen
      Saldo: balanceHistory.balance[index] || 0
    }));
    
    console.log('Line chart data prepared:', result);
    return result;
  }, [balanceHistory]);

  /**
   * Prepare Pie Chart Data (nur Ausgaben, Top 10)
   */
  const expensesPieData = useMemo(() => {
    console.log('Preparing expensesPieData from:', categories);
    
    if (!categories || categories.length === 0) {
      console.log('No categories data available');
      return [];
    }

    const result = categories
      .filter(cat => cat.total_amount < 0) // Nur Ausgaben
      .slice(0, 10) // Top 10
      .map(cat => ({
        name: cat.category_name,
        value: Math.abs(cat.total_amount),
        color: cat.color,
        icon: cat.icon,
        count: cat.transaction_count
      }));
    
    console.log('Expenses pie data prepared:', result);
    return result;
  }, [categories]);

  /**
   * Prepare Pie Chart Data (nur Einnahmen)
   */
  const incomePieData = useMemo(() => {
    console.log('Preparing incomePieData from:', categories);
    
    if (!categories || categories.length === 0) {
      console.log('No categories data available for income');
      return [];
    }

    const result = categories
      .filter(cat => cat.total_amount > 0) // Nur Einnahmen
      .map(cat => ({
        name: cat.category_name,
        value: cat.total_amount,
        color: cat.color,
        icon: cat.icon,
        count: cat.transaction_count
      }));
    
    console.log('Income pie data prepared:', result);
    return result;
  }, [categories]);

  /**
   * Custom Tooltip für Charts
   */
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  /**
   * Custom Label für Pie Chart
   */
  const renderPieLabel = (entry) => {
    if (entry.percent > 0.05) { // Nur wenn > 5%
      return `${(entry.percent * 100).toFixed(0)}%`;
    }
    return '';
  };

  // Loading State
  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <Card>
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Fehler beim Laden</h3>
          <p className="mt-1 text-sm text-gray-500">{error}</p>
          <Button onClick={refetch} className="mt-4">
            Erneut versuchen
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">📊 Gesamt-Übersicht</h2>
        <p className="text-sm text-gray-600 mt-1">
          Aggregierte Daten über alle {summary?.account_count || 0} Konten
        </p>
      </div>

      {/* Unified Filter - NEW! */}
      <UnifiedFilter
        showDateRange={true}
        showCategory={true}
        showTransactionType={true}
        showSearch={false}
        onChange={() => refetch()}
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Einnahmen */}
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">Gesamt-Einnahmen</p>
              <p className="text-2xl font-bold text-green-900 mt-1">
                {formatCurrency(summary?.total_income || 0)}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
          </div>
        </Card>

        {/* Ausgaben */}
        <Card className="bg-gradient-to-br from-red-50 to-rose-50 border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-600">Gesamt-Ausgaben</p>
              <p className="text-2xl font-bold text-red-900 mt-1">
                {formatCurrency(summary?.total_expenses || 0)}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
            </div>
          </div>
        </Card>

        {/* Netto-Saldo */}
        <Card className={`bg-gradient-to-br ${
          (summary?.net_balance || 0) >= 0 
            ? 'from-blue-50 to-indigo-50 border-blue-200' 
            : 'from-orange-50 to-amber-50 border-orange-200'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${
                (summary?.net_balance || 0) >= 0 ? 'text-blue-600' : 'text-orange-600'
              }`}>
                Netto-Saldo
              </p>
              <p className={`text-2xl font-bold mt-1 ${
                (summary?.net_balance || 0) >= 0 ? 'text-blue-900' : 'text-orange-900'
              }`}>
                {formatCurrency(summary?.net_balance || 0)}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              (summary?.net_balance || 0) >= 0 ? 'bg-blue-100' : 'bg-orange-100'
            }`}>
              <svg className={`w-6 h-6 ${
                (summary?.net_balance || 0) >= 0 ? 'text-blue-600' : 'text-orange-600'
              }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </Card>

        {/* Transaktionen */}
        <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-600">Transaktionen</p>
              <p className="text-2xl font-bold text-purple-900 mt-1">
                {summary?.transaction_count || 0}
              </p>
              <p className="text-xs text-purple-600 mt-1">
                Über {summary?.account_count || 0} Konten
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </Card>
      </div>

      {/* Line Chart: Saldoentwicklung */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          📈 Saldoentwicklung über Zeit
        </h3>
        
        {lineChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={lineChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="month" 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis 
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="Einnahmen" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={{ fill: '#10b981', r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="Ausgaben" 
                stroke="#ef4444" 
                strokeWidth={2}
                dot={{ fill: '#ef4444', r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="Saldo" 
                stroke="#3b82f6" 
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-gray-500">
            Keine Daten für den ausgewählten Zeitraum
          </div>
        )}
      </Card>

      {/* Kategorie-Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ausgaben nach Kategorien */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            💸 Ausgaben nach Kategorien (Top 10)
          </h3>
          
          {expensesPieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={expensesPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderPieLabel}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {expensesPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => formatCurrency(value)}
                    content={<CustomTooltip />}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Legende */}
              <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
                {expensesPieData.map((cat, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="text-xl">{cat.icon}</span>
                      <span className="text-sm font-medium text-gray-700">{cat.name}</span>
                      <span className="text-xs text-gray-500">({cat.count})</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(cat.value)}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Keine Ausgaben-Kategorien vorhanden
            </div>
          )}
        </Card>

        {/* Einnahmen nach Kategorien */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            💰 Einnahmen nach Kategorien
          </h3>
          
          {incomePieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={incomePieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderPieLabel}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {incomePieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => formatCurrency(value)}
                    content={<CustomTooltip />}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Legende */}
              <div className="mt-4 space-y-2">
                {incomePieData.map((cat, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="text-xl">{cat.icon}</span>
                      <span className="text-sm font-medium text-gray-700">{cat.name}</span>
                      <span className="text-xs text-gray-500">({cat.count})</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(cat.value)}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Keine Einnahmen-Kategorien vorhanden
            </div>
          )}
        </Card>
      </div>

      {/* Empfänger/Absender Übersicht */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Absender (Einnahmen) */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            📥 Top Absender (Einnahmen)
          </h3>
          
          {senders && senders.length > 0 ? (
            <div className="space-y-3">
              {senders.slice(0, 5).map((sender, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-green-700">#{index + 1}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {sender.recipient}
                      </p>
                      <p className="text-xs text-gray-500">
                        {sender.transaction_count}× Transaktionen
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0 ml-4">
                    <p className="text-sm font-bold text-green-600">
                      {formatCurrency(sender.total_amount)}
                    </p>
                    <p className="text-xs text-gray-500 text-right">
                      {sender.percentage?.toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
              <p className="mt-2">Keine Absender-Daten verfügbar</p>
            </div>
          )}
        </Card>

        {/* Top Empfänger (Ausgaben) */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            📤 Top Empfänger (Ausgaben)
          </h3>
          
          {recipients && recipients.length > 0 ? (
            <div className="space-y-3">
              {recipients.slice(0, 5).map((recipient, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-red-700">#{index + 1}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {recipient.recipient}
                      </p>
                      <p className="text-xs text-gray-500">
                        {recipient.transaction_count}× Transaktionen
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0 ml-4">
                    <p className="text-sm font-bold text-red-600">
                      {formatCurrency(Math.abs(recipient.total_amount))}
                    </p>
                    <p className="text-xs text-gray-500 text-right">
                      {recipient.percentage?.toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
              <p className="mt-2">Keine Empfänger-Daten verfügbar</p>
            </div>
          )}
        </Card>
      </div>

      {/* DEVELOPER NOTE: Erweiterungsmöglichkeiten */}
      {/* 
      TODO: Weitere Features:
      
      1. Drilldown:
         - Klick auf Kategorie öffnet Modal mit Transaktionsliste
         - Klick auf Monat filtert alle Daten auf diesen Monat
      
      2. Account-Filter:
         - Dropdown zum Filtern auf bestimmte Accounts
         - Mehrfachauswahl möglich
      
      3. Export:
         - CSV-Export aller aggregierten Daten
         - PDF-Report mit Charts
      
      4. Vergleich:
         - Jahr-über-Jahr Vergleich (2023 vs 2024)
         - Monat-über-Monat Trend-Anzeige
      
      5. Prognosen:
         - Basierend auf historischen Daten
         - "Auf diesem Niveau würden Sie Ende Jahr X€ haben"
      
      6. Budgets:
         - Budget pro Kategorie setzen
         - Warnung wenn Budget überschritten
      */}
    </div>
  );
}

export default DashboardGraphOverview;
