import { DatasetMetadata, DatasetQualityReport, DatasetProvenance, DatasetPreviewData } from '../types/dataset';
import { MarineObservation, MarineSummary, CrossDomainLocationDetail } from '../types/marine';
import { OceanObservation, OceanTrendPoint, OceanSummaryMetrics } from '../types/ocean';
import { FisheriesObservation, FisheriesTrendPoint, FisheriesSummaryMetrics } from '../types/fisheries';
import { SpeciesRecord, SpeciesOccurrence } from '../types/species';
import { EDNASample, EDNADetection } from '../types/edna';
import { AnalysisResultData } from '../types/analysis';
import { MLModelInfo, AnomalyDetectionResult, HabitatSuitabilityResult, CatchForecastResult } from '../types/ml';
import { MarineAlert, AlertSummaryMetrics } from '../types/alert';
import { UserProfile } from '../types/auth';

// ----------------------------------------------------
// Mock Authenticated Profiles
// ----------------------------------------------------
export const MOCK_USERS: Record<string, UserProfile> = {
  scientist: {
    id: 'usr-cmlre-01',
    email: 'scientist@cmlre.gov.in',
    fullName: 'Dr. Ananya Nair',
    role: 'user',
    institution: 'Centre for Marine Living Resources & Ecology (CMLRE)',
    department: 'Fisheries Oceanography & Biodiversity Division',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    lastLogin: '2026-08-21T10:30:00Z',
    createdAt: '2025-01-15T08:00:00Z',
  },
  admin: {
    id: 'usr-cmlre-admin',
    email: 'admin@cmlre.gov.in',
    fullName: 'Chief Scientist S. Raghavan',
    role: 'admin',
    institution: 'Ministry of Earth Sciences (MoES)',
    department: 'Data Platform Operations & Governance',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    lastLogin: '2026-08-21T11:45:00Z',
    createdAt: '2024-11-01T08:00:00Z',
  }
};

// ----------------------------------------------------
// Mock Datasets (Includes real CMLRE filenames)
// ----------------------------------------------------
export const MOCK_DATASETS: DatasetMetadata[] = [
  {
    id: 'ds-cmlre-txt-01',
    title: 'CMLRE Molecular eDNA Profiling - Arabian Sea (dnaderiveddata1.txt)',
    description: 'High-throughput environmental DNA marker gene sequencing records targeting marine teleosts and invertebrates across South-Eastern Arabian Sea.',
    domain: 'molecular_edna',
    format: 'TXT',
    status: 'completed',
    qualityStatus: 'excellent',
    qualityScore: 97,
    rowCount: 3840,
    fileSizeBytes: 2458900,
    source: 'FORV Sagar Sampada Cruise 412',
    region: 'Arabian Sea',
    spatialBounds: { minLat: 8.4, maxLat: 15.2, minLon: 71.5, maxLon: 76.8, depthRange: [5, 450] },
    temporalCoverage: { start: '2025-02-10', end: '2025-06-25' },
    tags: ['eDNA', '12S rRNA', 'COI', 'Metabarcoding', 'Teleost'],
    createdAt: '2026-08-15T09:20:00Z',
    updatedAt: '2026-08-15T09:25:00Z',
    uploadedBy: 'Dr. Ananya Nair'
  },
  {
    id: 'ds-cmlre-txt-02',
    title: 'Marine Species Occurrence & Taxonomy Records (occurrence.txt)',
    description: 'Darwin Core standard occurrence data containing benthic, demersal and pelagic species surveys along the Indian EEZ and Lakshadweep Archipelago.',
    domain: 'biodiversity',
    format: 'TXT',
    status: 'completed',
    qualityStatus: 'good',
    qualityScore: 93,
    rowCount: 12450,
    fileSizeBytes: 5820400,
    source: 'CMLRE Biodiversity Monitoring Program',
    region: 'Lakshadweep & Malabar Coast',
    spatialBounds: { minLat: 7.8, maxLat: 16.5, minLon: 70.0, maxLon: 77.5, depthRange: [0, 1200] },
    temporalCoverage: { start: '2024-01-05', end: '2025-11-30' },
    tags: ['DarwinCore', 'WoRMS', 'Taxonomy', 'Occurrence', 'Biodiversity'],
    createdAt: '2026-08-12T14:10:00Z',
    updatedAt: '2026-08-12T14:18:00Z',
    uploadedBy: 'Chief Scientist S. Raghavan'
  },
  {
    id: 'ds-cmlre-ctd-03',
    title: 'CTD Oceanographic Hydrographic Profiles - Bay of Bengal Sector',
    description: 'Conductivity-Temperature-Depth vertical cast observations recording water column thermal stratification, salinity gradients, and dissolved oxygen minimum zones.',
    domain: 'oceanography',
    format: 'CTD',
    status: 'completed',
    qualityStatus: 'excellent',
    qualityScore: 98,
    rowCount: 85200,
    fileSizeBytes: 14200000,
    source: 'MoES Ocean Observation Network',
    region: 'Bay of Bengal',
    spatialBounds: { minLat: 11.0, maxLat: 19.5, minLon: 80.5, maxLon: 89.2, depthRange: [0, 2000] },
    temporalCoverage: { start: '2025-05-01', end: '2025-10-15' },
    tags: ['CTD', 'SST', 'Salinity', 'Dissolved Oxygen', 'OMZ'],
    createdAt: '2026-08-10T11:00:00Z',
    updatedAt: '2026-08-10T11:15:00Z',
    uploadedBy: 'Dr. Ananya Nair'
  },
  {
    id: 'ds-cmlre-csv-04',
    title: 'Pelagic Commercial Catch & CPUE Time-Series (2023-2025)',
    description: 'Harbor landings, Catch Per Unit Effort (CPUE), mechanized trawler logs, and pelagic stock estimates for Indian Mackerel, Sardine, and Yellowfin Tuna.',
    domain: 'fisheries',
    format: 'CSV',
    status: 'completed',
    qualityStatus: 'good',
    qualityScore: 91,
    rowCount: 41200,
    fileSizeBytes: 8910000,
    source: 'National Marine Fisheries Census / CMLRE',
    region: 'Indian EEZ (West & East Coasts)',
    spatialBounds: { minLat: 8.0, maxLat: 21.0, minLon: 69.5, maxLon: 88.5, depthRange: [10, 250] },
    temporalCoverage: { start: '2023-01-01', end: '2025-12-31' },
    tags: ['Fisheries', 'CPUE', 'Pelagic', 'Trawling', 'Stock Assessment'],
    createdAt: '2026-08-08T16:40:00Z',
    updatedAt: '2026-08-08T16:48:00Z',
    uploadedBy: 'Dr. Ananya Nair'
  }
];

