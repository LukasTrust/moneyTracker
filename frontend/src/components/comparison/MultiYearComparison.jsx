import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

/**
 * Multi-Year Comparison Component
 * Compare multiple years with trend analysis
 */
export default function MultiYearComparison({ data }) {
  if (!data) return null;

  const { years, trends, summary } = data;

  // Prepare chart data
  const chartData = years.map(year => ({
    year: year.year.toString(),
    Einnahmen: year.total_income,
    Ausgaben: Math.abs(year.total_expenses),
    Netto: year.net_balance,
    Transaktionen: year.transaction_count
  }));

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90 mb-2">Durchschnittliche Einnahmen</div>
          <div className="text-3xl font-bold">{formatCurrency(summary.average_income)}</div>
          <div className="text-sm opacity-75 mt-2">
            über {summary.years_compared} Jahre
          </div>
        </div>

        <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90 mb-2">Durchschnittliche Ausgaben</div>
          <div className="text-3xl font-bold">{formatCurrency(summary.average_expenses)}</div>
          <div className="text-sm opacity-75 mt-2">
            über {summary.years_compared} Jahre
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90 mb-2">Durchschnittlicher Nettosaldo</div>
          <div className="text-3xl font-bold">{formatCurrency(summary.average_net)}</div>
          <div className="text-sm opacity-75 mt-2">
            über {summary.years_compared} Jahre
          </div>
        </div>
      </div>

      {/* Year-over-Year Changes */}
      {trends && trends.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">
            Jahr-zu-Jahr Veränderungen
          </h3>
          <div className="space-y-4">
            {trends.map((trend, index) => (
              <div key={index} className="border border-neutral-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-neutral-900">
                    {trend.from_year} → {trend.to_year}
                  </h4>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Income Change */}
                  <div>
                    <div className="text-sm text-neutral-600 mb-1">Einnahmen</div>
                    <div className="flex items-center gap-2">
                      {trend.income_change_percent > 0 ? (
                        <TrendingUp className="w-4 h-4 text-green-600" />
                      ) : trend.income_change_percent < 0 ? (
                        <TrendingDown className="w-4 h-4 text-red-600" />
                      ) : null}
                      <span className={`font-semibold ${
                        trend.income_change_percent > 0 ? 'text-green-600' : 
                        trend.income_change_percent < 0 ? 'text-red-600' : 
                        'text-neutral-600'
                      }`}>
                        {trend.income_change > 0 ? '+' : ''}{formatCurrency(trend.income_change)}
                      </span>
                      <span className="text-sm text-neutral-600">
                        ({trend.income_change_percent > 0 ? '+' : ''}{trend.income_change_percent}%)
                      </span>
                    </div>
                  </div>

                  {/* Expenses Change */}
                  <div>
                    <div className="text-sm text-neutral-600 mb-1">Ausgaben</div>
                    <div className="flex items-center gap-2">
                      {trend.expenses_change_percent > 0 ? (
                        <TrendingUp className="w-4 h-4 text-red-600" />
                      ) : trend.expenses_change_percent < 0 ? (
                        <TrendingDown className="w-4 h-4 text-green-600" />
                      ) : null}
                      <span className={`font-semibold ${
                        trend.expenses_change_percent > 0 ? 'text-red-600' : 
                        trend.expenses_change_percent < 0 ? 'text-green-600' : 
                        'text-neutral-600'
                      }`}>
                        {trend.expenses_change > 0 ? '+' : ''}{formatCurrency(Math.abs(trend.expenses_change))}
                      </span>
                      <span className="text-sm text-neutral-600">
                        ({trend.expenses_change_percent > 0 ? '+' : ''}{trend.expenses_change_percent}%)
                      </span>
                    </div>
                  </div>

                  {/* Balance Change */}
                  <div>
                    <div className="text-sm text-neutral-600 mb-1">Saldo</div>
                    <div className="flex items-center gap-2">
                      {trend.balance_change_percent > 0 ? (
                        <TrendingUp className="w-4 h-4 text-green-600" />
                      ) : trend.balance_change_percent < 0 ? (
                        <TrendingDown className="w-4 h-4 text-red-600" />
                      ) : null}
                      <span className={`font-semibold ${
                        trend.balance_change_percent > 0 ? 'text-green-600' : 
                        trend.balance_change_percent < 0 ? 'text-red-600' : 
                        'text-neutral-600'
                      }`}>
                        {trend.balance_change > 0 ? '+' : ''}{formatCurrency(trend.balance_change)}
                      </span>
                      <span className="text-sm text-neutral-600">
                        ({trend.balance_change_percent > 0 ? '+' : ''}{trend.balance_change_percent}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bar Chart - Income vs Expenses */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
          Einnahmen vs. Ausgaben im Jahresvergleich
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis tickFormatter={formatCurrency} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Bar dataKey="Einnahmen" fill="#10b981" />
            <Bar dataKey="Ausgaben" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Line Chart - Net Balance Trend */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
          Nettosaldo-Trend
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis tickFormatter={formatCurrency} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="Netto" 
              stroke="#3b82f6" 
              strokeWidth={3}
              dot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Yearly Details Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-neutral-200">
          <h3 className="text-lg font-semibold text-neutral-900">
            Jahresübersicht
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-neutral-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Jahr
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Einnahmen
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Ausgaben
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Netto
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Transaktionen
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200">
              {years.map((year) => (
                <tr key={year.year} className="hover:bg-neutral-50">
                  <td className="px-6 py-4 whitespace-nowrap font-semibold text-neutral-900">
                    {year.year}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-green-600 font-medium">
                    {formatCurrency(year.total_income)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-red-600 font-medium">
                    {formatCurrency(Math.abs(year.total_expenses))}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-right font-semibold ${
                    year.net_balance >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(year.net_balance)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-neutral-600">
                    {year.transaction_count.toLocaleString('de-DE')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
