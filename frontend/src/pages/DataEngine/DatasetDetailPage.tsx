import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { datasetService } from '../../services/datasets';
import { 
  DatasetMetadata, 
  DatasetQualityReport, 
  DatasetProvenance, 
  DatasetPreviewData 
} from '../../types/dataset';
import { Tabs } from '../../components/ui/Tabs';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { QualityScoreBadge } from '../../components/data/QualityScoreBadge';
import { DatasetPreviewTable } from '../../components/data/DatasetPreviewTable';
import { ProvenancePanel } from '../../components/data/ProvenancePanel';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { 
  ArrowLeft, 
  Database, 
  Table, 
  ShieldCheck, 
  GitBranch, 
  MapPin, 
  Calendar, 
  HardDrive, 
  User, 
  Tag, 
  CheckCircle2, 
  AlertTriangle,
  Layers
} from 'lucide-react';

export const DatasetDetailPage: React.FC = () => {
  const { datasetId = 'ds-cmlre-txt-01' } = useParams<{ datasetId: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'overview' | 'preview' | 'quality' | 'provenance'>('overview');
  const [dataset, setDataset] = useState<DatasetMetadata | null>(null);
  const [quality, setQuality] = useState<DatasetQualityReport | null>(null);
  const [provenance, setProvenance] = useState<DatasetProvenance | null>(null);
  const [preview, setPreview] = useState<DatasetPreviewData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadAllDetails = async () => {
      setIsLoading(true);
      try {
        const [dsRes, qRes, provRes, prevRes] = await Promise.allSettled([
          datasetService.getDatasetById(datasetId),
          datasetService.getDatasetQuality(datasetId),
          datasetService.getDatasetProvenance(datasetId),
          datasetService.getDatasetPreview(datasetId)
        ]);

        if (dsRes.status === 'fulfilled') {
          setDataset(dsRes.value);
        }
        if (qRes.status === 'fulfilled') {
          setQuality(qRes.value);
        }
        if (provRes.status === 'fulfilled') {
          setProvenance(provRes.value);
        }
        if (prevRes.status === 'fulfilled') {
          setPreview(prevRes.value);
        }
      } catch (err) {
        console.error('Failed to load dataset details', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadAllDetails();
  }, [datasetId]);

  if (isLoading || !dataset) {
    return (
      <div className="space-y-6">
        <CardSkeleton rows={6} />
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Dataset Overview', icon: <Database className="w-4 h-4" /> },
    { id: 'preview', label: 'Data Preview', icon: <Table className="w-4 h-4" />, badge: `${preview?.rows.length || 0} rows` },
    { id: 'quality', label: 'Quality & QC Report', icon: <ShieldCheck className="w-4 h-4" />, badge: `${quality?.score}%` },
    { id: 'provenance', label: 'Lineage & Provenance', icon: <GitBranch className="w-4 h-4" /> }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Back Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate('/data')}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to Datasets
          </Button>
          <div className="h-4 w-[1px] bg-marine-800 hidden sm:block" />
          <span className="font-mono text-xs text-ocean-cyan font-bold">{dataset.id}</span>
        </div>

        <div className="flex items-center gap-3">
          <QualityScoreBadge score={dataset.qualityScore} status={dataset.qualityStatus} />
          <Button
            size="sm"
            variant="glow"
            onClick={() => navigate('/map')}
            leftIcon={<Layers className="w-3.5 h-3.5" />}
          >
            Locate on Marine Map
          </Button>
        </div>
      </div>

      {/* Dataset Title Block */}
      <div className="glass-panel rounded-2xl p-6 border border-marine-800 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="purple" size="sm">{dataset.domain.replace('_', ' ').toUpperCase()}</Badge>
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-marine-950 border border-marine-700 text-slate-300 font-bold">
            {dataset.format}
          </span>
          <span className="text-xs text-slate-400 font-mono">• Ingested on {new Date(dataset.createdAt).toLocaleDateString()}</span>
        </div>

        <h2 className="text-xl font-bold text-white tracking-tight">{dataset.title}</h2>
        <p className="text-xs text-slate-300 leading-relaxed max-w-4xl">{dataset.description}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as any)}
      />

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-up">
          {/* Metadata Grid */}
          <div className="md:col-span-2 space-y-6">
            <Card className="space-y-4">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Scientific Metadata & Spatial Bounding Box
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
                <div className="p-3 rounded-xl bg-marine-900/80 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">Total Records:</span>
                  <span className="text-white font-bold text-sm">{dataset.rowCount.toLocaleString()}</span>
                </div>
                <div className="p-3 rounded-xl bg-marine-900/80 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">File Size:</span>
                  <span className="text-white font-bold text-sm">{(dataset.fileSizeBytes / (1024 * 1024)).toFixed(2)} MB</span>
                </div>
                <div className="p-3 rounded-xl bg-marine-900/80 border border-marine-850">
                  <span className="text-[10px] text-slate-400 block font-sans">Sampling Platform:</span>
                  <span className="text-ocean-cyan font-bold truncate block">{dataset.source}</span>
                </div>
              </div>

              {/* Spatial Bounds Box */}
              {dataset.spatialBounds && (
                <div className="p-4 rounded-xl bg-marine-950/80 border border-marine-800 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-ocean-teal">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>PostGIS Bounding Box Coordinates (EPSG:4326)</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono text-slate-200">
                    <div><span className="text-slate-400">Min Lat: </span>{dataset.spatialBounds.minLat}°N</div>
                    <div><span className="text-slate-400">Max Lat: </span>{dataset.spatialBounds.maxLat}°N</div>
                    <div><span className="text-slate-400">Min Lon: </span>{dataset.spatialBounds.minLon}°E</div>
                    <div><span className="text-slate-400">Max Lon: </span>{dataset.spatialBounds.maxLon}°E</div>
                  </div>
                </div>
              )}

              {/* Tags */}
              <div className="space-y-2 pt-2 border-t border-marine-800">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-slate-400" />
                  Taxonomic & Standard Tags
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {dataset.tags.map((t, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-md bg-marine-900 border border-marine-700 text-xs font-mono text-ocean-cyan">
                      #{t}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          </div>

          {/* Right Sidebar: Collection & Temporal Window */}
          <div className="space-y-4">
            <Card className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Sampling Timeframe
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-marine-850 pb-2">
                  <span className="text-slate-400">Start Date:</span>
                  <span className="font-mono text-white font-semibold">{dataset.temporalCoverage.start}</span>
                </div>
                <div className="flex items-center justify-between border-b border-marine-850 pb-2">
                  <span className="text-slate-400">End Date:</span>
                  <span className="font-mono text-white font-semibold">{dataset.temporalCoverage.end}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Curator:</span>
                  <span className="text-slate-200">{dataset.uploadedBy}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Tabular Preview */}
      {activeTab === 'preview' && preview && (
        <div className="animate-slide-up">
          <DatasetPreviewTable previewData={preview} />
        </div>
      )}

      {/* Tab 3: Quality Report */}
      {activeTab === 'quality' && quality && (
        <div className="space-y-6 animate-slide-up">
          <Card className="space-y-4">
            <div className="flex items-center justify-between border-b border-marine-800 pb-3">
              <h3 className="text-sm font-semibold text-white">Quality Control & Validation Breakdown</h3>
              <span className="text-xs font-mono text-slate-400">Computed: {new Date(quality.computedAt).toLocaleString()}</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-marine-900 border border-marine-850">
                <span className="text-[10px] text-slate-400 block font-sans">Valid Rows:</span>
                <span className="text-emerald-400 font-bold text-sm">{quality.validRows.toLocaleString()}</span>
              </div>
              <div className="p-3 rounded-xl bg-marine-900 border border-marine-850">
                <span className="text-[10px] text-slate-400 block font-sans">Flagged Rows:</span>
                <span className="text-ocean-amber font-bold text-sm">{quality.flaggedRows.toLocaleString()}</span>
              </div>
              <div className="p-3 rounded-xl bg-marine-900 border border-marine-850">
                <span className="text-[10px] text-slate-400 block font-sans">Duplicates Removed:</span>
                <span className="text-white font-bold text-sm">{quality.duplicateCount}</span>
              </div>
              <div className="p-3 rounded-xl bg-marine-900 border border-marine-850">
                <span className="text-[10px] text-slate-400 block font-sans">Missing Value Ratio:</span>
                <span className="text-ocean-cyan font-bold text-sm">{(quality.missingValueRatio * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Validation Issues Log */}
            <div className="space-y-2 pt-2">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Automated Validation Issues Log
              </h4>
              {quality.issues.map((iss) => (
                <div
                  key={iss.id}
                  className="p-3 rounded-xl bg-marine-900/60 border border-marine-800 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase font-bold text-ocean-amber">[{iss.category}]</span>
                      <p className="text-slate-200">{iss.message}</p>
                    </div>
                    {iss.recommendation && (
                      <p className="text-[11px] text-slate-400 pl-4 border-l border-ocean-cyan/40">
                        <span className="text-ocean-cyan font-semibold">Recommendation: </span>
                        {iss.recommendation}
                      </p>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 whitespace-nowrap">
                    {iss.affectedRowsCount} rows
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Tab 4: Provenance */}
      {activeTab === 'provenance' && provenance && (
        <div className="animate-slide-up">
          <ProvenancePanel provenance={provenance} />
        </div>
      )}
    </div>
  );
};