// ----------------------------------------------------
// Mock Dataset Quality Reports
// ----------------------------------------------------
export const MOCK_QUALITY_REPORTS: Record<string, DatasetQualityReport> = {
  'ds-cmlre-txt-01': {
    datasetId: 'ds-cmlre-txt-01',
    score: 97,
    status: 'excellent',
    totalRows: 3840,
    validRows: 3798,
    flaggedRows: 42,
    duplicateCount: 3,
    missingValueRatio: 0.012,
    spatialCompleteness: 99.4,
    temporalCompleteness: 100.0,
    issues: [
      {
        id: 'iss-01',
        type: 'info',
        category: 'schema',
        message: 'Non-standard header preamble detected in TXT; automatically stripped 14 comment lines during ingestion.',
        affectedRowsCount: 14
      },
      {
        id: 'iss-02',
        type: 'warning',
        category: 'missing_values',
        message: 'Target primer read count missing in 28 low-depth station records; defaulted to zero abundance.',
        affectedRowsCount: 28,
        recommendation: 'Verify if PCR amplification failed at stations 412-A04 and 412-B02.'
      }
    ],
    computedAt: '2026-08-15T09:24:12Z'
  },
  'ds-cmlre-txt-02': {
    datasetId: 'ds-cmlre-txt-02',
    score: 93,
    status: 'good',
    totalRows: 12450,
    validRows: 11980,
    flaggedRows: 470,
    duplicateCount: 12,
    missingValueRatio: 0.038,
    spatialCompleteness: 96.8,
    temporalCompleteness: 98.5,
    issues: [
      {
        id: 'iss-03',
        type: 'warning',
        category: 'coordinates',
        message: '18 records had inverted lat/lon coordinates; automatically corrected to Indian Ocean bounding box.',
        affectedRowsCount: 18
      },
      {
        id: 'iss-04',
        type: 'warning',
        category: 'units',
        message: 'Depth given in fathoms in 142 records; converted to standard meters (m).',
        affectedRowsCount: 142
      }
    ],
    computedAt: '2026-08-12T14:16:45Z'
  }
};

// ----------------------------------------------------
// Mock Dataset Provenance
// ----------------------------------------------------
export const MOCK_PROVENANCE: Record<string, DatasetProvenance> = {
  'ds-cmlre-txt-01': {
    datasetId: 'ds-cmlre-txt-01',
    originalFileName: 'dnaderiveddata1.txt',
    fileHashSha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    sourceInstitution: 'Centre for Marine Living Resources & Ecology (CMLRE), Kochi',
    vesselCruiseId: 'FORV Sagar Sampada Cruise 412',
    dataCollector: 'Molecular Biology Team / Marine Genomics Lab',
    uploadedBy: 'Dr. Ananya Nair',
    uploadedAt: '2026-08-15T09:20:00Z',
    ingestionPipelineVersion: 'CMLRE-Ingest-v2.4.1-FastAPI',
    standardizationRulesApplied: [
      'TXT Preamble Strip & Tab Delimiter Normalization',
      'NCBI/MIFish Taxonomic Identifier Mapping',
      'WGS84 EPSG:4326 PostGIS Geometry Construction',
      'Darwin Core DNA_derived_data Extension Standard'
    ],
    storagePath: 'supabase-storage://cmlre-datasets/molecular/2026/dnaderiveddata1.txt',
    lineageNotes: 'Calibrated with negative extraction controls on Illumina NovaSeq 6000 paired-end reads.'
  },
  'ds-cmlre-txt-02': {
    datasetId: 'ds-cmlre-txt-02',
    originalFileName: 'occurrence.txt',
    fileHashSha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    sourceInstitution: 'Centre for Marine Living Resources & Ecology (CMLRE), Kochi',
    vesselCruiseId: 'FORV Sagar Sampada Surveys 2024-2025',
    dataCollector: 'Marine Biodiversity & Fishery Biology Group',
    uploadedBy: 'Chief Scientist S. Raghavan',
    uploadedAt: '2026-08-12T14:10:00Z',
    ingestionPipelineVersion: 'CMLRE-Ingest-v2.4.1-FastAPI',
    standardizationRulesApplied: [
      'WoRMS AphiaID Match & Synonym Resolution',
      'Coordinate Precision Rounding & Bounding Check',
      'ISO 8601 Temporal Timestamp Conversion'
    ],
    storagePath: 'supabase-storage://cmlre-datasets/biodiversity/2026/occurrence.txt',
    lineageNotes: 'Curated by senior taxonomists; verified against OBIS India node.'
  }
};

// ----------------------------------------------------
// Mock Dataset Preview Rows (Real CMLRE Schema Columns)
// ----------------------------------------------------
export const MOCK_PREVIEW_DATA: Record<string, DatasetPreviewData> = {
  'ds-cmlre-txt-01': {
    datasetId: 'ds-cmlre-txt-01',
    totalPreviewRows: 10,
    columns: [
      { name: 'sample_id', type: 'string' },
      { name: 'event_date', type: 'date' },
      { name: 'decimal_latitude', type: 'geo', unit: '°N' },
      { name: 'decimal_longitude', type: 'geo', unit: '°E' },
      { name: 'sampling_depth', type: 'number', unit: 'm' },
      { name: 'target_gene', type: 'string' },
      { name: 'scientific_name', type: 'string' },
      { name: 'read_count', type: 'number' },
      { name: 'match_percent', type: 'number', unit: '%' },
      { name: 'confidence_score', type: 'number' }
    ],
    rows: [
      { sample_id: 'CMLRE-EDNA-01', event_date: '2025-03-12', decimal_latitude: 9.94, decimal_longitude: 75.82, sampling_depth: 25, target_gene: '12S rRNA', scientific_name: 'Rastrelliger kanagurta', read_count: 1420, match_percent: 99.8, confidence_score: 0.99 },
      { sample_id: 'CMLRE-EDNA-02', event_date: '2025-03-12', decimal_latitude: 9.94, decimal_longitude: 75.82, sampling_depth: 75, target_gene: '12S rRNA', scientific_name: 'Sardinella longiceps', read_count: 3890, match_percent: 99.4, confidence_score: 0.98 },
      { sample_id: 'CMLRE-EDNA-03', event_date: '2025-03-14', decimal_latitude: 11.25, decimal_longitude: 74.90, sampling_depth: 50, target_gene: 'COI', scientific_name: 'Thunnus albacares', read_count: 650, match_percent: 98.9, confidence_score: 0.97 },
      { sample_id: 'CMLRE-EDNA-04', event_date: '2025-03-15', decimal_latitude: 12.87, decimal_longitude: 74.20, sampling_depth: 10, target_gene: '16S rRNA', scientific_name: 'Epinephelus coioides', read_count: 210, match_percent: 97.6, confidence_score: 0.94 },
      { sample_id: 'CMLRE-EDNA-05', event_date: '2025-03-16', decimal_latitude: 14.80, decimal_longitude: 73.50, sampling_depth: 150, target_gene: '12S rRNA', scientific_name: 'Nemipterus japonicus', read_count: 1840, match_percent: 99.2, confidence_score: 0.98 },
      { sample_id: 'CMLRE-EDNA-06', event_date: '2025-03-18', decimal_latitude: 10.05, decimal_longitude: 72.10, sampling_depth: 30, target_gene: 'COI', scientific_name: 'Coryphaena hippurus', read_count: 920, match_percent: 99.1, confidence_score: 0.98 }
    ]
  },
  'ds-cmlre-txt-02': {
    datasetId: 'ds-cmlre-txt-02',
    totalPreviewRows: 10,
    columns: [
      { name: 'occurrence_id', type: 'string' },
      { name: 'event_date', type: 'date' },
      { name: 'scientific_name', type: 'string' },
      { name: 'taxonomic_class', type: 'string' },
      { name: 'latitude', type: 'geo', unit: '°N' },
      { name: 'longitude', type: 'geo', unit: '°E' },
      { name: 'depth_meters', type: 'number', unit: 'm' },
      { name: 'individual_count', type: 'number' },
      { name: 'basis_of_record', type: 'string' }
    ],
    rows: [
      { occurrence_id: 'OCC-CMLRE-8910', event_date: '2024-11-04', scientific_name: 'Rastrelliger kanagurta', taxonomic_class: 'Actinopterygii', latitude: 9.85, longitude: 75.92, depth_meters: 18, individual_count: 120, basis_of_record: 'HumanObservation' },
      { occurrence_id: 'OCC-CMLRE-8911', event_date: '2024-11-05', scientific_name: 'Sardinella longiceps', taxonomic_class: 'Actinopterygii', latitude: 10.42, longitude: 75.40, depth_meters: 25, individual_count: 450, basis_of_record: 'PreservedSpecimen' },
      { occurrence_id: 'OCC-CMLRE-8912', event_date: '2024-11-08', scientific_name: 'Penaeus monodon', taxonomic_class: 'Malacostraca', latitude: 11.80, longitude: 74.85, depth_meters: 40, individual_count: 65, basis_of_record: 'HumanObservation' },
      { occurrence_id: 'OCC-CMLRE-8913', event_date: '2024-11-12', scientific_name: 'Thunnus albacares', taxonomic_class: 'Actinopterygii', latitude: 13.50, longitude: 73.10, depth_meters: 110, individual_count: 8, basis_of_record: 'HumanObservation' },
      { occurrence_id: 'OCC-CMLRE-8914', event_date: '2024-11-15', scientific_name: 'Epinephelus coioides', taxonomic_class: 'Actinopterygii', latitude: 8.50, longitude: 76.80, depth_meters: 55, individual_count: 14, basis_of_record: 'PreservedSpecimen' }
    ]
  }
};

