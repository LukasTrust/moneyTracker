import React, { useState, useEffect } from 'react';
import { useBudgetStore } from '../../store/budgetStore';
import { useCategoryStore } from '../../store/categoryStore';
import Button from '../common/Button';
import Input from '../common/Input';
import Modal from '../common/Modal';
import Card from '../common/Card';
import { ConfirmDialog } from '../common/Modal';
import { useToast } from '../../hooks/useToast';
import { parseAmount } from '../../utils/amount';

/**
 * BudgetManager - CRUD-Interface für Budgets
 * 
 * FEATURES:
 * - Liste aller Budgets mit Kategorie, Periode, Betrag
 * - Erstellen neuer Budgets
 * - Bearbeiten bestehender Budgets
 * - Löschen von Budgets (mit Bestätigung)
 * - Periode-Auswahl (monthly, yearly, quarterly, custom)
 * - Datum-Validierung
 * - Kategorie-Auswahl mit Farb-Indikator
 * 
 * @param {Object} props
 * @param {Function} props.onBudgetChange - Callback bei Änderungen
 */

const PERIOD_OPTIONS = [
  { value: 'monthly', label: 'Monatlich' },
  { value: 'yearly', label: 'Jährlich' },
  { value: 'quarterly', label: 'Quartalsweise' },
  { value: 'custom', label: 'Benutzerdefiniert' }
];

