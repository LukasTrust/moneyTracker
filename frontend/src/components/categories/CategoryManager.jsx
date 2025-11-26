import React, { useState, useCallback } from 'react';
import Button from '../common/Button';
import Input from '../common/Input';
import Modal from '../common/Modal';
import Card from '../common/Card';
import CategoryMappingEditor from './CategoryMappingEditor';
import { useCategoryData } from '../../hooks/useDataFetch';
import categoryService from '../../services/categoryService';
import { useToast } from '../../hooks/useToast';

/**
 * CategoryManager - CRUD-Interface für globale Kategorien
 * 
 * FEATURES:
 * - Liste aller Kategorien mit Name, Farbe, Icon
 * - Erstellen neuer Kategorien
 * - Bearbeiten bestehender Kategorien
 * - Löschen von Kategorien (mit Bestätigung)
 * - Farbwähler und Icon-Auswahl
 * - Inline-Anzeige der Mappings (Absender/Empfänger/Verwendungszweck)
 * - Mapping-Editor zum Hinzufügen/Bearbeiten von Zuordnungen
 * 
 * ERWEITERBARKEIT:
 * - Tags/Labels für Kategorien
 * - Hierarchische Kategorien (Unter-Kategorien)
 * - Import/Export von Kategorien
 * - Vorlagen für häufige Kategorien
 * 
 * @param {Object} props
 * @param {number} props.accountId - Account ID für Autocomplete-Daten im Mapping-Editor
 * @param {Function} props.onCategoryChange - Callback bei Änderungen (für Refresh)
 */

// Vordefinierte Farben zur Auswahl
const PRESET_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
  '#6366f1', // indigo
  '#84cc16', // lime
  '#06b6d4', // cyan
  '#a855f7', // purple
];

// Vordefinierte Icons (Emojis)
const PRESET_ICONS = [
  '🏠', '🛒', '💰', '🚗', '🛡️', '🎮', '📱', '🍔',
  '✈️', '🏥', '📚', '💼', '🎬', '🎵', '⚽', '🏋️',
  '👕', '🎨', '🔧', '🌳', '☕', '🍕', '🎂', '🎁',
];