// ----------------------------------------------------
// Mock Unified Marine Observations (Cross-Domain Fusion)
// ----------------------------------------------------
export const MOCK_MARINE_OBSERVATIONS: MarineObservation[] = [
  {
    id: 'mob-01',
    datasetId: 'ds-cmlre-ctd-03',
    domain: 'oceanography',
    timestamp: '2026-08-18T06:30:00Z',
    latitude: 9.95,
    longitude: 75.80,
    depthMeters: 10,
    stationId: 'CMLRE-STN-KOC-01',
    region: 'Arabian Sea',
    temperature: 28.6,
    salinity: 35.2,
    dissolvedOxygen: 4.8,
    chlorophyllA: 1.85,
    ph: 8.12,
    speciesName: 'Indian Mackerel (Rastrelliger kanagurta)',
    catchWeightKg: 850,
    fishingEffortHours: 6.5,
    ednaDetectionsCount: 4,
    anomalyFlag: false,
    riskLevel: 'low'
  },
  {
    id: 'mob-02',
    datasetId: 'ds-cmlre-ctd-03',
    domain: 'cross_domain',
    timestamp: '2026-08-18T08:15:00Z',
    latitude: 11.20,
    longitude: 75.10,
    depthMeters: 45,
    stationId: 'CMLRE-STN-CLT-04',
    region: 'Arabian Sea',
    temperature: 26.8,
    salinity: 35.8,
    dissolvedOxygen: 1.9, // Hypoxic layer
    chlorophyllA: 3.40,
    ph: 7.85,
    speciesName: 'Oil Sardine (Sardinella longiceps)',
    catchWeightKg: 1200,
    fishingEffortHours: 8.0,
    ednaDetectionsCount: 9,
    anomalyFlag: true,
    anomalyScore: 78,
    riskLevel: 'high'
  },
  {
    id: 'mob-03',
    datasetId: 'ds-cmlre-txt-01',
    domain: 'molecular_edna',
    timestamp: '2026-08-19T10:00:00Z',
    latitude: 10.55,
    longitude: 72.60,
    depthMeters: 20,
    stationId: 'CMLRE-STN-LAK-02',
    region: 'Lakshadweep',
    temperature: 29.4,
    salinity: 34.6,
    dissolvedOxygen: 5.2,
    chlorophyllA: 0.95,
    ph: 8.25,
    speciesName: 'Yellowfin Tuna (Thunnus albacares)',
    catchWeightKg: 420,
    fishingEffortHours: 4.0,
    ednaDetectionsCount: 14,
    ednaTargetMarker: '12S rRNA',
    ednaConfidenceScore: 0.99,
    anomalyFlag: false,
    riskLevel: 'low'
  },
  {
    id: 'mob-04',
    datasetId: 'ds-cmlre-csv-04',
    domain: 'fisheries',
    timestamp: '2026-08-19T14:45:00Z',
    latitude: 15.40,
    longitude: 73.60,
    depthMeters: 30,
    stationId: 'CMLRE-STN-GOA-06',
    region: 'Arabian Sea',
    temperature: 27.9,
    salinity: 35.4,
    dissolvedOxygen: 3.9,
    chlorophyllA: 2.10,
    speciesName: 'Orange-spotted Grouper (Epinephelus coioides)',
    catchWeightKg: 640,
    fishingEffortHours: 7.2,
    gearType: 'Trawl net',
    anomalyFlag: false,
    riskLevel: 'low'
  },
  {
    id: 'mob-05',
    datasetId: 'ds-cmlre-ctd-03',
    domain: 'oceanography',
    timestamp: '2026-08-20T04:20:00Z',
    latitude: 13.08,
    longitude: 80.35,
    depthMeters: 15,
    stationId: 'CMLRE-STN-CHE-01',
    region: 'Bay of Bengal',
    temperature: 29.8,
    salinity: 33.1,
    dissolvedOxygen: 4.5,
    chlorophyllA: 1.45,
    ph: 8.08,
    speciesName: 'Giant Tiger Prawn (Penaeus monodon)',
    catchWeightKg: 380,
    fishingEffortHours: 5.5,
    anomalyFlag: false,
    riskLevel: 'low'
  },
  {
    id: 'mob-06',
    datasetId: 'ds-cmlre-ctd-03',
    domain: 'cross_domain',
    timestamp: '2026-08-20T07:10:00Z',
    latitude: 17.65,
    longitude: 83.35,
    depthMeters: 60,
    stationId: 'CMLRE-STN-VIZ-03',
    region: 'Bay of Bengal',
    temperature: 27.2,
    salinity: 33.8,
    dissolvedOxygen: 1.4, // Severe hypoxia
    chlorophyllA: 4.10,
    speciesName: 'Skipjack Tuna (Katsuwonus pelamis)',
    catchWeightKg: 950,
    fishingEffortHours: 9.0,
    anomalyFlag: true,
    anomalyScore: 88,
    riskLevel: 'critical'
  },
  {
    id: 'mob-07',
    datasetId: 'ds-cmlre-txt-02',
    domain: 'biodiversity',
    timestamp: '2026-08-20T11:30:00Z',
    latitude: 11.62,
    longitude: 92.72,
    depthMeters: 25,
    stationId: 'CMLRE-STN-PBL-01',
    region: 'Andaman & Nicobar',
    temperature: 29.1,
    salinity: 33.5,
    dissolvedOxygen: 5.0,
    chlorophyllA: 0.88,
    speciesName: 'Humphead Wrasse (Cheilinus undulatus)',
    individualCount: 3,
    ednaDetectionsCount: 6,
    anomalyFlag: false,
    riskLevel: 'low'
  }
];

