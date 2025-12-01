import api from './api';
import { toApiAmount } from '../utils/amount';

/**
 * Account Service - Verwaltet alle API-Calls für Konten
 * Uses amount utilities for consistent money handling
 */

export const accountService = {
  /**
   * Alle Konten abrufen
   */
  async getAccounts() {
    const response = await api.get('/accounts');
    return response.data;
  },

  /**
   * Einzelnes Konto abrufen
   */
  async getAccount(id) {
    const response = await api.get(`/accounts/${id}`);
    return response.data;
  },

  /**
   * Neues Konto erstellen
   */
  async createAccount(accountData) {
    const response = await api.post('/accounts', accountData);
    return response.data;
  },

  /**
   * Konto aktualisieren
   */
  async updateAccount(id, accountData) {
    const response = await api.put(`/accounts/${id}`, accountData);
    return response.data;
  },

  /**
   * Konto löschen
   */
  async deleteAccount(id) {
    const response = await api.delete(`/accounts/${id}`);
    return response.data;
  },
};

export default accountService;
