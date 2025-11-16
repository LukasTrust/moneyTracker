import api from './api';

/**
 * Category Service - Verwaltet Kategorien und deren Mappings
 * 
 * API-ROUTEN (Backend):
 * - GET    /categories                     → Alle globalen Kategorien
 * - POST   /categories                     → Neue Kategorie erstellen
 * - PUT    /categories/{id}                → Kategorie bearbeiten
 * - DELETE /categories/{id}                → Kategorie löschen
 * - GET    /accounts/{id}/categories-data  → Aggregierte Daten pro Kategorie
 */

export const categoryService = {
  async getCategories() {
    const response = await api.get('/categories');
    return response.data;
  },

  async getCategory(categoryId) {
    const response = await api.get(`/categories/${categoryId}`);
    return response.data;
  },

  async createCategory(categoryData) {
    const response = await api.post('/categories', categoryData);
    return response.data;
  },

  async updateCategory(categoryId, categoryData) {
    const response = await api.put(`/categories/${categoryId}`, categoryData);
    return response.data;
  },

  async deleteCategory(categoryId) {
    await api.delete(`/categories/${categoryId}`);
  },

  async recategorizeTransactions(accountId = null) {
    const queryParams = new URLSearchParams();
    if (accountId) queryParams.append('account_id', accountId);
    
    const response = await api.post(`/categories/recategorize?${queryParams}`);
    return response.data;
  },

  async checkPatternConflict(pattern, currentCategoryId = null) {
    const queryParams = new URLSearchParams();
    if (currentCategoryId) queryParams.append('current_category_id', currentCategoryId);
    
    const response = await api.get(`/categories/check-pattern-conflict/${encodeURIComponent(pattern)}?${queryParams}`);
    return response.data;
  },

  async removePatternFromCategory(categoryId, pattern) {
    const response = await api.delete(`/categories/${categoryId}/pattern/${encodeURIComponent(pattern)}`);
    return response.data;
  },

  async getCategoryData(accountId, params = {}) {
    const { fromDate, toDate } = params;
    
    const queryParams = new URLSearchParams();
    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);

    console.debug('[CategoryService] getCategoryData:', {
      accountId,
      params,
      queryParams: queryParams.toString()
    });

    const response = await api.get(
      `/accounts/${accountId}/categories-data?${queryParams}`
    );
    return response.data;
  },

  async getCategoryTransactions(accountId, categoryId, params = {}) {
    const { fromDate, toDate, limit = 50, offset = 0 } = params;
    
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);

    const response = await api.get(
      `/accounts/${accountId}/categories/${categoryId}/transactions?${queryParams}`
    );
    return response.data;
  }
};

export default categoryService;
