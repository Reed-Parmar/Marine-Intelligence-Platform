import React, { useState } from 'react';
import { DatasetPreviewData } from '../../types/dataset';
import { Search, Hash, Calendar, MapPin, Type } from 'lucide-react';

export interface DatasetPreviewTableProps {
  previewData: DatasetPreviewData;
}

export const DatasetPreviewTable: React.FC<DatasetPreviewTableProps> = ({ previewData }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredRows = previewData.rows.filter((row) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return Object.values(row).some((val) =>
      String(val).toLowerCase().includes(term)
    );
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'number':
        return <Hash className="w-3 h-3 text-ocean-cyan" />;
      case 'date':
        return <Calendar className="w-3 h-3 text-ocean-amber" />;
      case 'geo':
        return <MapPin className="w-3 h-3 text-ocean-teal" />;
      default:
        return <Type className="w-3 h-3 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Table Search & Record Count */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative max-w-xs w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search within preview records..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-marine-900 border border-marine-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan"
          />
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Showing {filteredRows.length} of {previewData.rows.length} preview rows
        </div>
      </div>

      {/* Scrollable Data Table */}
      <div className="glass-panel rounded-xl overflow-hidden border border-marine-800">
        <div className="overflow-x-auto max-h-96 custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 z-10 bg-marine-900 border-b border-marine-800 shadow-sm">
              <tr className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                {previewData.columns.map((col) => (
                  <th key={col.name} className="py-3 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 font-mono">
                      {getTypeIcon(col.type)}
                      <span>{col.name}</span>
                      {col.unit && (
                        <span className="text-[10px] text-ocean-cyan font-normal lowercase">
                          ({col.unit})
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-marine-850 text-xs font-mono">
              {filteredRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-marine-900/50 transition-colors">
                  {previewData.columns.map((col) => {
                    const value = row[col.name];
                    return (
                      <td key={col.name} className="py-2.5 px-4 whitespace-nowrap text-slate-200">
                        {value !== undefined && value !== null ? String(value) : (
                          <span className="text-slate-600 italic">null</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
