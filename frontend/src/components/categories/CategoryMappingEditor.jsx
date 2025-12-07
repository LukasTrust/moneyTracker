import React, { useState, useCallback, useEffect } from 'react';
import Button from '../common/Button';
import Card from '../common/Card';
import Input from '../common/Input';
import Modal from '../common/Modal';
import categoryService from '../../services/categoryService';
import { useToast } from '../../hooks/useToast';

/**
 * CategoryMappingEditor - Editor zum Zuordnen von Erkennungsmustern zu Kategorien
 * 
 * FEATURES:
 * - Vereinfachte Mustererkennung: Ein Pattern-Array für alle Erkennungsmuster
 * - Wortgrenzen-basiertes Matching (z.B. "REWE" matched "REWE Markt" aber nicht "SOMEREWETEXT")
 * - Case-insensitive Suche
 * - Durchsucht sowohl Empfänger als auch Verwendungszweck
 * - Automatisches Speichern beim Hinzufügen/Entfernen von Mustern
 * - Sofortige Aktualisierung der Kategorieliste
 * - Konfliktprüfung: Verhindert doppelte Patterns in verschiedenen Kategorien
 * 
 * DATENMODELL:
 * - patterns: Array von Strings, die in Empfänger ODER Verwendungszweck vorkommen können
 * 
 * @param {Object} props
 * @param {Object} props.category - Kategorie-Objekt
 * @param {Function} props.onSave - Callback nach erfolgreichem Speichern (wird sofort aufgerufen)
 * @param {Function} props.onCancel - Callback beim Abbrechen/Schließen
 */
