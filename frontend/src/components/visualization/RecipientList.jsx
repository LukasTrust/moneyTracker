import React from 'react';
import Card from '../common/Card';

/**
 * RecipientList - Tabelle für Top Absender/Empfänger
 * 
 * @param {Object} props
 * @param {Array} props.data - Array von {recipient/name, total_amount/value, transaction_count/count} Objekten
 * @param {string} props.title - Tabellen-Titel (z.B. "Top Absender")
 * @param {string} props.type - 'sender' oder 'recipient' für Icon/Styling
 * @param {string} props.currency - Währungssymbol (z.B. "EUR")
 * @param {boolean} props.loading - Zeigt Skeleton Loader wenn true
 * @param {Function} props.onRowClick - Optional: Callback bei Klick auf Zeile
 * 
 * ERWEITERBARKEIT:
 * - Weitere Spalten: Durchschnitt, Letzte Transaktion, Kategorie
 * - Sortierung: onClick auf Header für Sort-Toggle
 * - Pagination: limit/offset Props für große Listen
 */

function RecipientList({ data, title, type = 'recipient', currency = 'EUR', loading = false, onRowClick }) {
  // Icon basierend auf Typ
  const getIcon = () => {
    if (type === 'sender') {
      return (
        <svg
          className="h-5 w-5 text-green-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 11l5-5m0 0l5 5m-5-5v12"
          />
        </svg>
      );
    }
    return (
      <svg
        className="h-5 w-5 text-red-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 13l-5 5m0 0l-5-5m5 5V6"
        />
      </svg>
    );
  };

  // Skeleton Loader
  if (loading) {
    return (
      <Card>
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  // Keine Daten vorhanden
  if (!data || data.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="text-center py-12 text-gray-500">
          <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
            {getIcon()}
          </div>
          <p className="text-sm">Keine Daten verfügbar</p>
          <p className="text-xs text-gray-400 mt-1">
            Ändere den Zeitraum oder lade Transaktionen hoch
          </p>
        </div>
      </Card>
    );
  }

  // Berechne Gesamtsumme und -anzahl
  // Normalize data format (support both old and new API format)
  const normalizedData = data.map(item => ({
    name: item.name || item.recipient,
    value: item.value || item.total_amount,
    count: item.count || item.transaction_count,
  }));
  
  const total = normalizedData.reduce((sum, item) => sum + Math.abs(item.value), 0);
  const totalCount = normalizedData.reduce((sum, item) => sum + item.count, 0);

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <span className="text-sm text-gray-500">Top {data.length}</span>
      </div>

      {/* Tabelle */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Rang
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {type === 'sender' ? 'Absender' : 'Empfänger'}
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Betrag
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Transaktionen
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Durchschnitt
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Anteil
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {normalizedData.map((item, index) => {
              const average = Math.abs(item.value) / item.count;
              const percentage = (Math.abs(item.value) / total) * 100;

              return (
                <tr
                  key={index}
                  onClick={() => onRowClick && onRowClick(item)}
                  className={`
                    transition-colors
                    ${onRowClick ? 'hover:bg-gray-50 cursor-pointer' : ''}
                  `}
                >
                  {/* Rang mit Medal für Top 3 */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      {index === 0 && <span className="mr-1">🥇</span>}
                      {index === 1 && <span className="mr-1">🥈</span>}
                      {index === 2 && <span className="mr-1">🥉</span>}
                      <span className={index < 3 ? 'font-semibold' : ''}>
                        {index + 1}
                      </span>
                    </div>
                  </td>

                  {/* Name mit Icon */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="mr-3">{getIcon()}</div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {item.name || 'Unbekannt'}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Betrag */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className={`text-sm font-semibold ${
                      type === 'sender' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {new Intl.NumberFormat('de-DE', {
                        style: 'currency',
                        currency: currency,
                      }).format(Math.abs(item.value))}
                    </div>
                  </td>

                  {/* Transaktionen */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="text-sm text-gray-900">{item.count}×</div>
                  </td>

                  {/* Durchschnitt */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="text-sm text-gray-500">
                      {new Intl.NumberFormat('de-DE', {
                        style: 'currency',
                        currency: currency,
                      }).format(average)}
                    </div>
                  </td>

                  {/* Anteil mit Progress Bar */}
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end">
                      <span className="text-sm text-gray-900 mr-2">
                        {percentage.toFixed(1)}%
                      </span>
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            type === 'sender' ? 'bg-green-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>

          {/* Footer mit Gesamtsummen */}
          <tfoot className="bg-gray-50">
            <tr className="font-semibold">
              <td className="px-6 py-4 text-sm text-gray-900" colSpan="2">
                Gesamt
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="text-sm text-gray-900">
                  {new Intl.NumberFormat('de-DE', {
                    style: 'currency',
                    currency: currency,
                  }).format(total)}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="text-sm text-gray-900">{totalCount}×</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="text-sm text-gray-500">
                  {new Intl.NumberFormat('de-DE', {
                    style: 'currency',
                    currency: currency,
                  }).format(total / totalCount)}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="text-sm text-gray-900">100%</div>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

export default RecipientList;

/**
 * ERWEITERBARKEITS-GUIDE:
 * 
 * 1. Sortierung implementieren:
 *    const [sortBy, setSortBy] = useState('value');
 *    const [sortOrder, setSortOrder] = useState('desc');
 *    
 *    const sortedData = useMemo(() => {
 *      return [...data].sort((a, b) => {
 *        const order = sortOrder === 'asc' ? 1 : -1;
 *        return (a[sortBy] - b[sortBy]) * order;
 *      });
 *    }, [data, sortBy, sortOrder]);
 * 
 * 2. Pagination hinzufügen:
 *    const [page, setPage] = useState(1);
 *    const itemsPerPage = 10;
 *    const paginatedData = data.slice((page - 1) * itemsPerPage, page * itemsPerPage);
 * 
 * 3. Kategorie-Spalte:
 *    <th>Kategorie</th>
 *    <td>
 *      <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
 *        {item.category}
 *      </span>
 *    </td>
 * 
 * 4. Export-Funktion:
 *    <button onClick={() => exportToCsv(data, title)}>
 *      CSV Export
 *    </button>
 * 
 * 5. Letzte Transaktion anzeigen:
 *    <td className="text-xs text-gray-500">
 *      {format(new Date(item.lastTransaction), 'dd.MM.yyyy')}
 *    </td>
 */