// ----------------------------------------------------
// Mock Location Cross-Domain Detail (for Map click)
// ----------------------------------------------------
export const MOCK_LOCATION_DETAIL: CrossDomainLocationDetail = {
  coordinates: { latitude: 9.94, longitude: 75.80 },
  region: 'South-Eastern Arabian Sea (Cochin Transect)',
  bathymetryDepth: 42.5,
  oceanography: {
    seaSurfaceTemperature: 28.6,
    salinity: 35.2,
    dissolvedOxygen: 4.8,
    chlorophyllA: 1.85,
    thermoclineDepth: 35.0,
    mixedLayerDepth: 18.0,
    lastUpdated: '2026-08-20T06:00:00Z'
  },
  fisheries: {
    dominantCatch: 'Rastrelliger kanagurta (Indian Mackerel)',
    totalLandingsTons: 142.8,
    cpueKgPerHour: 130.5,
    dominantGear: 'Ring seine & Mechanized Trawl',
    fishingPressureLevel: 'Moderate'
  },
  biodiversity: {
    speciesRecordedCount: 68,
    keySpeciesPresent: [
      'Rastrelliger kanagurta',
      'Sardinella longiceps',
      'Stolephorus commersonnii',
      'Epinephelus coioides'
    ],
    shannonWienerIndex: 3.42,
    endemicSpeciesFlag: false
  },
  molecularEdna: {
    samplesAnalyzed: 8,
    taxaIdentified: 24,
    topDetections: [
      { species: 'Rastrelliger kanagurta', confidence: 0.99, marker: '12S rRNA' },
      { species: 'Sardinella longiceps', confidence: 0.98, marker: '12S rRNA' },
      { species: 'Thunnus albacares', confidence: 0.94, marker: 'COI' }
    ]
  },
  aiPrediction: {
    anomalyDetected: false,
    riskScore: 24,
    habitatSuitabilityPercent: 88,
    recommendation: 'Optimal conditions for pelagic schooling fishes. Thermal and DO gradients within standard physiological tolerance bounds.'
  }
};

// ----------------------------------------------------
// Mock Ocean CTD Profiles & Trends
// ----------------------------------------------------
export const MOCK_OCEAN_SUMMARY: OceanSummaryMetrics = {
  meanSST: 28.5,
  minSST: 25.4,
  maxSST: 31.2,
  meanSalinity: 34.8,
  meanOxygen: 4.2,
  hypoxicAreaSqKm: 18450,
  activeSamplingStations: 38,
  totalCTDCasts: 1420
};

export const MOCK_CTD_DEPTH_CAST = [
  { depth: 0, temperature: 29.2, salinity: 34.5, dissolvedOxygen: 5.1, chlorophyllA: 1.2 },
  { depth: 10, temperature: 29.0, salinity: 34.6, dissolvedOxygen: 5.0, chlorophyllA: 2.4 },
  { depth: 25, temperature: 28.6, salinity: 34.8, dissolvedOxygen: 4.8, chlorophyllA: 3.8 }, // Subsurface Chlorophyll Max
  { depth: 50, temperature: 26.2, salinity: 35.3, dissolvedOxygen: 3.4, chlorophyllA: 1.5 },
  { depth: 75, temperature: 23.5, salinity: 35.6, dissolvedOxygen: 1.8, chlorophyllA: 0.6 },
  { depth: 100, temperature: 20.8, salinity: 35.8, dissolvedOxygen: 0.9, chlorophyllA: 0.2 }, // Oxygen Minimum Zone
  { depth: 150, temperature: 17.4, salinity: 35.7, dissolvedOxygen: 0.6, chlorophyllA: 0.05 },
  { depth: 200, temperature: 15.1, salinity: 35.5, dissolvedOxygen: 0.5, chlorophyllA: 0.01 },
  { depth: 300, temperature: 12.8, salinity: 35.3, dissolvedOxygen: 0.8, chlorophyllA: 0.0 },
  { depth: 500, temperature: 9.6, salinity: 35.1, dissolvedOxygen: 1.4, chlorophyllA: 0.0 }
];

export const MOCK_OCEAN_TRENDS: OceanTrendPoint[] = [
  { date: 'Jan 2025', avgSST: 27.8, avgSalinity: 34.6, avgOxygen: 5.2, avgChlorophyll: 1.1 },
  { date: 'Feb 2025', avgSST: 28.2, avgSalinity: 34.8, avgOxygen: 5.0, avgChlorophyll: 1.3 },
  { date: 'Mar 2025', avgSST: 29.1, avgSalinity: 35.1, avgOxygen: 4.7, avgChlorophyll: 1.6 },
  { date: 'Apr 2025', avgSST: 30.2, avgSalinity: 35.4, avgOxygen: 4.3, avgChlorophyll: 1.9 },
  { date: 'May 2025', avgSST: 30.9, avgSalinity: 35.5, avgOxygen: 4.0, avgChlorophyll: 2.4, anomalyFlag: true },
  { date: 'Jun 2025', avgSST: 28.5, avgSalinity: 34.2, avgOxygen: 3.6, avgChlorophyll: 3.8 }, // SW Monsoon upwelling
  { date: 'Jul 2025', avgSST: 27.2, avgSalinity: 33.8, avgOxygen: 3.1, avgChlorophyll: 4.5 },
  { date: 'Aug 2025', avgSST: 27.0, avgSalinity: 33.6, avgOxygen: 2.8, avgChlorophyll: 4.2 },
  { date: 'Sep 2025', avgSST: 27.8, avgSalinity: 34.0, avgOxygen: 3.4, avgChlorophyll: 3.2 },
  { date: 'Oct 2025', avgSST: 28.6, avgSalinity: 34.5, avgOxygen: 4.1, avgChlorophyll: 2.1 },
  { date: 'Nov 2025', avgSST: 28.9, avgSalinity: 34.7, avgOxygen: 4.8, avgChlorophyll: 1.5 },
  { date: 'Dec 2025', avgSST: 28.1, avgSalinity: 34.6, avgOxygen: 5.1, avgChlorophyll: 1.2 }
];

// ----------------------------------------------------
// Mock Fisheries Metrics & Trends
// ----------------------------------------------------
export const MOCK_FISHERIES_SUMMARY: FisheriesSummaryMetrics = {
  totalCatchAnnualTons: 384500,
  overallAvgCPUE: 142.6,
  activeVesselsTracked: 1820,
  dominantCatchGroup: 'Pelagic Teleosts (Mackerel & Sardine)',
  sustainabilityIndex: 78,
  topLandingHarbors: [
    { name: 'Kochi (Cochin Fisheries Harbour)', landingsTons: 74200 },
    { name: 'Munambam Fishing Harbour', landingsTons: 58900 },
    { name: 'Mangalore Old Port', landingsTons: 49300 },
    { name: 'Visakhapatnam Fishing Harbour', landingsTons: 46100 },
    { name: 'Chennai Kasimedu Harbour', landingsTons: 41800 }
  ]
};

