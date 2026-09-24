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
