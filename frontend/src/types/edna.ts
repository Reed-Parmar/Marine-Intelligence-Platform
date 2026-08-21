export interface EDNASample {
  id: string;
  sampleCode: string;
  stationId: string;
  cruiseId: string;
  samplingDate: string;
  latitude: number;
  longitude: number;
  samplingDepthMeters: number;
  filterType: 'Sterivex 0.22µm' | 'Cellulose Nitrate 0.45µm' | 'Glass Fiber';
  waterVolumeFilteredLiters: number;
  dnaYieldNgPerUl: number;
  targetMarkers: ('12S' | '16S' | 'COI' | '18S')[];
  sequencingPlatform: 'Illumina NovaSeq' | 'Illumina MiSeq' | 'Oxford Nanopore';
  totalDetectionsCount: number;
  collectorName: string;
}

export interface EDNADetection {
  id: string;
  sampleId: string;
  sampleCode: string;
  speciesId?: string;
  scientificName: string;
  commonName: string;
  taxonomicRank: 'Species' | 'Genus' | 'Family';
  markerUsed: '12S' | '16S' | 'COI' | '18S';
  readCount: number;
  relativeAbundancePercent: number;
  matchIdentityPercent: number; // e.g. 99.4%
  confidenceScore: number; // 0.0 - 1.0 (e.g. 0.98)
  referenceDatabase: 'NCBI BLAST' | 'MIFish' | 'BOLD Systems';
  samplingCoordinates: [number, number];
}