export const MOCK_FISHERIES_TRENDS: FisheriesTrendPoint[] = [
  { period: 'Q1 2024', pelagicCatchTons: 52000, demersalCatchTons: 28000, crustaceanCatchTons: 14000, averageCPUE: 135, totalEffortHours: 72000 },
  { period: 'Q2 2024', pelagicCatchTons: 64000, demersalCatchTons: 31000, crustaceanCatchTons: 16500, averageCPUE: 148, totalEffortHours: 78000 },
  { period: 'Q3 2024', pelagicCatchTons: 28000, demersalCatchTons: 12000, crustaceanCatchTons: 7500, averageCPUE: 110, totalEffortHours: 36000 }, // Monsoon ban period
  { period: 'Q4 2024', pelagicCatchTons: 82000, demersalCatchTons: 42000, crustaceanCatchTons: 22000, averageCPUE: 172, totalEffortHours: 94000 },
  { period: 'Q1 2025', pelagicCatchTons: 56000, demersalCatchTons: 30000, crustaceanCatchTons: 15200, averageCPUE: 140, totalEffortHours: 74000 },
  { period: 'Q2 2025', pelagicCatchTons: 69000, demersalCatchTons: 33500, crustaceanCatchTons: 18000, averageCPUE: 154, totalEffortHours: 81000 }
];

// ----------------------------------------------------
// Mock Species Catalog
// ----------------------------------------------------
export const MOCK_SPECIES: SpeciesRecord[] = [
  {
    id: 'sp-01',
    taxonomy: {
      kingdom: 'Animalia',
      phylum: 'Chordata',
      class: 'Actinopterygii',
      order: 'Scombriformes',
      family: 'Scombridae',
      genus: 'Rastrelliger',
      species: 'Rastrelliger kanagurta',
      scientificName: 'Rastrelliger kanagurta',
      commonName: 'Indian Mackerel',
      aphiaId: 219717
    },
    iucnRedListCategory: 'Least Concern',
    commercialImportance: 'High',
    habitatType: 'Epipelagic',
    occurrenceCount: 2450,
    ednaDetectionCount: 420,
    knownDepthRange: [5, 90],
    preferredTemperatureRange: [25.0, 30.5],
    preferredSalinityRange: [32.0, 36.0],
    imageUrl: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&auto=format&fit=crop&q=80',
    description: 'Major commercial pelagic schooling species across the Indo-West Pacific, key indicator for upwelling and chlorophyll-rich coastal waters.'
  },
  {
    id: 'sp-02',
    taxonomy: {
      kingdom: 'Animalia',
      phylum: 'Chordata',
      class: 'Actinopterygii',
      order: 'Clupeiformes',
      family: 'Clupeidae',
      genus: 'Sardinella',
      species: 'Sardinella longiceps',
      scientificName: 'Sardinella longiceps',
      commonName: 'Indian Oil Sardine',
      aphiaId: 217420
    },
    iucnRedListCategory: 'Least Concern',
    commercialImportance: 'High',
    habitatType: 'Epipelagic',
    occurrenceCount: 3820,
    ednaDetectionCount: 680,
    knownDepthRange: [0, 60],
    preferredTemperatureRange: [24.5, 29.5],
    preferredSalinityRange: [33.0, 35.8],
    imageUrl: 'https://images.unsplash.com/photo-1535591273668-578e31182c4f?w=400&auto=format&fit=crop&q=80',
    description: 'Dominant pelagic fishery resource of south-west coast of India; highly sensitive to monsoonal upwelling and sea surface temperature fluctuations.'
  },
  {
    id: 'sp-03',
    taxonomy: {
      kingdom: 'Animalia',
      phylum: 'Chordata',
      class: 'Actinopterygii',
      order: 'Scombriformes',
      family: 'Scombridae',
      genus: 'Thunnus',
      species: 'Thunnus albacares',
      scientificName: 'Thunnus albacares',
      commonName: 'Yellowfin Tuna',
      aphiaId: 127027
    },
    iucnRedListCategory: 'Near Threatened',
    commercialImportance: 'High',
    habitatType: 'Epipelagic',
    occurrenceCount: 890,
    ednaDetectionCount: 195,
    knownDepthRange: [10, 250],
    preferredTemperatureRange: [20.0, 28.0],
    preferredSalinityRange: [34.0, 36.5],
    imageUrl: 'https://images.unsplash.com/photo-1524704654690-b56c05c78a00?w=400&auto=format&fit=crop&q=80',
    description: 'High-value oceanic apex predator distributed throughout the tropical Indian Ocean, tracked via satellite telemetry and molecular eDNA assays.'
  },
  {
    id: 'sp-04',
    taxonomy: {
      kingdom: 'Animalia',
      phylum: 'Chordata',
      class: 'Actinopterygii',
      order: 'Perciformes',
      family: 'Serranidae',
      genus: 'Epinephelus',
      species: 'Epinephelus coioides',
      scientificName: 'Epinephelus coioides',
      commonName: 'Orange-spotted Grouper',
      aphiaId: 218224
    },
    iucnRedListCategory: 'Vulnerable',
    commercialImportance: 'High',
    habitatType: 'Demersal',
    occurrenceCount: 420,
    ednaDetectionCount: 78,
    knownDepthRange: [5, 100],
    preferredTemperatureRange: [22.0, 29.0],
    preferredSalinityRange: [33.5, 36.0],
    imageUrl: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&auto=format&fit=crop&q=80',
    description: 'Reef and coastal shelf demersal species of significant commercial and ecological value; susceptible to overfishing and habitat degradation.'
  }
];

// ----------------------------------------------------
// Mock eDNA Samples & Detections
// ----------------------------------------------------
export const MOCK_EDNA_SAMPLES: EDNASample[] = [
  {
    id: 'edna-smp-01',
    sampleCode: 'CMLRE-412-STN01-D25',
    stationId: 'CMLRE-STN-KOC-01',
    cruiseId: 'SS-412',
    samplingDate: '2025-03-12T07:30:00Z',
    latitude: 9.94,
    longitude: 75.82,
    samplingDepthMeters: 25,
    filterType: 'Sterivex 0.22µm',
    waterVolumeFilteredLiters: 2.5,
    dnaYieldNgPerUl: 18.4,
    targetMarkers: ['12S', 'COI'],
    sequencingPlatform: 'Illumina NovaSeq',
    totalDetectionsCount: 38,
    collectorName: 'Dr. Ananya Nair'
  },
  {
    id: 'edna-smp-02',
    sampleCode: 'CMLRE-412-STN04-D75',
    stationId: 'CMLRE-STN-CLT-04',
    cruiseId: 'SS-412',
    samplingDate: '2025-03-14T09:15:00Z',
    latitude: 11.25,
    longitude: 74.90,
    samplingDepthMeters: 75,
    filterType: 'Sterivex 0.22µm',
    waterVolumeFilteredLiters: 3.0,
    dnaYieldNgPerUl: 12.8,
    targetMarkers: ['12S', '16S'],
    sequencingPlatform: 'Illumina NovaSeq',
    totalDetectionsCount: 29,
    collectorName: 'Dr. Ananya Nair'
  },
  {
    id: 'edna-smp-03',
    sampleCode: 'CMLRE-412-STN08-D20',
    stationId: 'CMLRE-STN-LAK-02',
    cruiseId: 'SS-412',
    samplingDate: '2025-03-18T11:00:00Z',
    latitude: 10.55,
    longitude: 72.60,
    samplingDepthMeters: 20,
    filterType: 'Cellulose Nitrate 0.45µm',
    waterVolumeFilteredLiters: 2.0,
    dnaYieldNgPerUl: 24.2,
    targetMarkers: ['12S', 'COI', '16S'],
    sequencingPlatform: 'Illumina NovaSeq',
    totalDetectionsCount: 54,
    collectorName: 'Molecular Genomics Lab'
  }
];

