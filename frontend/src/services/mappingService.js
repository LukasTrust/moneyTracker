import api from './api';

/**
 * Mapping Service - Verwaltet Header-Zuordnungen
 */

export const mappingService = {
  /**
   * Mappings für ein Konto abrufen
   */
  async getMappings(accountId) {
    const response = await api.get(`/accounts/${accountId}/mappings`);
    return response.data;
  },

  /**
   * Mappings für ein Konto erstellen/aktualisieren
   */
  async saveMappings(accountId, mappings) {
    const response = await api.post(`/accounts/${accountId}/mappings`, {
      mappings,
    });
    return response.data;
  },

  /**
   * Alle Mappings für ein Konto löschen
   */
  async deleteMappings(accountId) {
    const response = await api.delete(`/accounts/${accountId}/mappings`);
    return response.data;
  },
};

export default mappingService;
