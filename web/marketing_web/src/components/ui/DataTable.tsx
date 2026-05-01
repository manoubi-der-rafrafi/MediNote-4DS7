import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

export interface DataTableColumn<T> {
  key: keyof T;
  label: string;
  render?: (value: any, row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T extends { id?: string | number }> {
  columns: DataTableColumn<T>[];
  data: T[];
  loading?: boolean;
  pageSize?: number;
  onRowClick?: (row: T) => void;
}

export const DataTable = React.forwardRef<HTMLDivElement, DataTableProps<any>>(
  ({ columns, data, loading = false, pageSize = 10, onRowClick }, ref) => {
    const [sortKey, setSortKey] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const [page, setPage] = useState(0);
    const [filter, setFilter] = useState('');

    const filteredData = useMemo(() => {
      return data.filter(row =>
        columns.some(col =>
          String(row[col.key])
            .toLowerCase()
            .includes(filter.toLowerCase())
        )
      );
    }, [data, filter, columns]);

    const sortedData = useMemo(() => {
      if (!sortKey) return filteredData;
      
      return [...filteredData].sort((a, b) => {
        const aVal = a[sortKey as keyof typeof a];
        const bVal = b[sortKey as keyof typeof b];
        
        if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }, [filteredData, sortKey, sortOrder]);

    const paginatedData = sortedData.slice(page * pageSize, (page + 1) * pageSize);
    const totalPages = Math.ceil(sortedData.length / pageSize);

    const handleSort = (key: string) => {
      setSortKey(key);
      setSortOrder(sortKey === key && sortOrder === 'asc' ? 'desc' : 'asc');
      setPage(0);
    };

    return (
      <div ref={ref} className="bg-s1 rounded-lg overflow-hidden border border-bd">
        {/* Search */}
        <div className="p-4 border-b border-bd">
          <input
            type="text"
            placeholder="Filtrer..."
            value={filter}
            onChange={e => {
              setFilter(e.target.value);
              setPage(0);
            }}
            className="w-full px-3 py-2 bg-s2 border border-bd rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-marketing"
          />
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-bd bg-s2">
                {columns.map(col => (
                  <th
                    key={String(col.key)}
                    onClick={() => col.sortable !== false && handleSort(String(col.key))}
                    className={`px-4 py-3 text-left text-xs font-semibold text-gray-400 ${
                      col.sortable !== false ? 'cursor-pointer hover:text-white' : ''
                    }`}
                    style={{ width: col.width }}
                  >
                    <div className="flex items-center gap-2">
                      {col.label}
                      {col.sortable !== false && sortKey === String(col.key) && (
                        <>
                          {sortOrder === 'asc' ? (
                            <ChevronUp size={14} />
                          ) : (
                            <ChevronDown size={14} />
                          )}
                        </>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-8 text-center">
                    <div className="flex justify-center items-center gap-2">
                      <div className="w-2 h-2 bg-marketing rounded-full animate-pulse" />
                      <span className="text-gray-400">Chargement...</span>
                    </div>
                  </td>
                </tr>
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-400">
                    Aucune donnée
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, idx) => (
                  <tr
                    key={row.id || idx}
                    onClick={() => onRowClick?.(row)}
                    className="border-b border-bd hover:bg-s2 transition-colors cursor-pointer"
                  >
                    {columns.map(col => (
                      <td key={String(col.key)} className="px-4 py-3 text-sm">
                        {col.render ? col.render(row[col.key], row) : String(row[col.key])}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-bd flex items-center justify-between text-sm text-gray-400">
            <span>
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage(p => Math.max(0, p - 1))}
                className="px-3 py-1 bg-s2 rounded hover:bg-s3 disabled:opacity-50"
              >
                ←
              </button>
              <button
                disabled={page === totalPages - 1}
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                className="px-3 py-1 bg-s2 rounded hover:bg-s3 disabled:opacity-50"
              >
                →
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }
);

DataTable.displayName = 'DataTable';