function BudgetManager({ onBudgetChange }) {
  const { showToast } = useToast();
  
  // Store Hooks
  const {
    budgets,
    loading,
    error,
    fetchBudgets,
    createBudget,
    updateBudget,
    deleteBudget,
    clearError
  } = useBudgetStore();
  
  const { categories, fetchCategories } = useCategoryStore();

  // Local State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [deletingBudget, setDeletingBudget] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    category_id: '',
    period: 'monthly',
    amount: '',
    start_date: '',
    end_date: '',
    description: ''
  });

  const [formErrors, setFormErrors] = useState({});

  // Load budgets and categories on mount
  useEffect(() => {
    fetchBudgets({ force: true });
    fetchCategories();
  }, [fetchBudgets, fetchCategories]);

  // Clear error when component unmounts
  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  /**
   * Öffnet Modal zum Erstellen eines neuen Budgets
   */
  const handleCreate = () => {
    setEditingBudget(null);
    
    // Set defaults for current month
    const now = new Date();
    const startDate = new Date(now.getFullYear(), now.getMonth(), 1);
    const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    setFormData({
      category_id: categories[0]?.id || '',
      period: 'monthly',
      amount: '',
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      description: ''
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  /**
   * Öffnet Modal zum Bearbeiten eines Budgets
   */
  const handleEdit = (budget) => {
    setEditingBudget(budget);
    setFormData({
      category_id: budget.category_id,
      period: budget.period,
      amount: budget.amount.toString(),
      start_date: budget.start_date,
      end_date: budget.end_date,
      description: budget.description || ''
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  /**
   * Validierung der Form-Daten
   */
  const validateForm = () => {
    const errors = {};

    if (!formData.category_id) {
      errors.category_id = 'Kategorie ist erforderlich';
    }

    if (!formData.amount || parseAmount(formData.amount) <= 0) {
      errors.amount = 'Betrag muss größer als 0 sein';
    }

    if (!formData.start_date) {
      errors.start_date = 'Startdatum ist erforderlich';
    }

    if (!formData.end_date) {
      errors.end_date = 'Enddatum ist erforderlich';
    }

    if (formData.start_date && formData.end_date && formData.start_date > formData.end_date) {
      errors.end_date = 'Enddatum muss nach Startdatum liegen';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Speichern (Erstellen oder Aktualisieren)
   */
  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSaving(true);
    try {
      const budgetData = {
        category_id: parseInt(formData.category_id),
        period: formData.period,
        amount: parseAmount(formData.amount),
        start_date: formData.start_date,
        end_date: formData.end_date,
        description: formData.description || null
      };

      if (editingBudget) {
        await updateBudget(editingBudget.id, budgetData);
        showToast('Budget erfolgreich aktualisiert', 'success');
      } else {
        await createBudget(budgetData);
        showToast('Budget erfolgreich erstellt', 'success');
      }

      setIsModalOpen(false);
      if (onBudgetChange) onBudgetChange();
    } catch (err) {
      showToast(err.message || 'Fehler beim Speichern des Budgets', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Löschen mit Bestätigung
   */
  const handleDeleteClick = (budget) => {
    setDeletingBudget(budget);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingBudget) return;

    try {
      await deleteBudget(deletingBudget.id);
      showToast('Budget erfolgreich gelöscht', 'success');
      if (onBudgetChange) onBudgetChange();
    } catch (err) {
      showToast(err.message || 'Fehler beim Löschen des Budgets', 'error');
    } finally {
      setDeletingBudget(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeletingBudget(null);
  };

  /**
   * Periode ändern → Datum automatisch anpassen
   */
  const handlePeriodChange = (period) => {
    setFormData((prev) => ({ ...prev, period }));

    if (period === 'custom') return;

    const now = new Date();
    let startDate, endDate;

    switch (period) {
      case 'monthly':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        break;
      case 'yearly':
        startDate = new Date(now.getFullYear(), 0, 1);
        endDate = new Date(now.getFullYear(), 11, 31);
        break;
      case 'quarterly':
        const quarter = Math.floor(now.getMonth() / 3);
        startDate = new Date(now.getFullYear(), quarter * 3, 1);
        endDate = new Date(now.getFullYear(), quarter * 3 + 3, 0);
        break;
      default:
        return;
    }

    setFormData((prev) => ({
      ...prev,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    }));
  };

  /**
   * Helper: Get category name by ID
   */
  const getCategoryName = (categoryId) => {
    const categoriesArray = Array.isArray(categories) ? categories : [];
    const category = categoriesArray.find((c) => c.id === categoryId);
    return category ? category.name : 'Unbekannt';
  };

  /**
   * Helper: Get category color by ID
   */
  const getCategoryColor = (categoryId) => {
    const categoriesArray = Array.isArray(categories) ? categories : [];
    const category = categoriesArray.find((c) => c.id === categoryId);
    return category ? category.color : '#3b82f6';
  };

  /**
   * Format period label
   */
  const getPeriodLabel = (period) => {
    const option = PERIOD_OPTIONS.find((opt) => opt.value === period);
    return option ? option.label : period;
  };

  // Ensure categories and budgets are always arrays
  const categoriesArray = Array.isArray(categories) ? categories : [];
  const budgetsArray = Array.isArray(budgets) ? budgets : [];

  if (loading && budgetsArray.length === 0) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-500">Lade Budgets...</div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Budget-Verwaltung</h2>
          <Button onClick={handleCreate} disabled={loading || categoriesArray.length === 0}>
            + Neues Budget
          </Button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
            {error}
          </div>
        )}

        {categoriesArray.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Bitte erstelle zuerst Kategorien, bevor du Budgets anlegst.
          </div>
        )}

        {budgetsArray.length === 0 && categoriesArray.length > 0 ? (
          <div className="text-center py-8 text-gray-500">
            Noch keine Budgets vorhanden. Erstelle dein erstes Budget!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Kategorie</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Periode</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Betrag</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Zeitraum</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Beschreibung</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Aktionen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {budgetsArray.map((budget) => (
                  <tr key={budget.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getCategoryColor(budget.category_id) }}
                        />
                        <span className="font-medium">{getCategoryName(budget.category_id)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {getPeriodLabel(budget.period)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-green-600">
                      {parseAmount(budget.amount).toFixed(2)} €
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {budget.start_date} bis {budget.end_date}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                      {budget.description || '-'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleEdit(budget)}
                          className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                          disabled={deletingBudget?.id === budget.id}
                        >
                          Bearbeiten
                        </button>
                        <button
                          onClick={() => handleDeleteClick(budget)}
                          className="px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                          disabled={deletingBudget?.id === budget.id}
                        >
                          Löschen
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingBudget ? 'Budget bearbeiten' : 'Neues Budget erstellen'}
      >
        <div className="space-y-4">
          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Kategorie *
            </label>
            <select
              value={formData.category_id}
              onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSaving}
            >
              <option value="">Kategorie wählen...</option>
              {categoriesArray.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
            {formErrors.category_id && (
              <p className="mt-1 text-sm text-red-600">{formErrors.category_id}</p>
            )}
          </div>

          {/* Period Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Periode *
            </label>
            <select
              value={formData.period}
              onChange={(e) => handlePeriodChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSaving}
            >
              {PERIOD_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Amount */}
          <div>
            <Input
              label="Betrag (€) *"
              type="number"
              step="0.01"
              min="0"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              error={formErrors.amount}
              disabled={isSaving}
              placeholder="z.B. 500.00"
            />
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Input
                label="Startdatum *"
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                error={formErrors.start_date}
                disabled={isSaving}
              />
            </div>
            <div>
              <Input
                label="Enddatum *"
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                error={formErrors.end_date}
                disabled={isSaving}
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Beschreibung (optional)
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="3"
              placeholder="z.B. Budget für Weihnachtseinkäufe"
              disabled={isSaving}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
              disabled={isSaving}
            >
              Abbrechen
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? 'Speichern...' : 'Speichern'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deletingBudget !== null}
        onCancel={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Budget löschen?"
        message={
          deletingBudget
            ? `Möchten Sie das Budget für "${getCategoryName(deletingBudget.category_id)}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`
            : ''
        }
        confirmText="Löschen"
        cancelText="Abbrechen"
        variant="danger"
      />
    </div>
  );
}

export default BudgetManager;
