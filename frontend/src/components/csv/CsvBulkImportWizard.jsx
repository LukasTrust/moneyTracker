/**
 * CSV Bulk Import Wizard - Multi-File Import Process
 * 
 * FEATURES:
 * - Multiple file upload (drag & drop)
 * - Uses first file to define schema/mapping
 * - Applies mapping to all files
 * - Shows progress for each file
 * - Continues on error (per-file error handling)
 */

import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { previewCsv, bulkImportCsv, validateSavedMapping, suggestMapping } from '../../services/csvImportApi';
import mappingService from '../../services/mappingService';
import { useToast } from '../../hooks/useToast';

const STEPS = [
  { id: 1, title: 'Dateien auswählen', icon: '📁' },
  { id: 2, title: 'Mapping prüfen', icon: '✓' },
  { id: 3, title: 'Importieren', icon: '⚡' },
];

const REQUIRED_FIELDS = ['date', 'amount', 'recipient'];
const OPTIONAL_FIELDS = ['purpose'];

const FIELD_CONFIG = {
  date: { label: 'Datum', icon: '📅', description: 'Transaktionsdatum' },
  amount: { label: 'Betrag', icon: '💰', description: 'Transaktionsbetrag' },
  recipient: { label: 'Empfänger/Absender', icon: '👤', description: 'Gegenpartei der Transaktion' },
  purpose: { label: 'Verwendungszweck', icon: '📝', description: 'Beschreibung/Buchungstext (optional)' },
};

const getFieldLabel = (field) => FIELD_CONFIG[field]?.label || field;
const getFieldIcon = (field) => FIELD_CONFIG[field]?.icon || '📄';