function CategoryMappingEditor({ category, onSave, onCancel }) {
  const { showToast } = useToast();
  const [patterns, setPatterns] = useState([]);
  const [newPattern, setNewPattern] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isRecategorizing, setIsRecategorizing] = useState(false);
  const [recategorizeProgress, setRecategorizeProgress] = useState({ status: '', progress: 0, message: '' });
  
  // Conflict Modal State
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [conflictData, setConflictData] = useState(null);
  const [pendingPattern, setPendingPattern] = useState('');

  // Lade bestehende Patterns beim Mount oder wenn sich category.id ändert
  // WICHTIG: Nur bei ID-Wechsel neu laden, nicht bei jedem refetch!
  useEffect(() => {
    if (category?.mappings?.patterns) {
      setPatterns([...category.mappings.patterns]);
    } else {
      setPatterns([]);
    }
  }, [category?.id]); // ✅ FIX: Nur bei ID-Wechsel, nicht bei refetch

  /**
   * Fügt neues Pattern hinzu und speichert es sofort
   */
  const handleAddPattern = useCallback(async () => {
    const pattern = newPattern.trim();
    if (!pattern) return;

    // Check for duplicates (case-insensitive)
    if (patterns.some(p => p.toLowerCase() === pattern.toLowerCase())) {
      showToast('Dieses Muster existiert bereits', 'warning');
      return;
    }

    // Check pattern length
    if (pattern.length > 100) {
      showToast('Muster darf maximal 100 Zeichen lang sein', 'error');
      return;
    }

    // Check for conflicts with other categories
    try {
      const conflictCheck = await categoryService.checkPatternConflict(pattern, category.id);
      
      if (conflictCheck.conflict) {
        // Show conflict modal instead of window.confirm
        setConflictData(conflictCheck);
        setPendingPattern(pattern);
        setShowConflictModal(true);
        return; // Wait for user decision in modal
      }
    } catch (conflictErr) {
      console.error('❌ Failed to check pattern conflict:', conflictErr);
      showToast('Fehler bei der Konfliktprüfung', 'error');
      return;
    }

    // No conflict, proceed with adding
    await addPatternToCategory(pattern);
  }, [patterns, newPattern, showToast, category]);

  /**
   * Actually adds the pattern to the category (after conflict check)
   */
  const addPatternToCategory = useCallback(async (pattern) => {
    const newPatterns = [...patterns, pattern];
    
    // Sofort lokal aktualisieren für schnelles Feedback
    setPatterns(newPatterns);
    setNewPattern('');
    
    // Sofort speichern, damit es in der Liste erscheint
    try {
      setIsSaving(true);
      const updateData = {
        mappings: { patterns: newPatterns }
      };
      
      const updatedCategory = await categoryService.updateCategory(category.id, updateData);
      
      // Update from server response
      if (updatedCategory?.mappings?.patterns) {
        setPatterns([...updatedCategory.mappings.patterns]);
      }
      
      showToast('Muster hinzugefügt - kategorisiere Transaktionen neu...', 'info');
      
      // Neu-Kategorisierung durchführen mit job support
      try {
        setIsRecategorizing(true);
        const recategorizeResult = await categoryService.recategorizeTransactions(null, {
          waitForCompletion: true,
          onProgress: (progress) => {
            setRecategorizeProgress(progress);
          }
        });
        showToast(
          `${recategorizeResult.updated_count || 0} Transaktionen neu kategorisiert`, 
          'success'
        );
      } catch (recatErr) {
        console.error('⚠️ Recategorization failed:', recatErr);
        showToast('Muster gespeichert, aber Neu-Kategorisierung fehlgeschlagen', 'warning');
      } finally {
        setIsRecategorizing(false);
        setRecategorizeProgress({ status: '', progress: 0, message: '' });
      }
      
      // Informiere Parent-Component über Änderung (damit Liste sofort aktualisiert wird)
      if (onSave) onSave(updatedCategory);
      
      // Sende globales Event für alle Komponenten
      window.dispatchEvent(new CustomEvent('categoryUpdated', { detail: { category: updatedCategory } }));
    } catch (err) {
      console.error('❌ Error auto-saving pattern:', err);
      // Bei Fehler: Zurück zum vorherigen Zustand
      setPatterns(patterns);
      const errorMsg = err.response?.data?.detail || 'Fehler beim Speichern des Musters';
      showToast(errorMsg, 'error');
    } finally {
      setIsSaving(false);
    }
  }, [patterns, category, onSave, showToast]);

  /**
   * Handle conflict modal confirmation
   */
  const handleConflictConfirm = useCallback(async () => {
    if (!conflictData || !pendingPattern) return;

    setShowConflictModal(false);
    
    // Remove from other category
    try {
      await categoryService.removePatternFromCategory(conflictData.category_id, pendingPattern);
      showToast(`Muster wurde aus "${conflictData.category_name}" entfernt`, 'info');
      
      // Now add to current category
      await addPatternToCategory(pendingPattern);
    } catch (removeErr) {
      console.error('❌ Failed to remove pattern from other category:', removeErr);
      showToast('Fehler beim Entfernen des Musters aus der anderen Kategorie', 'error');
    } finally {
      setConflictData(null);
      setPendingPattern('');
      setNewPattern(''); // Clear input
    }
  }, [conflictData, pendingPattern, addPatternToCategory, showToast]);

  /**
   * Handle conflict modal cancel
   */
  const handleConflictCancel = useCallback(() => {
    setShowConflictModal(false);
    setConflictData(null);
    setPendingPattern('');
  }, []);

  /**
   * Entfernt Pattern und speichert sofort
   */
  const handleRemovePattern = useCallback(async (index) => {
    const newPatterns = patterns.filter((_, i) => i !== index);
    const removedPattern = patterns[index];
    
    // Sofort lokal aktualisieren
    setPatterns(newPatterns);
    
    // Sofort speichern
    try {
      setIsSaving(true);
      const updateData = {
        mappings: { patterns: newPatterns }
      };
      
      const updatedCategory = await categoryService.updateCategory(category.id, updateData);
      
      // Update from server response
      if (updatedCategory?.mappings?.patterns) {
        setPatterns([...updatedCategory.mappings.patterns]);
      }
      
      showToast(`Muster "${removedPattern}" entfernt - kategorisiere neu...`, 'info');
      
      // Neu-Kategorisierung durchführen mit job support
      try {
        setIsRecategorizing(true);
        const recategorizeResult = await categoryService.recategorizeTransactions(null, {
          waitForCompletion: true,
          onProgress: (progress) => {
            setRecategorizeProgress(progress);
          }
        });
        showToast(
          `${recategorizeResult.updated_count || 0} Transaktionen neu kategorisiert`, 
          'success'
        );
      } catch (recatErr) {
        console.error('⚠️ Recategorization failed:', recatErr);
        showToast('Muster entfernt, aber Neu-Kategorisierung fehlgeschlagen', 'warning');
      } finally {
        setIsRecategorizing(false);
        setRecategorizeProgress({ status: '', progress: 0, message: '' });
      }
      
      // Informiere Parent-Component über Änderung
      if (onSave) onSave(updatedCategory);
      
      // Sende globales Event für alle Komponenten
      window.dispatchEvent(new CustomEvent('categoryUpdated', { detail: { category: updatedCategory } }));
    } catch (err) {
      console.error('❌ Error auto-saving after remove:', err);
      // Bei Fehler: Zurück zum vorherigen Zustand
      setPatterns(patterns);
      const errorMsg = err.response?.data?.detail || 'Fehler beim Entfernen des Musters';
      showToast(errorMsg, 'error');
    } finally {
      setIsSaving(false);
    }
  }, [patterns, category, onSave, showToast]);

  if (!category) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-500">
          Keine Kategorie ausgewählt
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-neutral-200">
          <div
            className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
            style={{ backgroundColor: category.color + '20' }}
          >
            {category.icon}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold text-neutral-900">
              {category.name}
            </h3>
            <p className="text-sm text-neutral-600">
              Erkennungsmuster bearbeiten
            </p>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4" role="region" aria-label="Info: Erkennungsmuster">
          <div className="flex gap-3">
            <svg className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Wie funktionieren Erkennungsmuster?</p>
              <p>
                Transaktionen werden automatisch dieser Kategorie zugeordnet, wenn ein Muster 
                als ganzes Wort im Empfänger oder Verwendungszweck vorkommt. 
                Beispiel: "REWE" erkennt "REWE Markt" aber nicht "SOMEREWETEXT".
              </p>
            </div>
          </div>
        </div>

        {/* Pattern Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl" aria-hidden="true">🎯</span>
            <h4 className="font-semibold text-neutral-900">Erkennungsmuster</h4>
            <span className="text-sm text-neutral-500">
              ({patterns.length})
            </span>
          </div>

          {/* Input für neues Pattern */}
          <div className="flex gap-2">
            <Input
              value={newPattern}
              onChange={(e) => setNewPattern(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !isSaving) {
                  e.preventDefault();
                  handleAddPattern();
                }
              }}
              placeholder="z.B. REWE, Amazon, Miete, Gehalt"
              className="flex-1"
              disabled={isSaving}
            />

            <Button
              onClick={handleAddPattern}
              disabled={!newPattern.trim() || isSaving}
              size="sm"
              title="Hinzufügen"
              aria-label="Muster hinzufügen"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </Button>
          </div>

          {/* Liste der Patterns */}
            {patterns.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {patterns.map((pattern, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-neutral-50 rounded-lg group hover:bg-neutral-100 transition-colors"
                >
                  <span className="text-sm text-neutral-700 flex-1 break-all font-mono">
                    {pattern}
                  </span>
                  <button
                    onClick={() => handleRemovePattern(index)}
                    disabled={isSaving}
                    className="ml-2 p-1 text-neutral-400 hover:text-red-600 rounded opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Entfernen"
                    aria-label={`Muster ${pattern} entfernen`}
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-sm text-neutral-500 bg-neutral-50 rounded-lg">
              Keine Muster vorhanden
            </div>
          )}
        </div>

        {/* Loading Indicator */}
        {(isSaving || isRecategorizing) && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center gap-2 text-blue-800" role="status" aria-live="polite">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm font-medium">
              {isRecategorizing 
                ? recategorizeProgress.progress > 0 
                  ? `${Math.round(recategorizeProgress.progress)}% ${recategorizeProgress.message || 'Kategorisiere...'}`
                  : 'Kategorisiere Transaktionen...'
                : 'Speichere Änderungen...'
              }
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-neutral-200">
          <Button
            variant="ghost"
            onClick={onCancel}
            className="flex-1"
            disabled={isSaving}
          >
            Schließen
          </Button>
        </div>

        {/* Stats */}
        <div className="pt-4 border-t border-neutral-200">
          <p className="text-xs text-neutral-500 text-center">
            {patterns.length} {patterns.length === 1 ? 'Muster' : 'Muster'}
          </p>
        </div>
      </div>

      {/* Conflict Modal */}
      {showConflictModal && conflictData && (
        <Modal
          isOpen={showConflictModal}
          onClose={handleConflictCancel}
          title="Muster bereits vorhanden"
        >
          <div className="space-y-4">
            {/* Warning Message */}
            <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <svg className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <h4 className="font-semibold text-yellow-900 mb-1">
                  Konflikt erkannt
                </h4>
                <p className="text-sm text-yellow-800">
                  Das Muster <span className="font-mono font-semibold">"{pendingPattern}"</span> ist bereits in einer anderen Kategorie vorhanden.
                </p>
              </div>
            </div>

            {/* Current Category Info */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Aktuell zugeordnet zu:</p>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
                  style={{ backgroundColor: conflictData.category_color + '20' }}
                >
                  {conflictData.category_icon}
                </div>
                <div>
                  <p className="font-semibold text-gray-900">
                    {conflictData.category_name}
                  </p>
                  <p className="text-xs text-gray-500">
                    ID: {conflictData.category_id}
                  </p>
                </div>
              </div>
            </div>

            {/* Question */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                Möchten Sie das Muster aus <span className="font-semibold">"{conflictData.category_name}"</span> entfernen und zu <span className="font-semibold">"{category.name}"</span> hinzufügen?
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <Button
                variant="ghost"
                onClick={handleConflictCancel}
                className="flex-1"
              >
                Abbrechen
              </Button>
              <Button
                variant="primary"
                onClick={handleConflictConfirm}
                className="flex-1"
              >
                Ja, verschieben
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </Card>
  );
}

export default CategoryMappingEditor;
