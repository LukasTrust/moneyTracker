import React from 'react';

/**
 * Import Progress Indicator
 * Shows animated progress during CSV import
 */
export default function ImportProgress({ estimatedRows = 0, stage = 'uploading' }) {
  const stages = {
    uploading: { label: 'Datei wird hochgeladen...', icon: '📤', progress: 25 },
    parsing: { label: 'CSV wird analysiert...', icon: '🔍', progress: 50 },
    validating: { label: 'Daten werden validiert...', icon: '✓', progress: 75 },
    importing: { label: 'Transaktionen werden importiert...', icon: '⚡', progress: 90 },
    finishing: { label: 'Import wird abgeschlossen...', icon: '🎉', progress: 100 },
  };

  const currentStage = stages[stage] || stages.uploading;

  return (
    <div className="space-y-6">
      {/* Icon */}
      <div className="text-6xl animate-bounce" aria-hidden="true">{currentStage.icon}</div>

      {/* Title */}
      <h2 className="text-xl font-bold text-neutral-900">{currentStage.label}</h2>

      {/* Progress Bar */}
      <div className="w-full max-w-md mx-auto">
        <div className="flex items-center justify-between text-sm text-neutral-600 mb-2">
          <span>Fortschritt</span>
          <span className="font-semibold">{currentStage.progress}%</span>
        </div>
        <div className="w-full bg-neutral-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-primary-600 h-3 rounded-full transition-all duration-700 ease-out relative overflow-hidden"
            style={{ width: `${currentStage.progress}%` }}
          >
            {/* Animated shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer" />
          </div>
        </div>
      </div>

      {/* Estimated rows info */}
      {estimatedRows > 0 && (
        <div className="text-sm text-neutral-500">
          Verarbeite ca. <strong className="text-neutral-700">{estimatedRows}</strong> Zeilen
        </div>
      )}

      {/* Loading spinner */}
      <div className="flex items-center justify-center gap-3">
        <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent" aria-hidden="true"></div>
        <span className="text-neutral-600">Bitte warten...</span>
      </div>

      {/* Stage indicators */}
      <div className="flex items-center justify-center gap-2 pt-4">
        {Object.keys(stages).map((stageKey) => {
          const isActive = stageKey === stage;
          const isPast = stages[stageKey].progress < currentStage.progress;
          
          return (
            <div
              key={stageKey}
              className={`
                w-2 h-2 rounded-full transition-all
                ${isActive ? 'bg-primary-600 w-3 h-3' : isPast ? 'bg-primary-300' : 'bg-neutral-300'}
              `}
              aria-hidden="true"
            />
          );
        })}
      </div>
    </div>
  );
}
