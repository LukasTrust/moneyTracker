import React from 'react';

/**
 * Upload Progress Bar
 */
export default function UploadProgress({ progress }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-neutral-700">Wird hochgeladen...</span>
        <span className="text-neutral-600">{progress}%</span>
      </div>
      <div className="w-full bg-neutral-200 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-primary-600 h-2.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
