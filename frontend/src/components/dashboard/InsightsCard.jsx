import React from 'react';
import PropTypes from 'prop-types';
import { useDashboardInsights } from '../../hooks';
import insightsService from '../../services/insightsService';

/**
 * InsightsCard Component
 * 
 * Displays personalized spending insights with dismiss functionality.
 * Automatically fetches and generates insights on mount.
 * 
 * Features:
 * - Automatic insight generation
 * - Severity-based color coding
 * - Dismiss functionality
 * - Responsive design
 * - Loading and error states
 * 
 * @param {Object} props
 * @param {number} props.accountId - Account ID (null = global insights)
 * @param {number} props.limit - Maximum number of insights to display
 * @param {boolean} props.showDismissed - Show dismissed insights
 * @param {string} props.className - Additional CSS classes
 */
export default function InsightsCard({ 
  accountId = null, 
  limit = 5, 
  showDismissed = false,
  className = '' 
}) {
  const {
    insights,
    loading,
    error,
    generating,
    hasInsights,
    dismissInsight,
    generateInsights,
    refreshInsights
  } = useDashboardInsights(accountId);

  // Filter insights based on showDismissed prop
  const displayedInsights = showDismissed 
    ? insights 
    : insights.filter(i => !i.is_dismissed);

  // Limit displayed insights
  const limitedInsights = displayedInsights.slice(0, limit);

  /**
   * Handle dismiss click
   */
  const handleDismiss = async (insightId) => {
    const result = await dismissInsight(insightId);
    if (result.success) {
      console.log('Insight dismissed successfully');
    }
  };

  /**
   * Handle manual generation
   */
  const handleGenerate = async () => {
    const result = await generateInsights({ forceRegenerate: true });
    if (result.success) {
      console.log(`Generated ${result.insights_generated} new insights`);
    }
  };

  /**
   * Render loading state
   */
  if (loading && !hasInsights) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">💡 Spending Insights</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Lade Insights...</span>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error && !hasInsights) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">💡 Spending Insights</h3>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">
            ⚠️ Fehler beim Laden: {error}
          </p>
          <button
            onClick={refreshInsights}
            className="mt-2 text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  /**
   * Render empty state
   */
  if (!hasInsights && !generating) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">💡 Spending Insights</h3>
        </div>
        <div className="text-center py-8">
          <div className="text-4xl mb-3">🔍</div>
          <p className="text-gray-600 mb-4">
            Noch keine Insights verfügbar. Generiere personalisierte Einblicke in deine Ausgaben!
          </p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {generating ? 'Generiere...' : 'Insights generieren'}
          </button>
        </div>
      </div>
    );
  }

  /**
   * Render insights list
   */
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-gray-900">💡 Spending Insights</h3>
          {limitedInsights.length > 0 && (
            <span className="px-2 py-1 bg-primary-100 text-primary-700 text-xs font-medium rounded-full">
              {limitedInsights.length}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Refresh Button */}
          <button
            onClick={refreshInsights}
            disabled={loading}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
            title="Aktualisieren"
          >
            <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          
          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-3 py-1.5 text-sm bg-primary-50 text-primary-600 hover:bg-primary-100 rounded-lg transition-colors disabled:opacity-50"
            title="Neue Insights generieren"
          >
            {generating ? 'Generiere...' : 'Neu generieren'}
          </button>
        </div>
      </div>

      {/* Insights List */}
      <div className="divide-y divide-gray-100">
        {limitedInsights.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>Keine aktiven Insights vorhanden.</p>
          </div>
        ) : (
          limitedInsights.map((insight) => {
            const colors = insightsService.getSeverityColors(insight.severity);
            
            return (
              <div
                key={insight.id}
                className={`p-4 ${colors.bg} border-l-4 ${colors.border} transition-all hover:shadow-sm`}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Icon */}
                  <div className="text-2xl flex-shrink-0">
                    {colors.icon}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h4 className={`font-semibold ${colors.text} text-sm`}>
                        {insight.title}
                      </h4>
                      
                      {/* Priority Badge */}
                      {insight.priority >= 7 && (
                        <span className={`px-2 py-0.5 ${colors.badgeBg} ${colors.badgeText} text-xs font-medium rounded`}>
                          Wichtig
                        </span>
                      )}
                    </div>
                    
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {insight.description}
                    </p>
                    
                    {/* Metadata */}
                    {insight.metadata && (
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-600">
                        {insight.metadata.current_amount && (
                          <span className="px-2 py-1 bg-white bg-opacity-60 rounded">
                            Aktuell: {Number(insight.metadata.current_amount).toFixed(2)} €
                          </span>
                        )}
                        {insight.metadata.change_percent && (
                          <span className="px-2 py-1 bg-white bg-opacity-60 rounded">
                            {insight.metadata.change_percent > 0 ? '+' : ''}
                            {Number(insight.metadata.change_percent).toFixed(1)}%
                          </span>
                        )}
                        {insight.metadata.category_name && (
                          <span className="px-2 py-1 bg-white bg-opacity-60 rounded">
                            📂 {insight.metadata.category_name}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Dismiss Button */}
                  {!insight.is_dismissed && (
                    <button
                      onClick={() => handleDismiss(insight.id)}
                      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-white hover:bg-opacity-50 rounded transition-colors flex-shrink-0"
                      title="Ausblenden"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer - Show More Link */}
      {displayedInsights.length > limit && (
        <div className="p-4 bg-gray-50 border-t border-gray-200 text-center">
          <button
            onClick={refreshInsights}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            {displayedInsights.length - limit} weitere Insights anzeigen
          </button>
        </div>
      )}
    </div>
  );
}

InsightsCard.propTypes = {
  accountId: PropTypes.number,
  limit: PropTypes.number,
  showDismissed: PropTypes.bool,
  className: PropTypes.string
};
