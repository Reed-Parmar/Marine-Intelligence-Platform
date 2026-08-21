import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs } from '../../components/ui/Tabs';
import { DatasetExplorerPage } from './DatasetExplorerPage';
import { DatasetUploadPage } from './DatasetUploadPage';
import { Database, Upload, ListFilter } from 'lucide-react';

export const DataEnginePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'explorer' | 'upload'>('explorer');

  const tabs = [
    { id: 'explorer', label: 'Dataset Explorer', icon: <ListFilter className="w-4 h-4" /> },
    { id: 'upload', label: 'Ingest Dataset (TXT/CTD/CSV)', icon: <Upload className="w-4 h-4" /> }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-ocean-cyan" />
            CMLRE Data Engine & Ingestion Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse registered marine data or upload raw TXT, CTD casts, and Darwin Core standard files.
          </p>
        </div>

        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onChange={(id) => setActiveTab(id as 'explorer' | 'upload')}
        />
      </div>

      {/* Tab Content */}
      {activeTab === 'explorer' ? <DatasetExplorerPage /> : <DatasetUploadPage />}
    </div>
  );
};
