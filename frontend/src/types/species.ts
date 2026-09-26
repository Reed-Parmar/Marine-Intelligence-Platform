export interface SpeciesTaxonomy {
  kingdom: string;
  phylum: string;
  class: string;
  order: string;
  family: string;
  genus: string;
  species: string;
  scientificName: string;
  commonName: string;
  aphiaId?: number; // WoRMS taxonomic ID
}

export interface SpeciesRecord {
  id: string;
  taxonomy: SpeciesTaxonomy;
  iucnRedListCategory: 'Least Concern' | 'Near Threatened' | 'Vulnerable' | 'Endangered' | 'Critically Endangered' | 'Data Deficient';
  commercialImportance: 'High' | 'Moderate' | 'Low' | 'Non-Commercial';
  habitatType: 'Epipelagic' | 'Mesopelagic' | 'Demersal' | 'Benthic' | 'Coral Reef' | 'Estuarine';
  occurrenceCount: number;
  ednaDetectionCount: number;
  knownDepthRange: [number, number];
  preferredTemperatureRange: [number, number];
  preferredSalinityRange: [number, number];
  imageUrl?: string;
  description: string;
}

export interface SpeciesOccurrence {
  id: string;
  speciesId: string;
  scientificName: string;
  commonName: string;
  recordedBy: string;
  eventDate: string;
  latitude: number;
  longitude: number;
  depthMeters: number;
  individualCount: number;
  lifeStage?: 'Adult' | 'Juvenile' | 'Larva' | 'Egg';
  basisOfRecord: 'HumanObservation' | 'PreservedSpecimen' | 'MachineObservation' | 'EnvironmentalDNA';
  datasetId: string;
}

export interface SpeciesDistributionPoint {
  latitude: number;
  longitude: number;
  abundance: number;
  depth: number;
  surveyYear: number;
}

export interface SpeciesPredictionCandidate {
  species: string;
  commonName: string;
  family: string;
  classId: number;
  confidence: number;
  confidencePercent: number;
  order?: string;
  wormsAphiaId?: number;
  iucnStatus?: string;
  habitat?: string;
  depthRangeM?: [number, number];
}

export interface SpeciesIdentificationResponse {
  species: string;
  commonName: string;
  family: string;
  confidence: number;
  confidenceTier: 'HIGH' | 'MODERATE' | 'LOW';
  confidencePercent: number;
  wormsAphiaId?: number;
  iucnStatus?: string;
  habitat?: string;
  topPredictions: SpeciesPredictionCandidate[];
  modelVersion: string;
  modelArchitecture: string;
  device: string;
  inferenceTimeMs: number;
}

export interface SupportedSpeciesInfo {
  classId: number;
  scientificName: string;
  commonName: string;
  family: string;
  order?: string;
  class?: string;
  wormsAphiaId?: number;
  iucnStatus?: string;
  trophicGuild?: string;
  habitat?: string;
  depthRangeM?: [number, number];
}

export interface SpeciesModelInfoResponse {
  modelName: string;
  architecture: string;
  version: string;
  numClasses: number;
  classes: string[];
  supportedSpecies: SupportedSpeciesInfo[];
  inputResolution: [number, number, number];
  device: string;
  status: string;
}

