import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

/**
 * Quarterly Comparison Component
 * Compare quarters within a year and optionally with previous year
 */
export default function QuarterlyComparison({ data }) {
  if (!data) return null;

  const { year, quarters, quarter_to_quarter_changes, year_summary } = data;

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Prepare chart data
  const chartData = quarters.map(q => ({
    quarter: q.quarter,
    Einnahmen: q.total_income,
    Ausgaben: Math.abs(q.total_expenses),
    Netto: q.net_balance
  }));

  // Check if we have previous year comparison
  const hasPreviousYearComparison = quarters.some(q => q.comparison_to_previous_year);

  return (
    <div className="space-y-6">
      {/* Year Summary */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow p-6 text-white">
        <h3 className="text-xl font-bold mb-4">Jahresübersicht {year}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm opacity-90">Gesamteinnahmen</div>
            <div className="text-2xl font-bold">{formatCurrency(year_summary.total_income)}</div>
            <div className="text-xs opacity-75 mt-1">
              Ø {formatCurrency(year_summary.avg_quarterly_income)} pro Quartal
            </div>
          </div>
          <div>
            <div className="text-sm opacity-90">Gesamtausgaben</div>
            <div className="text-2xl font-bold">{formatCurrency(Math.abs(year_summary.total_expenses))}</div>
            <div className="text-xs opacity-75 mt-1">
              Ø {formatCurrency(year_summary.avg_quarterly_expenses)} pro Quartal
            </div>
          </div>
          <div>
            <div className="text-sm opacity-90">Nettosaldo</div>
            <div className="text-2xl font-bold">
              {formatCurrency(year_summary.total_income + year_summary.total_expenses)}
            </div>
          </div>
        </div>
      </div>

      {/* Quarterly Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
          Quartalsvergleich {year}
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="quarter" />
            <YAxis tickFormatter={formatCurrency} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Bar dataKey="Einnahmen" fill="#10b981" />
            <Bar dataKey="Ausgaben" fill="#ef4444" />
            <Bar dataKey="Netto" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Quarter-to-Quarter Changes */}
      {quarter_to_quarter_changes && quarter_to_quarter_changes.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">
            Quartal-zu-Quartal Veränderungen
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quarter_to_quarter_changes.map((change, index) => (
              <div key={index} className="border border-neutral-200 rounded-lg p-4">
                <h4 className="font-semibold text-neutral-900 mb-3">
                  {change.from_quarter} → {change.to_quarter}
                </h4>
                
                <div className="space-y-2">
                  {/* Income Change */}
                  <div>
                    <div className="text-xs text-neutral-600">Einnahmen</div>
                    <div className="flex items-center gap-2">
                      {change.income_change_percent > 0 ? (
                        <TrendingUp className="w-3 h-3 text-green-600" />
                      ) : change.income_change_percent < 0 ? (
                        <TrendingDown className="w-3 h-3 text-red-600" />
                      ) : null}
                      <span className={`text-sm font-semibold ${
                        change.income_change_percent > 0 ? 'text-green-600' : 
                        change.income_change_percent < 0 ? 'text-red-600' : 
                        'text-neutral-600'
                      }`}>
                        {change.income_change_percent > 0 ? '+' : ''}{change.income_change_percent}%
                      </span>
                    </div>
                  </div>

                  {/* Expenses Change */}
                  <div>
                    <div className="text-xs text-neutral-600">Ausgaben</div>
                    <div className="flex items-center gap-2">
                      {change.expenses_change_percent > 0 ? (
                        <TrendingUp className="w-3 h-3 text-red-600" />
                      ) : change.expenses_change_percent < 0 ? (
                        <TrendingDown className="w-3 h-3 text-green-600" />
                      ) : null}
                      <span className={`text-sm font-semibold ${
                        change.expenses_change_percent > 0 ? 'text-red-600' : 
                        change.expenses_change_percent < 0 ? 'text-green-600' : 
                        'text-neutral-600'
                      }`}>
                        {change.expenses_change_percent > 0 ? '+' : ''}{change.expenses_change_percent}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quarterly Details */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-neutral-200">
          <h3 className="text-lg font-semibold text-neutral-900">
            Detaillierte Quartalsübersicht
          </h3>
        </div>
        
        <div className="divide-y divide-neutral-200">
          {quarters.map((quarter) => (
            <div key={quarter.quarter} className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-lg font-bold text-neutral-900">{quarter.quarter} {year}</h4>
                  <p className="text-sm text-neutral-600">
                    {new Date(quarter.start_date).toLocaleDateString('de-DE')} - {new Date(quarter.end_date).toLocaleDateString('de-DE')}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-neutral-600">Transaktionen</div>
                  <div className="text-xl font-bold text-neutral-900">
                    {quarter.transaction_count.toLocaleString('de-DE')}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-sm text-green-700 mb-1">Einnahmen</div>
                  <div className="text-xl font-bold text-green-800">
                    {formatCurrency(quarter.total_income)}
                  </div>
                </div>
                
                <div className="bg-red-50 rounded-lg p-4">
                  <div className="text-sm text-red-700 mb-1">Ausgaben</div>
                  <div className="text-xl font-bold text-red-800">
                    {formatCurrency(Math.abs(quarter.total_expenses))}
                  </div>
                </div>
                
                <div className={`rounded-lg p-4 ${
                  quarter.net_balance >= 0 ? 'bg-blue-50' : 'bg-orange-50'
                }`}>
                  <div className={`text-sm mb-1 ${
                    quarter.net_balance >= 0 ? 'text-blue-700' : 'text-orange-700'
                  }`}>
                    Netto
                  </div>
                  <div className={`text-xl font-bold ${
                    quarter.net_balance >= 0 ? 'text-blue-800' : 'text-orange-800'
                  }`}>
                    {formatCurrency(quarter.net_balance)}
                  </div>
                </div>
              </div>

              {/* Previous Year Comparison */}
              {quarter.comparison_to_previous_year && (
                <div className="bg-neutral-50 rounded-lg p-4">
                  <h5 className="font-semibold text-neutral-900 mb-3">
                    Vergleich zu {quarter.comparison_to_previous_year.previous_year}
                  </h5>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-neutral-600 mb-2">Einnahmen</div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm text-neutral-700">
                          {formatCurrency(quarter.comparison_to_previous_year.previous_income)}
                        </div>
                        <div className="text-sm">→</div>
                        <div className="text-sm font-semibold text-neutral-900">
                          {formatCurrency(quarter.total_income)}
                        </div>
                        <div className={`flex items-center gap-1 text-sm font-semibold ${
                          quarter.comparison_to_previous_year.income_change_percent > 0 ? 'text-green-600' :
                          quarter.comparison_to_previous_year.income_change_percent < 0 ? 'text-red-600' :
                          'text-neutral-600'
                        }`}>
                          {quarter.comparison_to_previous_year.income_change_percent > 0 ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : quarter.comparison_to_previous_year.income_change_percent < 0 ? (
                            <TrendingDown className="w-3 h-3" />
                          ) : null}
                          <span>
                            {quarter.comparison_to_previous_year.income_change_percent > 0 ? '+' : ''}
                            {quarter.comparison_to_previous_year.income_change_percent}%
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-neutral-600 mb-2">Ausgaben</div>
                      <div className="flex items-center gap-2">
                        <div className="text-sm text-neutral-700">
                          {formatCurrency(Math.abs(quarter.comparison_to_previous_year.previous_expenses))}
                        </div>
                        <div className="text-sm">→</div>
                        <div className="text-sm font-semibold text-neutral-900">
                          {formatCurrency(Math.abs(quarter.total_expenses))}
                        </div>
                        <div className={`flex items-center gap-1 text-sm font-semibold ${
                          quarter.comparison_to_previous_year.expenses_change_percent > 0 ? 'text-red-600' :
                          quarter.comparison_to_previous_year.expenses_change_percent < 0 ? 'text-green-600' :
                          'text-neutral-600'
                        }`}>
                          {quarter.comparison_to_previous_year.expenses_change_percent > 0 ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : quarter.comparison_to_previous_year.expenses_change_percent < 0 ? (
                            <TrendingDown className="w-3 h-3" />
                          ) : null}
                          <span>
                            {quarter.comparison_to_previous_year.expenses_change_percent > 0 ? '+' : ''}
                            {quarter.comparison_to_previous_year.expenses_change_percent}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
