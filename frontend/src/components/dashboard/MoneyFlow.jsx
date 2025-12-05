import React, { useMemo } from 'react';
import Card from '../common/Card';

/**
 * MoneyFlow - Flow Diagram showing money flow from income to expense categories
 * 
 * FEATURES:
 * - Visual representation of income flowing into expense categories
 * - Proportional flow widths based on amounts
 * - Color-coded based on category colors
 * - Interactive tooltips
 * 
 * PROPS:
 * - moneyFlowData: Object with income_categories, expense_categories, total_income, total_expenses
 * - loading: Boolean for loading state
 */
function MoneyFlow({ moneyFlowData, loading }) {
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
   * Prepare Flow Data with cumulative positions
   */
  const flowData = useMemo(() => {
    if (!moneyFlowData || !moneyFlowData.expense_categories || moneyFlowData.expense_categories.length === 0) {
      return { flows: [], maxValue: 0 };
    }

    const totalExpenses = moneyFlowData.total_expenses;
    let cumulativePosition = 0;
    
    const flows = moneyFlowData.expense_categories.map((cat) => {
      const percentage = totalExpenses > 0 ? (cat.value / totalExpenses) * 100 : 0;
      const flow = {
        ...cat,
        percentage,
        startY: cumulativePosition,
        height: percentage,
      };
      cumulativePosition += percentage;
      return flow;
    });

    return { 
      flows, 
      maxValue: totalExpenses,
      totalIncome: moneyFlowData.total_income 
    };
  }, [moneyFlowData]);

  // Loading State
  if (loading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </Card>
    );
  }

  // No Data State
  if (!moneyFlowData || 
      (!moneyFlowData.income_categories?.length && !moneyFlowData.expense_categories?.length)) {
    return (
      <Card>
        <div className="text-center py-12">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <h3 className="text-sm font-medium text-gray-900">Keine Daten verfügbar</h3>
          <p className="mt-1 text-sm text-gray-500">
            Es gibt keine Transaktionen für den ausgewählten Zeitraum.
          </p>
        </div>
      </Card>
    );
  }

  // Dynamische Höhe basierend auf Anzahl der Kategorien
  const chartHeight = Math.max(400, Math.min(700, flowData.flows.length * 60 + 200));
  const barY = 60;
  const barHeight = chartHeight - 140;

  return (
    <Card className="bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-base font-medium text-gray-700 mb-1">
              Geldfluss von Einnahmen zu Ausgaben-Kategorien
            </h4>
            <p className="text-sm text-gray-500">
              Visualisierung der Verteilung von Einnahmen auf Ausgabenkategorien
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-green-50 px-3 py-2 rounded-lg border border-green-100">
              <div className="w-3 h-3 rounded-full bg-green-500 shadow-sm"></div>
              <div className="text-xs">
                <div className="text-gray-500">Einnahmen</div>
                <div className="font-semibold text-green-700">{formatCurrency(moneyFlowData.total_income)}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-red-50 px-3 py-2 rounded-lg border border-red-100">
              <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm"></div>
              <div className="text-xs">
                <div className="text-gray-500">Ausgaben</div>
                <div className="font-semibold text-red-700">{formatCurrency(moneyFlowData.total_expenses)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SVG Flow Diagram */}
      <div className="relative w-full bg-white rounded-xl border border-gray-100 p-4" style={{ height: `${chartHeight}px` }}>
        <svg className="w-full h-full" viewBox={`0 0 1200 ${chartHeight}`} preserveAspectRatio="xMidYMid meet">
          <defs>
            {/* Gradient for each flow */}
            {flowData.flows.map((flow, idx) => (
              <linearGradient key={`gradient-${idx}`} id={`flow-gradient-${idx}`} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.6" />
                <stop offset="25%" stopColor="#10b981" stopOpacity="0.5" />
                <stop offset="75%" stopColor={flow.color} stopOpacity="0.5" />
                <stop offset="100%" stopColor={flow.color} stopOpacity="0.7" />
              </linearGradient>
            ))}
            
            {/* Drop shadow filter */}
            <filter id="dropShadow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
              <feOffset dx="0" dy="2" result="offsetblur"/>
              <feComponentTransfer>
                <feFuncA type="linear" slope="0.2"/>
              </feComponentTransfer>
              <feMerge>
                <feMergeNode/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Income source (left side) */}
          <g filter="url(#dropShadow)">
            {/* Income bar background */}
            <rect
              x="40"
              y={barY}
              width="120"
              height={barHeight}
              fill="#f0fdf4"
              stroke="#10b981"
              strokeWidth="2"
              rx="10"
              opacity="0.3"
            />
            
            {/* Income categories breakdown */}
            {moneyFlowData.income_categories?.map((cat, idx) => {
              const totalIncome = moneyFlowData.total_income;
              const percentage = totalIncome > 0 ? (cat.value / totalIncome) * 100 : 0;
              const startY = barY + (idx > 0 ? moneyFlowData.income_categories.slice(0, idx).reduce((sum, c) => sum + (c.value / totalIncome) * barHeight, 0) : 0);
              const height = (percentage / 100) * barHeight;
              
              return (
                <g key={idx} className="group">
                  <rect
                    x="40"
                    y={startY}
                    width="120"
                    height={height}
                    fill={cat.color}
                    opacity="0.85"
                    className="transition-all duration-300 group-hover:opacity-100"
                  />
                  {/* Label */}
                  {height > 40 && (
                    <>
                      <text
                        x="100"
                        y={startY + height / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize="28"
                        fontWeight="bold"
                        className="drop-shadow-sm"
                      >
                        {cat.icon}
                      </text>
                      {height > 70 && (
                        <text
                          x="100"
                          y={startY + height / 2 + 30}
                          textAnchor="middle"
                          fill="white"
                          fontSize="12"
                          fontWeight="600"
                          className="drop-shadow-sm"
                        >
                          {(percentage).toFixed(0)}%
                        </text>
                      )}
                    </>
                  )}
                </g>
              );
            })}

            {/* Income bar border */}
            <rect
              x="40"
              y={barY}
              width="120"
              height={barHeight}
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              rx="10"
            />

            {/* Income label */}
            <text x="100" y={barY - 20} textAnchor="middle" fill="#059669" fontWeight="bold" fontSize="18">
              💰 Einnahmen
            </text>
            <text x="100" y={barY + barHeight + 30} textAnchor="middle" fill="#059669" fontWeight="bold" fontSize="16">
              {formatCurrency(moneyFlowData.total_income)}
            </text>
          </g>

          {/* Flow streams */}
          {flowData.flows.map((flow, idx) => {
            const startY = barY;
            const startHeight = barHeight;
            const endY = barY + (flow.startY / 100) * barHeight;
            const endHeight = (flow.height / 100) * barHeight;
            
            // Create curved path for flow
            const path = `
              M 160 ${startY + (startHeight * flow.startY / 100)}
              C 400 ${startY + (startHeight * flow.startY / 100)},
                800 ${endY},
                1040 ${endY}
              L 1040 ${endY + endHeight}
              C 800 ${endY + endHeight},
                400 ${startY + (startHeight * (flow.startY + flow.height) / 100)},
                160 ${startY + (startHeight * (flow.startY + flow.height) / 100)}
              Z
            `;

            return (
              <g key={idx} className="group">
                <path
                  d={path}
                  fill={`url(#flow-gradient-${idx})`}
                  opacity="0.6"
                  className="transition-all duration-300 group-hover:opacity-0.9 cursor-pointer"
                  style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
                />
                
                {/* Flow label in the middle */}
                {flow.height > 5 && (
                  <g className="pointer-events-none">
                    {/* Background for better readability */}
                    {flow.height > 8 && (
                      <rect
                        x="520"
                        y={endY + endHeight / 2 - 24}
                        width="160"
                        height="48"
                        fill="white"
                        opacity="0.95"
                        rx="8"
                        filter="url(#dropShadow)"
                      />
                    )}
                    <text
                      x="600"
                      y={endY + endHeight / 2 - 6}
                      textAnchor="middle"
                      fill="#1f2937"
                      fontSize="15"
                      fontWeight="700"
                    >
                      {flow.icon} {flow.name.length > 15 ? flow.name.substring(0, 15) + '...' : flow.name}
                    </text>
                    <text
                      x="600"
                      y={endY + endHeight / 2 + 14}
                      textAnchor="middle"
                      fill="#4b5563"
                      fontSize="13"
                      fontWeight="600"
                    >
                      {formatCurrency(flow.value)} • {flow.percentage.toFixed(1)}%
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          {/* Expense categories (right side) */}
          <g filter="url(#dropShadow)">
            {/* Expense bar background */}
            <rect
              x="1040"
              y={barY}
              width="120"
              height={barHeight}
              fill="#fef2f2"
              stroke="#ef4444"
              strokeWidth="2"
              rx="10"
              opacity="0.3"
            />

            {/* Individual expense categories */}
            {flowData.flows.map((flow, idx) => {
              const y = barY + (flow.startY / 100) * barHeight;
              const height = (flow.height / 100) * barHeight;
              
              return (
                <g key={idx} className="group">
                  <rect
                    x="1040"
                    y={y}
                    width="120"
                    height={height}
                    fill={flow.color}
                    opacity="0.85"
                    className="transition-all duration-300 group-hover:opacity-100"
                  />
                  {/* Category icon */}
                  {height > 40 && (
                    <>
                      <text
                        x="1100"
                        y={y + height / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize="28"
                        fontWeight="bold"
                        className="drop-shadow-sm"
                      >
                        {flow.icon}
                      </text>
                      {height > 70 && (
                        <text
                          x="1100"
                          y={y + height / 2 + 30}
                          textAnchor="middle"
                          fill="white"
                          fontSize="12"
                          fontWeight="600"
                          className="drop-shadow-sm"
                        >
                          {flow.percentage.toFixed(0)}%
                        </text>
                      )}
                    </>
                  )}
                </g>
              );
            })}

            {/* Expense bar border */}
            <rect
              x="1040"
              y={barY}
              width="120"
              height={barHeight}
              fill="none"
              stroke="#ef4444"
              strokeWidth="2"
              rx="10"
            />

            {/* Expense label */}
            <text x="1100" y={barY - 20} textAnchor="middle" fill="#dc2626" fontWeight="bold" fontSize="18">
              💸 Ausgaben
            </text>
            <text x="1100" y={barY + barHeight + 30} textAnchor="middle" fill="#dc2626" fontWeight="bold" fontSize="16">
              {formatCurrency(moneyFlowData.total_expenses)}
            </text>
          </g>
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h5 className="text-sm font-semibold text-gray-700 mb-3">Ausgabenkategorien</h5>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {moneyFlowData.expense_categories?.map((cat, idx) => (
            <div 
              key={idx} 
              className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg border border-gray-100 hover:border-gray-300 hover:shadow-sm transition-all duration-200"
            >
              <div 
                className="w-4 h-4 rounded shadow-sm flex-shrink-0"
                style={{ backgroundColor: cat.color }}
              />
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-gray-700 truncate">
                  {cat.icon} {cat.name}
                </div>
                <div className="text-xs text-gray-500">
                  {formatCurrency(cat.value)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

export default MoneyFlow;
