import React, { useMemo } from 'react';

/**
 * Category Heatmap - Visual comparison of category changes
 */
export default function CategoryHeatmap({ data }) {
  const { period1, period2 } = data;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(value);
  };

  const formatPercent = (value) => {
    if (!isFinite(value)) return 'N/A';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  // Prepare heatmap data
  const heatmapData = useMemo(() => {
    const categoryMap = new Map();

    // Collect all categories
    [...period1.categories, ...period2.categories].forEach((cat) => {
      if (!categoryMap.has(cat.category_name)) {
        categoryMap.set(cat.category_name, {
          name: cat.category_name,
          icon: cat.icon,
          color: cat.color,
          amount1: 0,
          amount2: 0,
        });
      }
    });

    // Fill in amounts
    period1.categories.forEach((cat) => {
      const entry = categoryMap.get(cat.category_name);
      entry.amount1 = cat.total_amount;
    });

    period2.categories.forEach((cat) => {
      const entry = categoryMap.get(cat.category_name);
      entry.amount2 = cat.total_amount;
    });

    // Calculate changes and sort
    return Array.from(categoryMap.values())
      .map((cat) => {
        const diff = cat.amount2 - cat.amount1;
        const percentChange =
          cat.amount1 !== 0
            ? ((cat.amount2 - cat.amount1) / Math.abs(cat.amount1)) * 100
            : cat.amount2 !== 0
            ? 100
            : 0;

        return {
          ...cat,
          diff,
          percentChange,
          absTotal: Math.abs(cat.amount1) + Math.abs(cat.amount2),
        };
      })
      .sort((a, b) => b.absTotal - a.absTotal);
  }, [period1, period2]);

  const getHeatColor = (percentChange) => {
    if (!isFinite(percentChange)) return 'bg-gray-100';
    
    const absChange = Math.abs(percentChange);
    
    if (percentChange > 0) {
      // Red for increases (more expenses)
      if (absChange > 50) return 'bg-red-600';
      if (absChange > 30) return 'bg-red-500';
      if (absChange > 15) return 'bg-red-400';
      if (absChange > 5) return 'bg-red-300';
      return 'bg-red-200';
    } else if (percentChange < 0) {
      // Green for decreases (less expenses)
      if (absChange > 50) return 'bg-green-600';
      if (absChange > 30) return 'bg-green-500';
      if (absChange > 15) return 'bg-green-400';
      if (absChange > 5) return 'bg-green-300';
      return 'bg-green-200';
    }
    return 'bg-gray-100';
  };

  const getTextColor = (percentChange) => {
    if (!isFinite(percentChange)) return 'text-gray-600';
    const absChange = Math.abs(percentChange);
    return absChange > 25 ? 'text-white' : 'text-gray-900';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Kategorien Heatmap - Prozentuale Veränderung
      </h2>
      <p className="text-sm text-gray-600 mb-4">
        Rot = Zunahme der Ausgaben | Grün = Abnahme der Ausgaben
      </p>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                Kategorie
              </th>
              <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                {period1.period_label}
              </th>
              <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                {period2.period_label}
              </th>
              <th className="text-center py-3 px-4 text-sm font-medium text-gray-700">
                Veränderung
              </th>
            </tr>
          </thead>
          <tbody>
            {heatmapData.map((cat, idx) => (
              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{cat.icon}</span>
                    <span className="font-medium text-gray-900">{cat.name}</span>
                  </div>
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-700">
                  {formatCurrency(cat.amount1)}
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-700">
                  {formatCurrency(cat.amount2)}
                </td>
                <td className="py-3 px-4">
                  <div className={`rounded-md p-2 text-center ${getHeatColor(cat.percentChange)}`}>
                    <div className={`text-sm font-semibold ${getTextColor(cat.percentChange)}`}>
                      {formatPercent(cat.percentChange)}
                    </div>
                    <div className={`text-xs ${getTextColor(cat.percentChange)}`}>
                      {cat.diff > 0 ? '+' : ''}
                      {formatCurrency(cat.diff)}
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