export const MOCK_EDNA_DETECTIONS: EDNADetection[] = [
  {
    id: 'edna-det-01',
    sampleId: 'edna-smp-01',
    sampleCode: 'CMLRE-412-STN01-D25',
    speciesId: 'sp-01',
    scientificName: 'Rastrelliger kanagurta',
    commonName: 'Indian Mackerel',
    taxonomicRank: 'Species',
    markerUsed: '12S',
    readCount: 1420,
    relativeAbundancePercent: 34.2,
    matchIdentityPercent: 99.8,
    confidenceScore: 0.99,
    referenceDatabase: 'MIFish',
    samplingCoordinates: [9.94, 75.82]
  },
  {
    id: 'edna-det-02',
    sampleId: 'edna-smp-01',
    sampleCode: 'CMLRE-412-STN01-D25',
    speciesId: 'sp-02',
    scientificName: 'Sardinella longiceps',
    commonName: 'Indian Oil Sardine',
    taxonomicRank: 'Species',
    markerUsed: '12S',
    readCount: 1180,
    relativeAbundancePercent: 28.4,
    matchIdentityPercent: 99.4,
    confidenceScore: 0.98,
    referenceDatabase: 'MIFish',
    samplingCoordinates: [9.94, 75.82]
  },
  {
    id: 'edna-det-03',
    sampleId: 'edna-smp-02',
    sampleCode: 'CMLRE-412-STN04-D75',
    speciesId: 'sp-03',
    scientificName: 'Thunnus albacares',
    commonName: 'Yellowfin Tuna',
    taxonomicRank: 'Species',
    markerUsed: 'COI',
    readCount: 650,
    relativeAbundancePercent: 18.2,
    matchIdentityPercent: 98.9,
    confidenceScore: 0.97,
    referenceDatabase: 'BOLD Systems',
    samplingCoordinates: [11.25, 74.90]
  },
  {
    id: 'edna-det-04',
    sampleId: 'edna-smp-03',
    sampleCode: 'CMLRE-412-STN08-D20',
    speciesId: 'sp-04',
    scientificName: 'Epinephelus coioides',
    commonName: 'Orange-spotted Grouper',
    taxonomicRank: 'Species',
    markerUsed: '12S',
    readCount: 420,
    relativeAbundancePercent: 12.6,
    matchIdentityPercent: 99.1,
    confidenceScore: 0.98,
    referenceDatabase: 'MIFish',
    samplingCoordinates: [10.55, 72.60]
  }
];

// ----------------------------------------------------
// Mock Scientific Analysis Result (Real Regression Suite)
// ----------------------------------------------------
export const MOCK_ANALYSIS_RESULTS: Record<string, AnalysisResultData> = {
  'analysis-sst-richness': {
    id: 'analysis-sst-richness',
    title: 'Cross-Domain Regression: Sea Surface Temperature vs Marine Species Richness',
    analysisType: 'cross_domain_correlation',
    summaryText: 'Moderate positive correlation observed between SST (25.5°C - 29.5°C) and pelagic species richness across 240 Arabian Sea sampling transects.',
    parameters: {
      analysisType: 'cross_domain_correlation',
      independentVariable: 'sea_surface_temperature',
      dependentVariable: 'species_richness',
      region: 'Arabian Sea',
      depthMin: 0,
      depthMax: 50,
      transformation: 'none'
    },
    status: 'completed',
    executionDurationMs: 420,
    statistics: {
      sampleSize: 45,
      pearsonR: 0.742,
      rSquared: 0.551,
      pValue: 0.0001,
      standardError: 2.14,
      fStatistic: 52.8,
      slope: 3.85,
      intercept: -82.4
    },
    scatterPoints: [
      { x: 25.5, y: 16, label: 'STN-01 (Kochi)', residual: 0.2 },
      { x: 26.0, y: 19, label: 'STN-02 (Alleppey)', residual: 1.1 },
      { x: 26.4, y: 18, label: 'STN-03 (Kollam)', residual: -1.4 },
      { x: 26.8, y: 22, label: 'STN-04 (Trivandrum)', residual: 1.2 },
      { x: 27.2, y: 21, label: 'STN-05 (Kanyakumari)', residual: -1.3 },
      { x: 27.5, y: 24, label: 'STN-06 (Vizhinjam)', residual: 0.5 },
      { x: 27.8, y: 26, label: 'STN-07 (Calicut)', residual: 1.3 },
      { x: 28.1, y: 25, label: 'STN-08 (Kannur)', residual: -0.8 },
      { x: 28.4, y: 28, label: 'STN-09 (Mangalore)', residual: 1.1 },
      { x: 28.7, y: 27, label: 'STN-10 (Udupi)', residual: -1.0 },
      { x: 29.0, y: 31, label: 'STN-11 (Karwar)', residual: 1.7 },
      { x: 29.3, y: 29, label: 'STN-12 (Goa South)', residual: -1.4 },
      { x: 29.6, y: 33, label: 'STN-13 (Goa North)', residual: 1.4 },
      { x: 30.0, y: 32, label: 'STN-14 (Ratnagiri)', residual: -1.1 },
      { x: 30.4, y: 34, label: 'STN-15 (Mumbai)', residual: -0.6 }
    ],
    regressionLine: {
      xMin: 25.5,
      xMax: 30.5,
      yAtMin: 15.8,
      yAtMax: 35.0
    },
    provenance: {
      inputDatasetIds: ['ds-cmlre-ctd-03', 'ds-cmlre-txt-02'],
      recordsUsedCount: 1420,
      algorithmName: 'Ordinary Least Squares (OLS) Linear Regression with Heteroskedasticity-Robust Standard Errors',
      computedTimestamp: '2026-08-21T09:15:00Z'
    },
    ecologicalInterpretation: 'Thermal optimum for coastal pelagic biodiversity peaks between 28.5°C and 29.8°C. Beyond 30.2°C, localized drops in dissolved oxygen cause slight compression of the suitable vertical habitat.'
  },
  'analysis-oxygen-cpue': {
    id: 'analysis-oxygen-cpue',
    title: 'Hypoxia vs Fisheries CPUE Correlation Analysis',
    analysisType: 'cross_domain_correlation',
    summaryText: 'Strong positive relationship between Subsurface Dissolved Oxygen (>2.5 mg/L) and Trawler Catch Per Unit Effort.',
    parameters: {
      analysisType: 'cross_domain_correlation',
      independentVariable: 'dissolved_oxygen',
      dependentVariable: 'cpue_kg_per_hour',
      region: 'Arabian Sea Shelf',
      depthMin: 20,
      depthMax: 100,
      transformation: 'none'
    },
    status: 'completed',
    executionDurationMs: 380,
    statistics: {
      sampleSize: 40,
      pearsonR: 0.815,
      rSquared: 0.664,
      pValue: 0.00005,
      standardError: 12.8,
      fStatistic: 75.2,
      slope: 28.4,
      intercept: 14.2
    },
    scatterPoints: [
      { x: 1.0, y: 40, label: 'Hypoxic Core A' },
      { x: 1.4, y: 52, label: 'Hypoxic Core B' },
      { x: 1.8, y: 68, label: 'Hypoxic Margin' },
      { x: 2.2, y: 79, label: 'Station 18' },
      { x: 2.6, y: 92, label: 'Station 22' },
      { x: 3.0, y: 104, label: 'Station 28' },
      { x: 3.5, y: 118, label: 'Station 34' },
      { x: 4.0, y: 129, label: 'Station 40' },
      { x: 4.5, y: 144, label: 'Station 48' },
      { x: 5.0, y: 156, label: 'Station 54' }
    ],
    regressionLine: {
      xMin: 1.0,
      xMax: 5.2,
      yAtMin: 42.6,
      yAtMax: 161.8
    },
    provenance: {
      inputDatasetIds: ['ds-cmlre-ctd-03', 'ds-cmlre-csv-04'],
      recordsUsedCount: 840,
      algorithmName: 'Linear Bivariate Correlation & Robust Huber Regressor',
      computedTimestamp: '2026-08-21T09:40:00Z'
    },
    ecologicalInterpretation: 'Demersal finfish and crustaceans avoid Oxygen Minimum Zones where DO falls below 1.5 mg/L, congregating at oxygenated shelf edges.'
  }
};

