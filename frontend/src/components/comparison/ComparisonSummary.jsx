import React from 'react';

/**
 * Comparison Summary Cards
 * Display high-level metrics with differences
 */
export default function ComparisonSummary({ data }) {
  const { period1, period2, comparison } = data;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(value);
  };

  const formatPercent = (value) => {
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  const getChangeColor = (value, isExpense = false) => {
    // For expenses, negative change is good (less expenses)
    // For income, positive change is good (more income)
    const isPositive = isExpense ? value < 0 : value > 0;
    return isPositive ? 'text-green-600' : 'text-red-600';
  };

  const summaryCards = [
    {
      title: 'Einnahmen',
      value1: period1.total_income,
      value2: period2.total_income,
      diff: comparison.income_diff,
      diffPercent: comparison.income_diff_percent,
      icon: '💰',
      isExpense: false,
    },
    {
      title: 'Ausgaben',
      value1: Math.abs(period1.total_expenses),
      value2: Math.abs(period2.total_expenses),
      diff: Math.abs(comparison.expenses_diff),
      diffPercent: comparison.expenses_diff_percent,
      icon: '💸',
      isExpense: true,
    },
    {
      title: 'Netto-Bilanz',
      value1: period1.net_balance,
      value2: period2.net_balance,
      diff: comparison.balance_diff,
      diffPercent: comparison.balance_diff_percent,
      icon: '📊',
      isExpense: false,
    },
    {
      title: 'Transaktionen',
      value1: period1.transaction_count,
      value2: period2.transaction_count,
      diff: comparison.transaction_count_diff,
      diffPercent: null,
      icon: '🔢',
      isExpense: false,
      isCount: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {summaryCards.map((card, idx) => (
        <div key={idx} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-neutral-600">{card.title}</h3>
            <span className="text-2xl">{card.icon}</span>
          </div>

          <div className="space-y-3">
            {/* Period 1 */}
            <div>
              <p className="text-xs text-neutral-500">{period1.period_label}</p>
              <p className="text-lg font-semibold text-neutral-900">
                {card.isCount ? card.value1 : formatCurrency(card.value1)}
              </p>
            </div>

            {/* Period 2 */}
            <div>
              <p className="text-xs text-neutral-500">{period2.period_label}</p>
              <p className="text-lg font-semibold text-neutral-900">
                {card.isCount ? card.value2 : formatCurrency(card.value2)}
              </p>
            </div>

            {/* Difference */}
            <div className="pt-3 border-t border-neutral-200">
              <div className="flex items-center justify-between">
                <span className="text-xs text-neutral-500">Veränderung:</span>
                <div className="text-right">
                  <p className={`text-sm font-semibold ${getChangeColor(card.diff, card.isExpense)}`}>
                    {card.diff > 0 ? '+' : ''}
                    {card.isCount ? card.diff : formatCurrency(card.diff)}
                  </p>
                  {card.diffPercent !== null && (
                    <p className={`text-xs ${getChangeColor(card.diffPercent, card.isExpense)}`}>
                      {formatPercent(card.diffPercent)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
