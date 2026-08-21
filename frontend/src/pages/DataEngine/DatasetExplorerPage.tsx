import React, { useEffect, useState } from 'react';
import { datasetService } from '../../services/datasets';
import { DatasetMetadata, DatasetDomain } from '../../types/dataset';
import { DatasetTable } from '../../components/data/DatasetTable';
import { Search, Filter, RefreshCw } from 'lucide-react';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';

export const DatasetExplorerPage: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [search, setSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchDatasets = async () => {
    setIsLoading(true);
    try {
      const data = await datasetService.getDatasets({
        domain: selectedDomain !== 'all' ? (selectedDomain as DatasetDomain) : undefined,
        search: search || undefined
      });
      setDatasets(data);
    } catch (err) {
      console.error('Failed to load datasets', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [selectedDomain, search]);

  const domainOptions = [
    { id: 'all', label: 'All Scientific Domains' },
    { id: 'molecular_edna', label: 'Molecular eDNA' },
    { id: 'biodiversity', label: 'Species & Biodiversity' },
    { id: 'oceanography', label: 'Oceanography (CTD)' },
    { id: 'fisheries', label: 'Commercial Fisheries' }
  ];

  return (
    <div className="space-y-4">
      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search datasets by keyword, vessel, gene marker, or tag..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-marine-900 border border-marine-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-ocean-cyan font-mono"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="bg-marine-900 border border-marine-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-ocean-cyan"
          >
            {domainOptions.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>

          <Button
            size="sm"
            variant="ghost"
            onClick={fetchDatasets}
            title="Refresh datasets"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Dataset Table or Skeletons */}
      {isLoading ? (
        <CardSkeleton rows={5} />
      ) : datasets.length === 0 ? (
        <EmptyState
          title="No Datasets Found"
          description="Try broadening your search term or selecting a different scientific domain."
          actionLabel="Reset Filters"
          onAction={() => {
            setSearch('');
            setSelectedDomain('all');
          }}
        />
      ) : (
        <DatasetTable datasets={datasets} />
      )}
    </div>
  );
};