// ----------------------------------------------------
// Mock Machine Learning Models & Inference
// ----------------------------------------------------
export const MOCK_ML_MODELS: MLModelInfo[] = [
  {
    id: 'ml-mod-01',
    name: 'Marine Environmental Anomaly Detector (MEAD-v2)',
    type: 'environmental_anomaly_detector',
    version: '2.1.0',
    framework: 'Isolation-Forest',
    trainingAccuracyF1: 0.942,
    lastTrainedDate: '2026-08-01',
    inputFeatures: ['SST_anomaly', 'Salinity_deviation', 'DO_gradient', 'Chlorophyll_spike', 'Wind_stress'],
    description: 'Isolation Forest & One-Class SVM ensemble identifying marine heatwaves, severe hypoxia, and unseasonal coastal upwelling events.',
    status: 'active'
  },
  {
    id: 'ml-mod-02',
    name: 'Pelagic Fish Habitat Suitability Model (MaxEnt-Ocean)',
    type: 'habitat_suitability_maxent',
    version: '1.8.4',
    framework: 'XGBoost',
    trainingAccuracyF1: 0.918,
    lastTrainedDate: '2026-07-20',
    inputFeatures: ['SST', 'Bathymetry', 'Thermocline_Depth', 'Chlorophyll_a', 'Distance_to_Coast'],
    description: 'Species Environmental Niche & Ecological Habitat Suitability Index predicting commercial pelagic distributions.',
    status: 'active'
  },
  {
    id: 'ml-mod-03',
    name: 'Catch Prediction (MBLF-Net)',
    type: 'catch_forecasting_xgboost',
    version: '3.0.1',
    framework: 'XGBoost',
    trainingAccuracyF1: 0.885,
    lastTrainedDate: '2026-07-15',
    inputFeatures: ['Historical_CPUE', 'Monsoon_Index', 'SST_Lag30', 'Fishing_Effort_Hours'],
    description: 'Temporal CNN-LSTM forecaster generating quarterly catch landings estimates with 95% confidence intervals.',
    status: 'active'
  }
];

export const MOCK_ANOMALIES: AnomalyDetectionResult[] = [
  {
    id: 'anom-01',
    region: 'South-Eastern Arabian Sea (Off Kozhikode)',
    latitude: 11.20,
    longitude: 75.10,
    detectionDate: '2026-08-20T12:00:00Z',
    anomalyType: 'Severe Hypoxia Event',
    severity: 'High',
    anomalyScore: 84,
    confidenceScore: 0.92,
    baselineExpectedValue: 'DO >= 3.8 mg/L at 40m depth',
    observedCurrentValue: 'DO = 1.9 mg/L (Upwelling OMZ intrusion)',
    contributingFeatures: [
      { feature: 'Subsurface Dissolved Oxygen', importanceWeight: 0.52, impactDirection: 'negative' },
      { feature: 'Chlorophyll-a Plume Density', importanceWeight: 0.28, impactDirection: 'positive' },
      { feature: 'Thermocline Shoaling Index', importanceWeight: 0.20, impactDirection: 'positive' }
    ],
    mitigationAdvice: 'Demersal stocks expected to migrate shoreward or disperse into deeper oxygenated offshore pockets.'
  },
  {
    id: 'anom-02',
    region: 'North-Western Bay of Bengal (Off Visakhapatnam)',
    latitude: 17.65,
    longitude: 83.35,
    detectionDate: '2026-08-20T08:30:00Z',
    anomalyType: 'Marine Heatwave (MHW)',
    severity: 'Severe',
    anomalyScore: 88,
    confidenceScore: 0.95,
    baselineExpectedValue: 'Mean SST 28.1°C',
    observedCurrentValue: 'SST 30.8°C (+2.7°C above 90th percentile)',
    contributingFeatures: [
      { feature: 'Sea Surface Temperature Anomaly', importanceWeight: 0.65, impactDirection: 'positive' },
      { feature: 'Wind Speed Reduction', importanceWeight: 0.22, impactDirection: 'negative' },
      { feature: 'Solar Radiance Flux', importanceWeight: 0.13, impactDirection: 'positive' }
    ],
    mitigationAdvice: 'Issue thermal stress alert for nearshore coral patches and monitor pelagic tuna schooling depths.'
  }
];

export const MOCK_HABITAT_SUITABILITY: HabitatSuitabilityResult[] = [
  {
    speciesName: 'Rastrelliger kanagurta',
    commonName: 'Indian Mackerel',
    targetRegion: 'South-Eastern Arabian Sea',
    suitabilityIndex: 0.88,
    suitabilityClass: 'Optimal',
    optimalDepthRangeMeters: [10, 45],
    optimalTemperatureRangeCelsius: [27.0, 29.5],
    predictedBiomassIndex: 142.5,
    confidenceScore: 0.94,
    environmentalDrivers: [
      { driver: 'Chlorophyll-a', currentValue: '2.4 mg/m³', optimalRange: '1.5 - 3.5 mg/m³', stressContributionPercent: 5 },
      { driver: 'SST', currentValue: '28.6°C', optimalRange: '27.0 - 29.5°C', stressContributionPercent: 8 },
      { driver: 'Dissolved Oxygen', currentValue: '4.8 mg/L', optimalRange: '> 3.5 mg/L', stressContributionPercent: 2 }
    ]
  },
  {
    speciesName: 'Thunnus albacares',
    commonName: 'Yellowfin Tuna',
    targetRegion: 'Central Arabian Sea / Lakshadweep',
    suitabilityIndex: 0.76,
    suitabilityClass: 'Favorable',
    optimalDepthRangeMeters: [30, 180],
    optimalTemperatureRangeCelsius: [22.0, 28.0],
    predictedBiomassIndex: 88.0,
    confidenceScore: 0.91,
    environmentalDrivers: [
      { driver: 'Thermocline Depth', currentValue: '45m', optimalRange: '40 - 80m', stressContributionPercent: 12 },
      { driver: 'Mixed Layer Salinity', currentValue: '35.4 PSU', optimalRange: '34.5 - 36.0 PSU', stressContributionPercent: 4 },
      { driver: 'Forage Biomass Proxy', currentValue: 'High', optimalRange: 'Moderate - High', stressContributionPercent: 6 }
    ]
  }
];