function CategoryManager({ accountId, onCategoryChange }) {
  const { categories, loading, error, refetch } = useCategoryData();
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [isDeleting, setIsDeleting] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [confirmDeleteTarget, setConfirmDeleteTarget] = useState(null);
  
  // Mapping Editor State
  const [showMappingEditor, setShowMappingEditor] = useState(false);
  const [mappingCategory, setMappingCategory] = useState(null);
  
  // Form State
  const [formData, setFormData] = useState({
    name: '',
    color: PRESET_COLORS[0],
    icon: PRESET_ICONS[0],
  });

  const [formErrors, setFormErrors] = useState({});

  /**
   * Öffnet Modal zum Erstellen einer neuen Kategorie
   */
  const handleCreate = useCallback(() => {
    setEditingCategory(null);
    setFormData({
      name: '',
      color: PRESET_COLORS[0],
      icon: PRESET_ICONS[0],
    });
    setFormErrors({});
    setIsModalOpen(true);
  }, []);

  /**
   * Öffnet Modal zum Bearbeiten einer Kategorie
   */
  const handleEdit = useCallback((category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      color: category.color || PRESET_COLORS[0],
      icon: category.icon || PRESET_ICONS[0],
    });
    setFormErrors({});
    setIsModalOpen(true);
  }, []);

  /**
   * Validiert Form-Daten
   */
  const validateForm = () => {
    const errors = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Name ist erforderlich';
    }
    
    if (!formData.color) {
      errors.color = 'Farbe ist erforderlich';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Speichert Kategorie (Erstellen oder Bearbeiten)
   */
  const { showToast } = useToast();

  const handleSave = async () => {
    if (!validateForm()) return;

    setIsSaving(true);
    try {
      // NOTE: Do not include `mappings` here. Mappings are edited in the
      // MappingEditor and saved separately. Including a stale snapshot here
      // could overwrite newer patterns. Only send fields actually edited in
      // this modal (name/color/icon).
      const categoryData = {
        name: formData.name.trim(),
        color: formData.color,
        icon: formData.icon,
      };

      if (editingCategory) {
        await categoryService.updateCategory(editingCategory.id, categoryData);
      } else {
        await categoryService.createCategory(categoryData);
      }

      setIsModalOpen(false);
      refetch();
      if (onCategoryChange) onCategoryChange();
    } catch (err) {
      console.error('Error saving category:', err);
      showToast('Fehler beim Speichern der Kategorie', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Löscht Kategorie nach Bestätigung
   */
  const handleDelete = async (category) => {
    // open confirmation modal
    setConfirmDeleteTarget(category);
    setShowConfirmDelete(true);
  };

  const handleConfirmDelete = async () => {
    if (!confirmDeleteTarget) return;
    setShowConfirmDelete(false);
    setIsDeleting(confirmDeleteTarget.id);
    try {
      await categoryService.deleteCategory(confirmDeleteTarget.id);
      refetch();
      if (onCategoryChange) onCategoryChange();
      showToast('Kategorie gelöscht', 'success');
    } catch (err) {
      console.error('Error deleting category:', err);
      showToast('Fehler beim Löschen der Kategorie', 'error');
    } finally {
      setIsDeleting(null);
      setConfirmDeleteTarget(null);
    }
  };

  const handleCancelConfirmDelete = () => {
    setShowConfirmDelete(false);
    setConfirmDeleteTarget(null);
  };

  /**
   * Handler für Form-Änderungen
   */
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  /**
   * Öffnet Mapping-Editor für Kategorie
   */
  const handleEditMappings = useCallback((category) => {
    setMappingCategory(category);
    setShowMappingEditor(true);
  }, []);

  /**
   * Handler nach erfolgreichem Speichern der Mappings (ohne Editor zu schließen)
   */
  /**
   * Handler nach erfolgreichem Speichern der Mappings (erwartet optional updatedCategory)
   */
  const handleMappingsSaved = useCallback((updatedCategory) => {
    // Kategorien-Liste im Hintergrund aktualisieren
    refetch();
    if (onCategoryChange) onCategoryChange();

    // Wenn der Editor uns das aktualisierte Category-Objekt zurückgibt,
    // aktualisiere auch den lokalen mappingCategory damit die UI das
    // aktuelle Objekt zeigt (insbesondere wichtig, wenn Editor offen bleibt).
    if (updatedCategory && mappingCategory && updatedCategory.id === mappingCategory.id) {
      setMappingCategory(updatedCategory);
    }
  }, [refetch, onCategoryChange, mappingCategory]);

  /**
   * Schließt Mapping-Editor und aktualisiert Daten
   */
  const handleCloseMappingEditor = useCallback(() => {
    setShowMappingEditor(false);
    setMappingCategory(null);
    refetch();
    if (onCategoryChange) onCategoryChange();
  }, [refetch, onCategoryChange]);

  // Error State
  if (error) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={refetch}>Erneut versuchen</Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Kategorien verwalten</h2>
          <p className="text-sm text-neutral-600 mt-1">
            Erstellen und bearbeiten Sie globale Kategorien für alle Konten
          </p>
        </div>
        <Button onClick={handleCreate} disabled={loading} title="Neue Kategorie erstellen" aria-label="Neue Kategorie">
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Neue Kategorie
        </Button>
      </div>

      {/* Categories List */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-neutral-100 rounded-lg h-32 animate-pulse" />
          ))}
        </div>
      ) : categories.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-neutral-400"
              aria-hidden="true"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-neutral-900">Keine Kategorien</h3>
            <p className="mt-1 text-sm text-neutral-500">
              Erstellen Sie Ihre erste Kategorie, um Transaktionen zu organisieren.
            </p>
            <div className="mt-6">
              <Button onClick={handleCreate}>
                Kategorie erstellen
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((category) => (
            <Card key={category.id}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 flex-1">
                  {/* Icon & Color */}
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                    style={{ backgroundColor: category.color + '20' }}
                  >
                    {category.icon}
                  </div>
                  
                  {/* Name */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-neutral-900 truncate">
                      {category.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: category.color }}
                      />
                      <span className="text-xs text-neutral-500 font-mono">
                        {category.color}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleEdit(category)}
                    className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-gray-100 transition-colors"
                    title="Bearbeiten"
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(category)}
                    className="p-2 text-neutral-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                    title="Löschen"
                    aria-label={`Kategorie ${category.name} löschen`}
                  >
                    {isDeleting === category.id ? (
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Patterns Preview - Zeigt Erkennungsmuster */}
              {category.mappings?.patterns?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-neutral-200">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-medium text-neutral-500">
                      Erkennungsmuster ({category.mappings.patterns.length}):
                    </p>
                    <button
                      onClick={() => handleEditMappings(category)}
                      className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                      aria-label={`Erkennungsmuster für ${category.name} bearbeiten`}
                    >
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Bearbeiten
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {category.mappings.patterns.slice(0, 8).map((pattern, i) => (
                      <span
                        key={`p-${i}`}
                        className="px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded font-mono"
                      >
                        {pattern}
                      </span>
                    ))}
                    {category.mappings.patterns.length > 8 && (
                      <span className="px-2 py-1 text-xs text-neutral-500">
                        +{category.mappings.patterns.length - 8} mehr
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              {/* No Patterns - Add Button */}
              {!category.mappings?.patterns?.length && (
                <div className="mt-4 pt-4 border-t border-neutral-200">
                  <button
                    onClick={() => handleEditMappings(category)}
                    className="w-full text-sm text-neutral-500 hover:text-primary-600 py-2 px-3 rounded-lg hover:bg-primary-50 transition-colors flex items-center justify-center gap-2"
                    aria-label={`Erkennungsmuster für ${category.name} hinzufügen`}
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Erkennungsmuster hinzufügen
                  </button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingCategory ? 'Kategorie bearbeiten' : 'Neue Kategorie'}
      >
        <div className="space-y-4">
          {/* Name */}
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            error={formErrors.name}
            placeholder="z.B. Lebensmittel, Transport, Miete"
            required
          />

          {/* Icon Selector */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Icon
            </label>
            <div className="grid grid-cols-8 gap-2">
              {PRESET_ICONS.map((icon) => (
                <button
                  key={icon}
                  type="button"
                  onClick={() => handleChange('icon', icon)}
                  className={`
                    w-10 h-10 rounded-lg flex items-center justify-center text-2xl
                    transition-all border-2
                    ${formData.icon === icon
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-neutral-200 hover:border-neutral-300 bg-white'
                    }
                  `}
                >
                  {icon}
                </button>
              ))}
            </div>
          </div>

          {/* Color Selector */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Farbe
            </label>
            <div className="grid grid-cols-6 gap-2">
              {PRESET_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => handleChange('color', color)}
                  className={`
                    w-10 h-10 rounded-lg transition-all border-2
                    ${formData.color === color
                      ? 'border-neutral-900 scale-110'
                      : 'border-neutral-200 hover:scale-105'
                    }
                  `}
                  style={{ backgroundColor: color }}
                  title={color}
                />
              ))}
            </div>
            {/* Custom Color Input */}
            <div className="mt-2">
              <Input
                type="color"
                label="Oder eigene Farbe wählen"
                value={formData.color}
                onChange={(e) => handleChange('color', e.target.value)}
              />
            </div>
          </div>

          {/* Actions */}
            <div className="flex gap-3 pt-4">
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1"
            >
              {isSaving ? 'Speichert...' : 'Speichern'}
            </Button>
            <Button
              variant="ghost"
              onClick={() => setIsModalOpen(false)}
              className="flex-1"
            >
              Abbrechen
            </Button>
          </div>
        </div>
      </Modal>

      {/* Mapping Editor Modal */}
      {showMappingEditor && mappingCategory && (
        <Modal
          isOpen={showMappingEditor}
          onClose={handleCloseMappingEditor}
          title={`Zuordnungen für "${mappingCategory.name}"`}
          size="large"
        >
          <CategoryMappingEditor
            category={mappingCategory}
            accountId={accountId}
            onSave={handleMappingsSaved}
            onCancel={handleCloseMappingEditor}
          />
        </Modal>
      )}
      {/* Confirm Delete Modal */}
      {showConfirmDelete && confirmDeleteTarget && (
        <Modal
          isOpen={showConfirmDelete}
          onClose={handleCancelConfirmDelete}
          title="Kategorie löschen"
        >
          <div className="space-y-4">
            <p>Kategorie "{confirmDeleteTarget.name}" wirklich löschen?</p>
            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={handleCancelConfirmDelete}
                className="px-4 py-2 rounded-lg border"
              >
                Abbrechen
              </button>
              <button
                onClick={handleConfirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg"
                disabled={isDeleting === confirmDeleteTarget.id}
              >
                {isDeleting === confirmDeleteTarget.id ? 'Löscht...' : 'Löschen'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default CategoryManager;
