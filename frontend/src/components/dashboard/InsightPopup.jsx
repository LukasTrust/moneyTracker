import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import insightsService from '../../services/insightsService';

/**
 * InsightPopup Component
 * 
 * Auto-displaying modal/toast popup for insights.
 * 
 * Features:
 * - Auto-fetches displayable insights on mount
 * - Respects cooldown periods
 * - Marks insights as shown when displayed
 * - Smooth animations
 * - Dismiss functionality
 * - Can show multiple insights sequentially
 * 
 * @param {Object} props
 * @param {number} props.accountId - Account ID (null = global insights)
 * @param {number} props.maxInsights - Max number of insights to show per session (default: 1)
 * @param {number} props.delayMs - Delay before showing first insight (default: 2000ms)
 * @param {boolean} props.autoShow - Auto-show on mount (default: true)
 * @param {Function} props.onInsightShown - Callback when insight is shown
 * @param {Function} props.onInsightDismissed - Callback when insight is dismissed
 */
export default function InsightPopup({
  accountId = null,
  maxInsights = 1,
  delayMs = 2000,
  autoShow = true,
  onInsightShown = null,
  onInsightDismissed = null
}) {
  const [insights, setInsights] = useState([]);
  const [currentInsight, setCurrentInsight] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  /**
   * Fetch displayable insights
   */
  const fetchDisplayableInsights = async () => {
    setLoading(true);
    
    try {
      const displayableInsights = await insightsService.getDisplayableInsights({
        accountId,
        maxCount: maxInsights
      });
      
      setInsights(displayableInsights);
      
      // Auto-show first insight if available
      if (displayableInsights.length > 0 && autoShow) {
        setTimeout(() => {
          showNextInsight(displayableInsights, 0);
        }, delayMs);
      }
    } catch (error) {
      console.error('Error fetching displayable insights:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Show next insight in queue
   */
  const showNextInsight = async (insightsList, index) => {
    if (index >= insightsList.length) {
      return; // No more insights to show
    }
    
    const insight = insightsList[index];
    setCurrentInsight(insight);
    setCurrentIndex(index);
    setShowPopup(true);
    
    // Mark as shown on backend
    try {
      await insightsService.markInsightShown(insight.id);
      
      if (onInsightShown) {
        onInsightShown(insight);
      }
    } catch (error) {
      console.error('Error marking insight as shown:', error);
    }
  };

  /**
   * Handle dismiss
   */
  const handleDismiss = async () => {
    if (!currentInsight) return;
    
    try {
      await insightsService.dismissInsight(currentInsight.id);
      
      if (onInsightDismissed) {
        onInsightDismissed(currentInsight);
      }
    } catch (error) {
      console.error('Error dismissing insight:', error);
    }
    
    // Close popup with animation
    setShowPopup(false);
    
    // Show next insight after delay
    setTimeout(() => {
      setCurrentInsight(null);
      
      if (currentIndex + 1 < insights.length) {
        setTimeout(() => {
          showNextInsight(insights, currentIndex + 1);
        }, 1000);
      }
    }, 300);
  };

  /**
   * Handle close without dismiss (just hide for this session)
   */
  const handleClose = () => {
    setShowPopup(false);
    
    setTimeout(() => {
      setCurrentInsight(null);
      
      // Show next insight after delay
      if (currentIndex + 1 < insights.length) {
        setTimeout(() => {
          showNextInsight(insights, currentIndex + 1);
        }, 1000);
      }
    }, 300);
  };

  /**
   * Auto-fetch on mount
   */
  useEffect(() => {
    if (autoShow) {
      fetchDisplayableInsights();
    }
  }, [accountId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!currentInsight || !showPopup) {
    return null;
  }

  const colors = insightsService.getSeverityColors(currentInsight.severity);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black bg-opacity-50 z-50 transition-opacity duration-300 ${
          showPopup ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleClose}
      />

      {/* Popup Modal */}
      <div
        className={`fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md transition-all duration-300 ${
          showPopup ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none'
        }`}
      >
        <div className={`bg-white rounded-xl shadow-2xl border-l-4 ${colors.border} overflow-hidden`}>
          {/* Header */}
          <div className={`${colors.bg} px-6 py-4 border-b ${colors.border}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{colors.icon}</span>
                <div>
                  <h3 className={`font-semibold ${colors.text} text-lg`}>
                    💡 Spending Insight
                  </h3>
                  {currentInsight.priority >= 7 && (
                    <span className={`text-xs ${colors.badgeText} font-medium`}>
                      Wichtig
                    </span>
                  )}
                </div>
              </div>
              
              <button
                onClick={handleClose}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Schließen"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-5">
            <h4 className={`font-bold ${colors.text} text-xl mb-3`}>
              {currentInsight.title}
            </h4>
            
            <p className="text-gray-700 leading-relaxed mb-4">
              {currentInsight.description}
            </p>

            {/* Metadata */}
            {currentInsight.insight_data && (
              <div className="flex flex-wrap gap-2 mb-4">
                {currentInsight.insight_data.current_amount && (
                  <span className={`px-3 py-1 ${colors.badgeBg} ${colors.badgeText} text-sm rounded-full`}>
                    Aktuell: {Number(currentInsight.insight_data.current_amount).toFixed(2)} €
                  </span>
                )}
                {currentInsight.insight_data.change_percent && (
                  <span className={`px-3 py-1 ${colors.badgeBg} ${colors.badgeText} text-sm rounded-full`}>
                    {currentInsight.insight_data.change_percent > 0 ? '+' : ''}
                    {Number(currentInsight.insight_data.change_percent).toFixed(1)}%
                  </span>
                )}
                {currentInsight.insight_data.category_name && (
                  <span className={`px-3 py-1 ${colors.badgeBg} ${colors.badgeText} text-sm rounded-full`}>
                    📂 {currentInsight.insight_data.category_name}
                  </span>
                )}
              </div>
            )}

            {/* Show count */}
            {currentInsight.show_count > 0 && (
              <p className="text-xs text-gray-500 mb-4">
                Bereits {currentInsight.show_count}x angezeigt
              </p>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <button
              onClick={handleDismiss}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Nicht mehr zeigen
            </button>
            
            <button
              onClick={handleClose}
              className={`px-6 py-2 ${colors.badgeBg} ${colors.badgeText} font-medium rounded-lg hover:opacity-80 transition-opacity`}
            >
              Verstanden
            </button>
          </div>

          {/* Progress Indicator (if multiple insights) */}
          {insights.length > 1 && (
            <div className="px-6 pb-3">
              <div className="flex items-center justify-center gap-1">
                {insights.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1.5 rounded-full transition-all ${
                      idx === currentIndex
                        ? 'w-8 bg-primary-600'
                        : 'w-1.5 bg-gray-300'
                    }`}
                  />
                ))}
              </div>
              <p className="text-xs text-center text-gray-500 mt-2">
                Insight {currentIndex + 1} von {insights.length}
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

InsightPopup.propTypes = {
  accountId: PropTypes.number,
  maxInsights: PropTypes.number,
  delayMs: PropTypes.number,
  autoShow: PropTypes.bool,
  onInsightShown: PropTypes.func,
  onInsightDismissed: PropTypes.func
};