export const MOCK_CATCH_FORECASTS: CatchForecastResult[] = [
  {
    forecastPeriod: 'Q3 2026 (Post-Monsoon)',
    targetSpecies: 'Indian Oil Sardine (Sardinella longiceps)',
    predictedCatchTons: 78500,
    confidenceInterval95: [71200, 85800],
    historicalAverageTons: 64200,
    trendDirection: 'increasing',
    modelExplanation: 'Favorable monsoonal upwelling and above-average chlorophyll-a blooms indicate strong recruitment and biomass resurgence along the Malabar coast.'
  },
  {
    forecastPeriod: 'Q3 2026 (Post-Monsoon)',
    targetSpecies: 'Indian Mackerel (Rastrelliger kanagurta)',
    predictedCatchTons: 54200,
    confidenceInterval95: [49000, 59400],
    historicalAverageTons: 52800,
    trendDirection: 'stable',
    modelExplanation: 'Stable thermal regime and steady primary production maintain sustained yields across coastal neritic zones.'
  },
  {
    forecastPeriod: 'Q3 2026 (Post-Monsoon)',
    targetSpecies: 'Yellowfin Tuna (Thunnus albacares)',
    predictedCatchTons: 29800,
    confidenceInterval95: [26500, 33100],
    historicalAverageTons: 33400,
    trendDirection: 'declining',
    modelExplanation: 'Subsurface thermocline deepening in offshore waters indicates temporary dispersal into oceanic EEZ limits.'
  },
  {
    forecastPeriod: 'Q3 2026 (Post-Monsoon)',
    targetSpecies: 'Karikkadi Shrimp (Parapenaeopsis stylifera)',
    predictedCatchTons: 38700,
    confidenceInterval95: [35200, 42200],
    historicalAverageTons: 32900,
    trendDirection: 'increasing',
    modelExplanation: 'High post-ban trawl efficiency and muddy bottom substrate enrichment drive strong coastal landing volumes.'
  }
];

// ----------------------------------------------------
// Mock Alerts
// ----------------------------------------------------
export const MOCK_ALERTS: MarineAlert[] = [
  {
    id: 'alt-01',
    title: 'Critical Hypoxia Risk in Coastal Trawling Grounds',
    category: 'biodiversity_risk',
    severity: 'critical',
    region: 'South-Eastern Arabian Sea (Off Calicut)',
    latitude: 11.20,
    longitude: 75.10,
    confidencePercent: 88,
    timestamp: '2026-08-21T07:30:00Z',
    isAcknowledged: false,
    contributingFactors: [
      { factor: 'Dissolved Oxygen (DO)', direction: 'down', value: '1.9 mg/L' },
      { factor: 'Sea Surface Temp (SST)', direction: 'up', value: '+1.4°C' },
      { factor: 'Chlorophyll-a Biomass', direction: 'up', value: '3.8 mg/m³' },
      { factor: 'Active Trawler Effort', direction: 'up', value: '8.2 hrs/sq.km' }
    ],
    description: 'Upwelling-driven Oxygen Minimum Zone shoaling has intruded into the 30-50m shelf depth zone, reducing suitable demersal habitat by 42%.',
    affectedSpeciesOrIndustries: ['Demersal Shrimp Trawling', 'Nemipterus japonicus', 'Epinephelus coioides'],
    recommendedAction: 'Advisory to commercial mechanized trawlers to shift operations beyond 70m depth contours or southward of Alleppey.'
  },
  {
    id: 'alt-02',
    title: 'Marine Heatwave (MHW) Warning - Visakhapatnam Sector',
    category: 'environmental_anomaly',
    severity: 'warning',
    region: 'North-Western Bay of Bengal',
    latitude: 17.65,
    longitude: 83.35,
    confidencePercent: 92,
    timestamp: '2026-08-20T14:15:00Z',
    isAcknowledged: false,
    contributingFactors: [
      { factor: 'Sea Surface Temperature', direction: 'up', value: '30.8°C (+2.7°C)' },
      { factor: 'Surface Wind Speed', direction: 'down', value: '2.8 m/s' },
      { factor: 'Thermal Stratification', direction: 'up', value: 'High' }
    ],
    description: 'Persistent SST anomaly exceeding the 90th historical percentile for 5 consecutive days. Coral stress indices elevated in coastal reefs.',
    affectedSpeciesOrIndustries: ['Coastal Coral Reefs', 'Pelagic Skipjack Schools', 'Artisanal Gillnetters'],
    recommendedAction: 'Deploy CTD autonomous gliders for continuous depth-resolved thermocline monitoring.'
  },
  {
    id: 'alt-03',
    title: 'Fisheries Effort Saturation Advisory in Gulf of Mannar',
    category: 'fisheries_stress',
    severity: 'advisory',
    region: 'Gulf of Mannar & Palk Bay',
    latitude: 9.15,
    longitude: 79.20,
    confidencePercent: 79,
    timestamp: '2026-08-19T10:00:00Z',
    isAcknowledged: true,
    contributingFactors: [
      { factor: 'Fleet Density', direction: 'up', value: '380 vessels/100 sq.km' },
      { factor: 'Juvenile Landings Ratio', direction: 'up', value: '28%' },
      { factor: 'Average CPUE', direction: 'down', value: '88 kg/hr' }
    ],
    description: 'Catch per unit effort has dropped 18% below seasonal baseline with high juvenile proportions in trawl codends.',
    affectedSpeciesOrIndustries: ['Penaeid Shrimp Fishery', 'Cephalopod Landings'],
    recommendedAction: 'Enforce square mesh codends (30mm) and review spatial effort allocation.'
  }
];

export const MOCK_ALERT_SUMMARY: AlertSummaryMetrics = {
  totalAlerts: 3,
  criticalCount: 1,
  warningCount: 1,
  advisoryCount: 1,
  unacknowledgedCount: 2
};

export const MOCK_MARINE_SUMMARY: MarineSummary = {
  totalObservations: 142850,
  totalDatasets: 18,
  totalSpeciesRecorded: 1420,
  totalEdnaDetections: 3840,
  activeAnomalies: 2,
  spatialCoveragePercentage: 92.4,
  regionsBreakdown: [
    { region: 'Arabian Sea (West Coast)', observationCount: 78500, speciesCount: 940, activeVessels: 1120 },
    { region: 'Bay of Bengal (East Coast)', observationCount: 42100, speciesCount: 680, activeVessels: 540 },
    { region: 'Lakshadweep Archipelago', observationCount: 14250, speciesCount: 410, activeVessels: 95 },
    { region: 'Andaman & Nicobar Islands', observationCount: 8000, speciesCount: 520, activeVessels: 65 }
  ],
  temporalSpan: {
    earliest: '2023-01-01',
    latest: '2026-08-21'
  }
};