export default function CsvBulkImportWizard({ accountId, onImportSuccess }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [files, setFiles] = useState([]);
  const [csvPreview, setCsvPreview] = useState(null);
  const [mapping, setMapping] = useState({
    date: '',
    amount: '',
    recipient: '',
    purpose: '',
  });
  const [existingMapping, setExistingMapping] = useState(null);
  const [mappingEditable, setMappingEditable] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const { showToast } = useToast();

  // Load existing mappings when component mounts
  useEffect(() => {
    if (accountId) {
      loadExistingMappings();
    }
  }, [accountId]);

  const loadExistingMappings = async () => {
    try {
      const mappings = await mappingService.getMappings(accountId);
      
      if (mappings && mappings.length > 0) {
        const mappingObj = {};
        mappings.forEach((m) => {
          mappingObj[m.standard_field] = m.csv_header;
        });
        
        setExistingMapping(mappingObj);
        setMapping(mappingObj);
        setMappingEditable(false);
      } else {
        setExistingMapping(null);
        setMappingEditable(true);
      }
    } catch (error) {
      console.error('Error loading mappings:', error);
      setExistingMapping(null);
      setMappingEditable(true);
    }
  };

  // Drag & Drop Configuration for multiple files
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    multiple: true,
    onDrop: async (acceptedFiles) => {
      if (!acceptedFiles || acceptedFiles.length === 0) return;

      setIsLoading(true);
      setFiles(acceptedFiles);
      
      try {
        // Use first file to define schema
        const firstFile = acceptedFiles[0];
        const preview = await previewCsv(firstFile);
        setCsvPreview(preview);
        
        // Validate against saved mappings or suggest new ones
        if (existingMapping) {
          try {
            const validation = await validateSavedMapping(accountId, firstFile);
            
            if (validation.is_valid) {
              setMappingEditable(false);
              showToast(`✅ ${acceptedFiles.length} Dateien geladen. Gespeichertes Mapping wird verwendet.`, 'success');
            } else if (validation.has_saved_mapping) {
              setMappingEditable(true);
              
              // Apply suggestions where available
              const updatedMapping = { ...existingMapping };
              validation.validation_results.forEach(result => {
                if (!result.is_valid && result.suggested_header) {
                  updatedMapping[result.field] = result.suggested_header;
                }
              });
              setMapping(updatedMapping);
              
              showToast(
                `⚠️ Schema weicht ab. Bitte Mapping überprüfen.`,
                'warning'
              );
            }
          } catch (error) {
            console.error('Validation error:', error);
            setMappingEditable(true);
            showToast('⚠️ Bitte Mapping überprüfen.', 'warning');
          }
        } else {
          // No existing mapping - get suggestions
          setMappingEditable(true);
          try {
            const suggestions = await suggestMapping(firstFile);
            
            const suggestedMapping = {
              date: '',
              amount: '',
              recipient: '',
              purpose: '',
            };
            
            Object.entries(suggestions.suggestions).forEach(([field, suggestion]) => {
              if (suggestion.suggested_header && suggestion.confidence > 0.5) {
                suggestedMapping[field] = suggestion.suggested_header;
              }
            });
            
            setMapping(suggestedMapping);
            
            const autoMappedCount = Object.values(suggestedMapping).filter(v => v).length;
            if (autoMappedCount > 0) {
              showToast(
                `✅ ${acceptedFiles.length} Dateien geladen. ${autoMappedCount} Felder automatisch zugeordnet.`,
                'success'
              );
            } else {
              showToast(`✅ ${acceptedFiles.length} Dateien geladen. Bitte ordnen Sie die Felder zu.`, 'success');
            }
          } catch (error) {
            console.error('Error getting suggestions:', error);
            showToast(`✅ ${acceptedFiles.length} Dateien geladen. Bitte ordnen Sie die Felder zu.`, 'success');
          }
        }
        
        setCurrentStep(2);
      } catch (error) {
        showToast(
          error.response?.data?.detail || 'Fehler beim Laden der Dateien',
          'error'
        );
        setFiles([]);
        setCsvPreview(null);
      } finally {
        setIsLoading(false);
      }
    },
  });

  const handleMappingChange = (fieldName, csvHeader) => {
    if (!mappingEditable) return;
    
    setMapping((prev) => ({
      ...prev,
      [fieldName]: csvHeader,
    }));
  };

  const enableMappingEdit = () => {
    setMappingEditable(true);
  };

  const handleStartBulkImport = async () => {
    if (!files || files.length === 0 || !mapping) return;

    // Validate mapping before starting import
    const missingFields = REQUIRED_FIELDS.filter(field => !mapping[field]);
    
    if (missingFields.length > 0) {
      showToast(
        `❌ Pflichtfelder fehlen: ${missingFields.join(', ')}`,
        'error'
      );
      return;
    }

    setIsLoading(true);
    setCurrentStep(3);
    setUploadProgress(0);

    try {
      const result = await bulkImportCsv(accountId, mapping, files, {
        onProgress: (progress) => {
          setUploadProgress(progress.progress);
        }
      });
      
      setImportResult(result);
      
      // Show summary
      if (result.successful_files > 0) {
        showToast(
          `✅ ${result.successful_files}/${result.total_files} Dateien erfolgreich importiert! ${result.total_imported_count} Transaktionen.`,
          'success'
        );
      }
      
      if (result.failed_files > 0) {
        showToast(
          `⚠️ ${result.failed_files} Dateien fehlgeschlagen`,
          'warning'
        );
      }
      
      if (result.total_duplicate_count > 0) {
        showToast(
          `ℹ️ ${result.total_duplicate_count} Duplikate übersprungen`,
          'info'
        );
      }
      
      if (result.recurring_detected > 0) {
        showToast(
          `📋 ${result.recurring_detected} wiederkehrende Verträge erkannt`,
          'success'
        );
      }

      // Reload mappings
      await loadExistingMappings();
      
      // Notify parent
      if (onImportSuccess) {
        onImportSuccess();
      }
    } catch (error) {
      const errorDetail = error.response?.data?.detail || 'Unbekannter Fehler beim Import';
      showToast(
        `❌ Bulk-Import fehlgeschlagen: ${errorDetail}`,
        'error'
      );
      setCurrentStep(2);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentStep(1);
    setFiles([]);
    setCsvPreview(null);
    setMapping(existingMapping || {
      date: '',
      amount: '',
      recipient: '',
      purpose: '',
    });
    setMappingEditable(!existingMapping);
    setImportResult(null);
    setUploadProgress(0);
  };

  return (
    <div className="space-y-6">
      {/* Progress Stepper */}
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`
                    w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold transition-all
                    ${currentStep >= step.id
                      ? 'bg-primary-600 text-white'
                      : 'bg-neutral-200 text-neutral-500'
                    }
                    ${currentStep === step.id ? 'ring-4 ring-primary-200' : ''}
                  `}
                >
                  {step.icon}
                </div>
                <span
                  className={`
                    mt-2 text-xs font-medium text-center
                    ${currentStep >= step.id ? 'text-neutral-900' : 'text-neutral-500'}
                  `}
                >
                  {step.title}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`
                    flex-1 h-1 mx-2 rounded transition-all
                    ${currentStep > step.id ? 'bg-primary-600' : 'bg-neutral-200'}
                  `}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        {/* STEP 1: Multiple File Upload */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-neutral-900">
              <span aria-hidden="true">📁</span> CSV-Dateien hochladen (Bulk)
            </h2>
            <p className="text-neutral-600">
              Laden Sie mehrere CSV-Dateien gleichzeitig hoch. Die erste Datei definiert das Schema.
            </p>

            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all
                ${isDragActive
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-neutral-300 hover:border-neutral-400 bg-neutral-50'
                }
              `}
            >
              <input {...getInputProps()} />
              <div className="text-6xl mb-4" aria-hidden="true">📄📄📄</div>
              {isDragActive ? (
                <p className="text-lg font-medium text-primary-600">
                  Dateien hier ablegen...
                </p>
              ) : (
                <>
                  <p className="text-lg font-medium text-neutral-900 mb-2">
                    Mehrere CSV-Dateien hierher ziehen oder klicken
                  </p>
                  <p className="text-sm text-neutral-500">
                    Unterstützte Formate: .csv (mehrere Dateien möglich)
                  </p>
                </>
              )}
            </div>

            {isLoading && (
              <div className="flex items-center justify-center gap-3 py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary-600 border-t-transparent" aria-hidden="true"></div>
                <span className="text-neutral-600">Analysiere erste Datei...</span>
              </div>
            )}
          </div>
        )}

        {/* STEP 2: Mapping Configuration & Preview */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-neutral-900">
                  ✓ Mapping prüfen
                </h2>
                <p className="text-neutral-600 mt-1">
                  Schema wird auf alle {files.length} Datei(en) angewendet
                </p>
              </div>
              <button
                onClick={() => setCurrentStep(1)}
                className="text-sm text-neutral-500 hover:text-neutral-700"
                aria-label="Zurück zum Upload"
              >
                ← Zurück
              </button>
            </div>

            {/* File List */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                📁 {files.length} Datei(en) ausgewählt:
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                {files.slice(0, 5).map((file, idx) => (
                  <li key={idx}>• {file.name}</li>
                ))}
                {files.length > 5 && (
                  <li className="text-blue-600">... und {files.length - 5} weitere</li>
                )}
              </ul>
            </div>

            {csvPreview && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm text-green-800">
                  ✓ Schema erkannt: <strong>{csvPreview.total_rows}</strong> Zeilen (erste Datei),{' '}
                  <strong>{csvPreview.headers.length}</strong> Spalten
                </p>
              </div>
            )}

            {/* Mapping Configuration */}
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-neutral-900">
                  Felder zuordnen
                </h3>
                {existingMapping && !mappingEditable && (
                  <button
                    onClick={enableMappingEdit}
                    className="px-3 py-1.5 text-sm font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100"
                  >
                    ✏️ Mapping ändern
                  </button>
                )}
              </div>

              <div className="space-y-4">
                {REQUIRED_FIELDS.map((field) => (
                  <div key={field} className="border rounded-lg p-4 border-neutral-200">
                    <label className="block text-sm font-medium text-neutral-900 mb-2">
                      <span className="mr-2">{getFieldIcon(field)}</span>
                      {getFieldLabel(field)}
                      <span className="text-red-500 ml-1">*</span>
                      {!mappingEditable && (
                        <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                      )}
                    </label>
                    <select
                      value={mapping[field] || ''}
                      onChange={(e) => handleMappingChange(field, e.target.value)}
                      disabled={!mappingEditable}
                      className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
                    >
                      <option value="">-- Bitte wählen --</option>
                      {csvPreview?.headers.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
                  </div>
                ))}

                {OPTIONAL_FIELDS.map((field) => (
                  <div key={field} className="border rounded-lg p-4 border-neutral-200 bg-neutral-50">
                    <label className="block text-sm font-medium text-neutral-900 mb-2">
                      <span className="mr-2">{getFieldIcon(field)}</span>
                      {getFieldLabel(field)}
                      <span className="text-neutral-400 ml-1 text-xs">(optional)</span>
                      {!mappingEditable && (
                        <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                      )}
                    </label>
                    <select
                      value={mapping[field] || ''}
                      onChange={(e) => handleMappingChange(field, e.target.value)}
                      disabled={!mappingEditable}
                      className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
                    >
                      <option value="">-- Nicht zuordnen --</option>
                      {csvPreview?.headers.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Validation Alert */}
            {(() => {
              const missingFields = REQUIRED_FIELDS.filter(field => !mapping[field]);
              const hasAllRequired = missingFields.length === 0;
              
              return (
                <>
                  {!hasAllRequired && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">⚠️</span>
                        <div>
                          <h3 className="font-semibold text-red-900 mb-1">
                            Pflichtfelder fehlen
                          </h3>
                          <p className="text-sm text-red-700">
                            Folgende Felder müssen gemappt werden: <strong>{missingFields.map(f => getFieldLabel(f)).join(', ')}</strong>
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  {hasAllRequired && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">✅</span>
                        <div>
                          <h3 className="font-semibold text-green-900 mb-1">
                            Mapping vollständig
                          </h3>
                          <p className="text-sm text-green-700">
                            Bereit für Bulk-Import von {files.length} Datei(en)
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              );
            })()}

            <div className="flex gap-3">
              <button
                onClick={handleStartBulkImport}
                disabled={!REQUIRED_FIELDS.every(field => mapping[field])}
                className={`
                  flex-1 px-6 py-3 rounded-lg font-semibold transition-colors
                  ${!REQUIRED_FIELDS.every(field => mapping[field])
                    ? 'bg-neutral-300 text-neutral-500 cursor-not-allowed'
                    : 'bg-primary-600 text-white hover:bg-primary-700'
                  }
                `}
              >
                ⚡ Bulk-Import starten
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Import Progress & Results */}
        {currentStep === 3 && (
          <div className="space-y-6">
            {isLoading ? (
              <div className="text-center">
                <div className="text-6xl mb-4">⚡</div>
                <h2 className="text-xl font-bold text-neutral-900 mb-4">
                  Importiere {files.length} Datei(en)...
                </h2>
                
                {uploadProgress > 0 && (
                  <div className="max-w-md mx-auto">
                    <div className="flex justify-between text-sm text-neutral-600 mb-2">
                      <span>Upload-Fortschritt</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ) : importResult ? (
              <>
                <div className="text-center">
                  <div className="text-6xl mb-4">
                    {importResult.successful_files === importResult.total_files ? '✅' : '⚠️'}
                  </div>
                  <h2 className="text-2xl font-bold mb-2" style={{
                    color: importResult.successful_files === importResult.total_files ? '#059669' : '#d97706'
                  }}>
                    {importResult.successful_files === importResult.total_files 
                      ? 'Bulk-Import erfolgreich!'
                      : 'Bulk-Import teilweise erfolgreich'
                    }
                  </h2>
                  <p className="text-neutral-600">{importResult.message}</p>
                </div>
                
                {/* Summary Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-blue-600">
                      {importResult.successful_files}
                    </p>
                    <p className="text-sm text-blue-700 mt-1">Erfolgreich</p>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-green-600">
                      {importResult.total_imported_count}
                    </p>
                    <p className="text-sm text-green-700 mt-1">Transaktionen</p>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-yellow-600">
                      {importResult.total_duplicate_count}
                    </p>
                    <p className="text-sm text-yellow-700 mt-1">Duplikate</p>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-red-600">
                      {importResult.failed_files}
                    </p>
                    <p className="text-sm text-red-700 mt-1">Fehlgeschlagen</p>
                  </div>
                </div>

                {/* Per-File Results */}
                <div className="max-w-4xl mx-auto">
                  <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                    Detaillierte Ergebnisse pro Datei:
                  </h3>
                  <div className="space-y-2">
                    {importResult.file_results.map((fileResult, idx) => (
                      <div
                        key={idx}
                        className={`border rounded-lg p-4 ${
                          fileResult.success
                            ? 'border-green-200 bg-green-50'
                            : 'border-red-200 bg-red-50'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className={`font-semibold ${
                              fileResult.success ? 'text-green-900' : 'text-red-900'
                            }`}>
                              {fileResult.success ? '✅' : '❌'} {fileResult.filename}
                            </h4>
                            <p className={`text-sm mt-1 ${
                              fileResult.success ? 'text-green-700' : 'text-red-700'
                            }`}>
                              {fileResult.message}
                            </p>
                            {fileResult.errors && fileResult.errors.length > 0 && (
                              <details className="mt-2">
                                <summary className="text-xs text-red-600 cursor-pointer">
                                  Fehler anzeigen ({fileResult.errors.length})
                                </summary>
                                <ul className="text-xs text-red-600 mt-2 space-y-1 list-disc list-inside">
                                  {fileResult.errors.map((error, errIdx) => (
                                    <li key={errIdx}>{error}</li>
                                  ))}
                                </ul>
                              </details>
                            )}
                          </div>
                          {fileResult.success && (
                            <div className="ml-4 text-right">
                              <div className="text-sm font-semibold text-green-700">
                                {fileResult.imported_count} importiert
                              </div>
                              {fileResult.duplicate_count > 0 && (
                                <div className="text-xs text-yellow-600">
                                  {fileResult.duplicate_count} Duplikate
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="text-center">
                  <button
                    onClick={handleReset}
                    className="bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700"
                  >
                    Weiteren Bulk-Import starten
                  </button>
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
