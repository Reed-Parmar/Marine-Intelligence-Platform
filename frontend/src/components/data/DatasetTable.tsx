import React from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetMetadata } from '../../types/dataset';
import { Badge } from '../ui/Badge';
import { QualityScoreBadge } from './QualityScoreBadge';
import { Eye, HardDrive, Calendar, MapPin, Tag } from 'lucide-react';
import { Button } from '../ui/Button';

export interface DatasetTableProps {
  datasets: DatasetMetadata[];
  onSelectDataset?: (dataset: DatasetMetadata) => void;
}

export const DatasetTable: React.FC<DatasetTableProps> = ({ datasets }) => {
  const navigate = useNavigate();

  const getDomainBadge = (domain: string) => {
    switch (domain) {
      case 'molecular_edna':
        return <Badge variant="purple" size="sm">Molecular eDNA</Badge>;
      case 'biodiversity':
        return <Badge variant="teal" size="sm">Biodiversity</Badge>;
      case 'oceanography':
        return <Badge variant="cyan" size="sm">Oceanography</Badge>;
      case 'fisheries':
        return <Badge variant="amber" size="sm">Fisheries</Badge>;
      default:
        return <Badge variant="blue" size="sm">{domain}</Badge>;
    }
  };

  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-marine-800">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-marine-800 bg-marine-900/80 text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
              <th className="py-3.5 px-4">Dataset Name & Source</th>
              <th className="py-3.5 px-4">Domain</th>
              <th className="py-3.5 px-4">Format</th>
              <th className="py-3.5 px-4">QC Score</th>
              <th className="py-3.5 px-4">Records</th>
              <th className="py-3.5 px-4">Region</th>
              <th className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-marine-850 text-xs">
            {datasets.map((dataset) => (
              <tr
                key={dataset.id}
                className="hover:bg-marine-900/60 transition-colors group cursor-pointer"
                onClick={() => navigate(`/data/datasets/${dataset.id}`)}
              >
                {/* Name & Source */}
                <td className="py-4 px-4 max-w-xs">
                  <p className="font-semibold text-white group-hover:text-ocean-cyan transition-colors truncate">
                    {dataset.title}
                  </p>
                  <p className="text-[11px] text-slate-400 truncate mt-0.5">{dataset.source}</p>
                </td>

                {/* Domain */}
                <td className="py-4 px-4 whitespace-nowrap">
                  {getDomainBadge(dataset.domain)}
                </td>

                {/* Format */}
                <td className="py-4 px-4 whitespace-nowrap">
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300 font-bold">
                    {dataset.format}
                  </span>
                </td>

                {/* Quality Score */}
                <td className="py-4 px-4 whitespace-nowrap">
                  <QualityScoreBadge score={dataset.qualityScore} status={dataset.qualityStatus} size="sm" />
                </td>

                {/* Record Count */}
                <td className="py-4 px-4 whitespace-nowrap font-mono text-slate-300">
                  {dataset.rowCount.toLocaleString()}
                </td>

                {/* Region */}
                <td className="py-4 px-4 whitespace-nowrap text-slate-300">
                  <div className="flex items-center gap-1.5 truncate max-w-[140px]">
                    <MapPin className="w-3 h-3 text-ocean-cyan flex-shrink-0" />
                    <span className="truncate">{dataset.region}</span>
                  </div>
                </td>

                {/* Actions */}
                <td className="py-4 px-4 text-right whitespace-nowrap">
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Eye className="w-3.5 h-3.5" />}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/data/datasets/${dataset.id}`);
                    }}
                  >
                    Inspect
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
