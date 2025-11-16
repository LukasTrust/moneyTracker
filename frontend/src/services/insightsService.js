import api from './api';

/**
 * Insights Service - Verwaltet personalisierte Spending-Insights
 * 
 * API-ROUTEN (Backend):
 * - GET    /insights                      → Alle Insights abrufen
 * - POST   /insights/generate             → Neue Insights generieren
 * - POST   /insights/dismiss/{id}         → Insight ausblenden
 * - GET    /insights/statistics           → Insight-Statistiken
 * - GET    /insights/generation-logs      → Generierungshistorie
 * - DELETE /insights/{id}                 → Insight löschen
 */

const insightsService = {
  /**
   * Get insights ready to be displayed (respecting cooldown)
   * @param {Object} params - Query-Parameter
   * @param {number} params.accountId - Filter nach Account
   * @param {number} params.maxCount - Maximale Anzahl (Standard: 1)
   * @returns {Promise<Array>} Displayable insights
   */
  async getDisplayableInsights({ accountId = null, maxCount = 1 } = {}) {
    const params = new URLSearchParams();
    if (accountId !== null) params.append('account_id', accountId);
    if (maxCount) params.append('max_count', maxCount);
    
    const response = await api.get(`/insights/displayable?${params}`);
    return response.data;
  },

  /**
   * Mark insight as shown (starts cooldown timer)
   * @param {number} insightId - Insight-ID
   * @returns {Promise<Object>} { success: boolean, message: string }
   */
  async markInsightShown(insightId) {
    const response = await api.post(`/insights/mark-shown/${insightId}`);
    return response.data;
  },

  /**
   * Alle Insights abrufen
   * @param {Object} params - Query-Parameter
   * @param {number} params.accountId - Filter nach Account (null = alle + globale)
   * @param {boolean} params.includeDismissed - Ausgeblendete Insights einschließen
   * @param {string} params.insightType - Filter nach Typ (mom_increase, yoy_decrease, etc.)
   * @param {string} params.severity - Filter nach Schweregrad (info, success, warning, alert)
   * @param {number} params.limit - Maximale Anzahl (Standard: 20)
   * @returns {Promise<Object>} { insights: [], total: number, active_count: number, dismissed_count: number }
   */
  async getInsights({ 
    accountId = null, 
    includeDismissed = false, 
    insightType = null, 
    severity = null, 
    limit = 20 
  } = {}) {
    const params = new URLSearchParams();
    if (accountId !== null) params.append('account_id', accountId);
    if (includeDismissed) params.append('include_dismissed', 'true');
    if (insightType) params.append('insight_type', insightType);
    if (severity) params.append('severity', severity);
    if (limit) params.append('limit', limit);
    
    const response = await api.get(`/insights?${params}`);
    return response.data;
  },

  /**
   * Neue Insights generieren
   * @param {Object} params - Generierungs-Parameter
   * @param {number} params.accountId - Account-ID (null = globale Insights)
   * @param {Array<string>} params.generationTypes - Typen: ['mom', 'yoy', 'category_growth', 'savings_potential', 'full_analysis']
   * @param {boolean} params.forceRegenerate - Erneute Generierung erzwingen
   * @returns {Promise<Object>} { success: boolean, insights_generated: number, message: string }
   */
  async generateInsights({ 
    accountId = null, 
    generationTypes = null, 
    forceRegenerate = false 
  } = {}) {
    const payload = {
      account_id: accountId,
      generation_types: generationTypes,
      force_regenerate: forceRegenerate
    };
    
    const response = await api.post('/insights/generate', payload);
    return response.data;
  },

  /**
   * Insight ausblenden (dismiss)
   * @param {number} insightId - Insight-ID
   * @returns {Promise<Object>} { success: boolean, message: string }
   */
  async dismissInsight(insightId) {
    const response = await api.post(`/insights/dismiss/${insightId}`);
    return response.data;
  },

  /**
   * Insight dauerhaft löschen
   * @param {number} insightId - Insight-ID
   * @returns {Promise<Object>} { success: boolean, message: string }
   */
  async deleteInsight(insightId) {
    const response = await api.delete(`/insights/${insightId}`);
    return response.data;
  },

  /**
   * Insight-Statistiken abrufen
   * @param {number} accountId - Optional: Filter nach Account
   * @returns {Promise<Object>} Statistiken über Insights
   */
  async getStatistics(accountId = null) {
    const params = new URLSearchParams();
    if (accountId !== null) params.append('account_id', accountId);
    
    const response = await api.get(`/insights/statistics?${params}`);
    return response.data;
  },

  /**
   * Generierungshistorie abrufen
   * @param {Object} params - Query-Parameter
   * @param {number} params.accountId - Filter nach Account
   * @param {number} params.limit - Maximale Anzahl (Standard: 10)
   * @returns {Promise<Array>} Generierungs-Logs
   */
  async getGenerationLogs({ accountId = null, limit = 10 } = {}) {
    const params = new URLSearchParams();
    if (accountId !== null) params.append('account_id', accountId);
    if (limit) params.append('limit', limit);
    
    const response = await api.get(`/insights/generation-logs?${params}`);
    return response.data;
  },

  /**
   * Severity zu Farbe mappen (für UI)
   * @param {string} severity - info, success, warning, alert
   * @returns {Object} { bg: string, text: string, border: string, icon: string }
   */
  getSeverityColors(severity) {
    const colors = {
      info: {
        bg: 'bg-blue-50',
        text: 'text-blue-700',
        border: 'border-blue-200',
        icon: '💡',
        badgeBg: 'bg-blue-100',
        badgeText: 'text-blue-800'
      },
      success: {
        bg: 'bg-green-50',
        text: 'text-green-700',
        border: 'border-green-200',
        icon: '✅',
        badgeBg: 'bg-green-100',
        badgeText: 'text-green-800'
      },
      warning: {
        bg: 'bg-yellow-50',
        text: 'text-yellow-700',
        border: 'border-yellow-200',
        icon: '⚠️',
        badgeBg: 'bg-yellow-100',
        badgeText: 'text-yellow-800'
      },
      alert: {
        bg: 'bg-red-50',
        text: 'text-red-700',
        border: 'border-red-200',
        icon: '🚨',
        badgeBg: 'bg-red-100',
        badgeText: 'text-red-800'
      }
    };
    
    return colors[severity] || colors.info;
  },

  /**
   * Insight-Type zu deutschem Label mappen
   * @param {string} insightType - z.B. 'mom_increase'
   * @returns {string} Deutscher Label
   */
  getInsightTypeLabel(insightType) {
    const labels = {
      mom_increase: 'Ausgaben gestiegen (Monat)',
      mom_decrease: 'Ausgaben gesunken (Monat)',
      yoy_increase: 'Ausgaben gestiegen (Jahr)',
      yoy_decrease: 'Ausgaben gesunken (Jahr)',
      top_growth_category: 'Kategorie mit höchstem Wachstum',
      savings_potential: 'Sparpotenzial erkannt',
      unusual_expense: 'Ungewöhnliche Ausgabe'
    };
    
    return labels[insightType] || insightType;
  }
};

export default insightsService;
