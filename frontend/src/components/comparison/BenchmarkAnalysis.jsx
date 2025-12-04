import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * Benchmark Analysis Component
 * Shows how current spending compares to historical averages
 */
export default function BenchmarkAnalysis({ data }) {
  if (!data) return null;

  const { current, benchmark, categories } = data;

  // Get status icon and color
  const getStatusDisplay = (status, diffPercent) => {
    if (status === 'above') {
      return {
        icon: <TrendingUp className="w-5 h-5" />,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        label: 'Über Durchschnitt'
      };
    } else if (status === 'below') {
      return {
        icon: <TrendingDown className="w-5 h-5" />,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        label: 'Unter Durchschnitt'
      };
    } else {
      return {
        icon: <Minus className="w-5 h-5" />,
        color: 'text-neutral-600',
        bgColor: 'bg-neutral-50',
        label: 'Im Durchschnitt'
      };
    }
  };

  const overallStatus = getStatusDisplay(benchmark.status, benchmark.difference_percent);

  return (
    <div className="space-y-6">
      {/* Overall Benchmark Summary */}
      <div className={`${overallStatus.bgColor} rounded-lg p-6 border border-opacity-20`}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              Gesamtausgaben im Vergleich zum Durchschnitt
            </h3>
            <p className="text-sm text-neutral-600 mb-4">
              Basierend auf {benchmark.num_periods_analyzed} historischen Perioden
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-neutral-600">Aktuelle Ausgaben</div>
                <div className="text-2xl font-bold text-neutral-900">
                  {new Intl.NumberFormat('de-DE', {
                    style: 'currency',
                    currency: 'EUR'
                  }).format(current.total_expenses)}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-neutral-600">Durchschnitt</div>
                <div className="text-2xl font-bold text-neutral-900">
                  {new Intl.NumberFormat('de-DE', {
                    style: 'currency',
                    currency: 'EUR'
                  }).format(benchmark.average_expenses)}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-neutral-600">Differenz</div>
                <div className={`text-2xl font-bold flex items-center gap-2 ${overallStatus.color}`}>
                  {overallStatus.icon}
                  <span>
                    {benchmark.difference > 0 ? '+' : ''}
                    {new Intl.NumberFormat('de-DE', {
                      style: 'currency',
                      currency: 'EUR'
                    }).format(benchmark.difference)}
                  </span>
                </div>
                <div className={`text-sm ${overallStatus.color} mt-1`}>
                  {benchmark.difference_percent > 0 ? '+' : ''}
                  {benchmark.difference_percent}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-neutral-200">
          <h3 className="text-lg font-semibold text-neutral-900">
            Kategorien-Benchmark
          </h3>
          <p className="text-sm text-neutral-600 mt-1">
            Vergleich deiner Ausgaben mit deinem historischen Durchschnitt
          </p>
        </div>

        <div className="divide-y divide-neutral-200">
          {categories && categories.length > 0 ? (
            categories.map((category) => {
              const catStatus = getStatusDisplay(category.status, category.difference_percent);
              
              return (
                <div key={category.category_id} className="p-4 hover:bg-neutral-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-neutral-900">
                        {category.category_name}
                      </div>
                      <div className="text-sm text-neutral-600 mt-1">
                        Aktuell: {new Intl.NumberFormat('de-DE', {
                          style: 'currency',
                          currency: 'EUR'
                        }).format(category.current_expenses)} | 
                        Durchschnitt: {new Intl.NumberFormat('de-DE', {
                          style: 'currency',
                          currency: 'EUR'
                        }).format(category.average_expenses)}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 ml-4">
                      <div className="text-right">
                        <div className={`font-semibold ${catStatus.color} flex items-center gap-1 justify-end`}>
                          {catStatus.icon}
                          <span>
                            {category.difference > 0 ? '+' : ''}
                            {new Intl.NumberFormat('de-DE', {
                              style: 'currency',
                              currency: 'EUR'
                            }).format(category.difference)}
                          </span>
                        </div>
                        <div className={`text-sm ${catStatus.color}`}>
                          {category.difference_percent > 0 ? '+' : ''}
                          {category.difference_percent}%
                        </div>
                      </div>
                      
                      {/* Visual indicator */}
                      <div className="w-24 h-2 bg-neutral-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${category.status === 'above' ? 'bg-red-500' : 'bg-green-500'}`}
                          style={{
                            width: `${Math.min(Math.abs(category.difference_percent), 100)}%`
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-neutral-500">
              Keine Kategoriedaten verfügbar
            </div>
          )}
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">💡 Insights</h4>
        <ul className="space-y-2 text-sm text-blue-800">
          {benchmark.status === 'above' && (
            <li>
              Deine Ausgaben liegen {Math.abs(benchmark.difference_percent)}% über deinem historischen Durchschnitt. 
              Prüfe die Kategorien mit den größten Abweichungen.
            </li>
          )}
          {benchmark.status === 'below' && (
            <li>
              Gut gemacht! Deine Ausgaben liegen {Math.abs(benchmark.difference_percent)}% unter deinem historischen Durchschnitt.
            </li>
          )}
          {categories && categories.length > 0 && (
            <>
              {categories[0].status === 'above' && (
                <li>
                  Die größte Abweichung nach oben ist in der Kategorie "{categories[0].category_name}" 
                  mit {categories[0].difference_percent}% über dem Durchschnitt.
                </li>
              )}
            </>
          )}
        </ul>
      </div>
    </div>
  );
}
