import { ApiClient } from './api';
import { SpeciesRecord, SpeciesOccurrence } from '../types/species';
import { MOCK_SPECIES } from './mockData';

function normalizeSpecies(s: any): SpeciesRecord {
  return {
    id: String(s.id || ''),
    taxonomy: {
      scientificName: s.taxonomy?.scientificName || s.scientific_name || 'Marine specimen',
      commonName: s.taxonomy?.commonName || s.common_name || 'Marine organism',
      kingdom: s.taxonomy?.kingdom || s.kingdom || 'Animalia',
      phylum: s.taxonomy?.phylum || s.phylum || 'Chordata',
      class: s.taxonomy?.class || s.class_name || s.class || 'Actinopterygii',
      order: s.taxonomy?.order || s.order_name || s.order || 'Perciformes',
      family: s.taxonomy?.family || s.family || 'Scombridae',
      genus: s.taxonomy?.genus || s.genus || (s.scientific_name ? s.scientific_name.split(' ')[0] : 'Scomber'),
      species: s.taxonomy?.species || s.species || (s.scientific_name ? s.scientific_name.split(' ')[1] : 'sp.')
    },
    iucnRedListCategory: (s.iucnRedListCategory || s.iucn_red_list_status || 'Least Concern') as any,
    commercialImportance: (s.commercialImportance || s.commercial_importance || 'High') as any,
    habitatType: (s.habitatType || s.habitat_type || 'Epipelagic') as any,
    occurrenceCount: Number(s.occurrenceCount ?? s.occurrences_count ?? 48),
    ednaDetectionCount: Number(s.ednaDetectionCount ?? s.edna_detection_count ?? 12),
    knownDepthRange: s.knownDepthRange || [
      s.depth_min !== undefined ? Number(s.depth_min) : 0,
      s.depth_max !== undefined ? Number(s.depth_max) : 100
    ],
    preferredTemperatureRange: s.preferredTemperatureRange || [22.0, 29.5],
    preferredSalinityRange: s.preferredSalinityRange || [33.0, 36.0],
    imageUrl: s.imageUrl || s.image_url || 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&auto=format&fit=crop&q=80',
    description: s.description || 'Marine specimen cataloged in CMLRE biodiversity repository.'
  };
}

function normalizeOccurrence(o: any, speciesId: string): SpeciesOccurrence {
  return {
    id: String(o.id || ''),
    speciesId: String(o.speciesId || o.species_id || speciesId),
    scientificName: o.scientificName || o.scientific_name || 'Marine specimen',
    commonName: o.commonName || o.common_name || 'Marine organism',
    recordedBy: o.recordedBy || o.recorded_by || 'FORV Sagar Sampada',
    eventDate: o.eventDate || o.event_date || o.observed_at || o.time || new Date().toISOString().split('T')[0],
    latitude: Number(o.latitude || 0),
    longitude: Number(o.longitude || 0),
    depthMeters: o.depthMeters ?? (o.depth !== undefined ? Number(o.depth) : 0),
    individualCount: o.individualCount ?? (o.individual_count !== undefined ? Number(o.individual_count) : 1),
    basisOfRecord: o.basisOfRecord || o.basis_of_record || 'HumanObservation',
    datasetId: o.datasetId || o.dataset_id || 'ds-default'
  };
}

export const speciesService = {
  async getSpeciesList(search?: string): Promise<SpeciesRecord[]> {
    let fallback = [...MOCK_SPECIES];
    if (search) {
      const q = search.toLowerCase();
      fallback = fallback.filter(s => 
        s.taxonomy.scientificName.toLowerCase().includes(q) ||
        s.taxonomy.commonName.toLowerCase().includes(q) ||
        s.taxonomy.family.toLowerCase().includes(q)
      );
    }
    const res = await ApiClient.get<any[]>('/species', fallback, search ? { search } : undefined);
    const list = Array.isArray(res.data) ? res.data : fallback;
    return list.map(normalizeSpecies);
  },

  async getSpeciesById(speciesId: string): Promise<SpeciesRecord> {
    const fallback = MOCK_SPECIES.find(s => s.id === speciesId) || MOCK_SPECIES[0];
    const res = await ApiClient.get<any>(`/species/${speciesId}`, fallback);
    return normalizeSpecies(res.data || fallback);
  },

  async getSpeciesOccurrences(speciesId: string): Promise<SpeciesOccurrence[]> {
    const fallback: SpeciesOccurrence[] = [
      {
        id: 'occ-01',
        speciesId,
        scientificName: 'Rastrelliger kanagurta',
        commonName: 'Indian Mackerel',
        recordedBy: 'FORV Sagar Sampada',
        eventDate: '2025-03-12',
        latitude: 9.94,
        longitude: 75.82,
        depthMeters: 25,
        individualCount: 140,
        basisOfRecord: 'HumanObservation',
        datasetId: 'ds-cmlre-txt-02'
      },
      {
        id: 'occ-02',
        speciesId,
        scientificName: 'Rastrelliger kanagurta',
        commonName: 'Indian Mackerel',
        recordedBy: 'CMLRE Coastal Survey',
        eventDate: '2025-03-15',
        latitude: 11.25,
        longitude: 74.90,
        depthMeters: 45,
        individualCount: 85,
        basisOfRecord: 'EnvironmentalDNA',
        datasetId: 'ds-cmlre-txt-01'
      }
    ];

    const res = await ApiClient.get<any[]>(`/species/${speciesId}/occurrences`, fallback);
    const list = Array.isArray(res.data) ? res.data : fallback;
    return list.map(o => normalizeOccurrence(o, speciesId));
  }
};
