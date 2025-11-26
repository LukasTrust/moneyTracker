import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

/**
 * Comparison Charts - Side-by-side bar charts
 */
export default function ComparisonCharts({ data }) {
  const { period1, period2 } = data;

  console.log('ComparisonCharts - period1:', period1);
  console.log('ComparisonCharts - period2:', period2);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Prepare data for income/expenses comparison
  const summaryData = [
    {
      name: period1.period_label,
      Einnahmen: period1.total_income,
      Ausgaben: Math.abs(period1.total_expenses),
    },
    {
      name: period2.period_label,
      Einnahmen: period2.total_income,
      Ausgaben: Math.abs(period2.total_expenses),
    },
  ];

  // Prepare category comparison data (top 10 by total absolute amount)
  const categoryMap = new Map();

  // Collect all categories from both periods
  [...period1.categories, ...period2.categories].forEach((cat) => {
    if (!categoryMap.has(cat.category_name)) {
      categoryMap.set(cat.category_name, {
        name: cat.category_name,
        color: cat.color,
        period1: 0,
        period2: 0,
      });
    }
  });

  // Fill in amounts
  period1.categories.forEach((cat) => {
    const entry = categoryMap.get(cat.category_name);
    entry.period1 = Math.abs(cat.total_amount);
  });

  period2.categories.forEach((cat) => {
    const entry = categoryMap.get(cat.category_name);
    entry.period2 = Math.abs(cat.total_amount);
  });

  // Convert to array and sort by total (sum of both periods)
  const categoryData = Array.from(categoryMap.values())
    .map((cat) => ({
      ...cat,
      total: cat.period1 + cat.period2,
    }))
    .filter((cat) => cat.total > 0) // Filter out categories with no data
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);

  console.log('Category data for chart:', categoryData);

  return (
    <div className="space-y-6">
      {/* Income vs Expenses */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">
          Einnahmen vs. Ausgaben
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={summaryData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Bar dataKey="Einnahmen" fill="#10b981" />
            <Bar dataKey="Ausgaben" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Category Comparison */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">
          Top 10 Kategorien im Vergleich
        </h2>
        {categoryData.length > 0 ? (
          <ResponsiveContainer width="100%" height={Math.max(categoryData.length * 60, 300)}>
            <BarChart data={categoryData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={(value) => formatCurrency(value)} />
              <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="period1" name={period1.period_label} fill="#3b82f6" />
              <Bar dataKey="period2" name={period2.period_label} fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-neutral-500">
            Keine Kategorie-Daten verfügbar
          </div>
        )}
      </div>
    </div>
  );
}
