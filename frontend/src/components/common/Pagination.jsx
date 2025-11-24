import React from 'react';
import Button from './Button';

/**
 * Reusable Pagination component
 * Props:
 * - page, pages, pageSize, total
 * - loading
 * - onPageChange(newPage)
 * - onPageSizeChange(newSize)
 */
export default function Pagination({
  page = 1,
  pages = 1,
  pageSize = 50,
  total = 0,
  loading = false,
  onPageChange = () => {},
  onPageSizeChange = () => {},
  className = ''
}) {
  return (
    <div className={`my-4 flex items-center justify-between space-x-4 ${className}`}>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={loading || page <= 1}
        >
          Zurück
        </Button>
        <Button
          variant="secondary"
          onClick={() => onPageChange(Math.min(pages, page + 1))}
          disabled={loading || page >= pages}
        >
          Vorwärts
        </Button>
      </div>

      <div className="text-sm text-gray-600">
        Seite {page} von {pages} {total ? ` (Gesamt: ${total})` : ''}
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-600">Einträge pro Seite:</label>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
          className="appearance-none bg-white border border-gray-300 rounded-md px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
          disabled={loading}
        >
          <option value={10}>10</option>
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
    </div>
  );
}
