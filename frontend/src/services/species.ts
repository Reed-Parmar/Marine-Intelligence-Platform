import { ApiClient } from './api';
import { SpeciesRecord, SpeciesOccurrence } from '../types/species';

function normalizeSpecies(s: any): SpeciesRecord {
  return {
    id: String(s.id || ''),
    taxonomy: {
      scientificName: s.taxonomy?.scientificName || s.scientific_name || '',
      commonName: s.taxonomy?.commonName || s.common_name || '',
      kingdom: s.taxonomy?.kingdom || s.kingdom || '',
      phylum: s.taxonomy?.phylum || s.phylum || '',
      class: s.taxonomy?.class || s.class_name || s.class || '',
      order: s.taxonomy?.order || s.order_name || s.order || '',
      family: s.taxonomy?.family || s.family_name || s.family || '',
      genus: s.taxonomy?.genus || s.genus || (s.scientific_name ? (s.scientific_name.split(' ')[0] || '') : ''),
      species: s.taxonomy?.species || s.species || (s.scientific_name ? (s.scientific_name.split(' ')[1] || '') : ''),
      aphiaId: s.taxonomy?.aphiaId || s.aphia_id || s.aphiaId || undefined
    },
    iucnRedListCategory: (s.iucnRedListCategory || s.iucn_red_list_status || 'Unknown') as any,
    commercialImportance: (s.commercialImportance || s.commercial_importance || 'Unknown') as any,
    habitatType: (s.habitatType || s.habitat_type || 'Unknown') as any,
    occurrenceCount: Number(s.occurrenceCount ?? s.occurrences_count ?? 0),
    ednaDetectionCount: Number(s.ednaDetectionCount ?? s.edna_detection_count ?? 0),
    knownDepthRange: s.knownDepthRange || [
      s.depth_min !== undefined ? Number(s.depth_min) : 0,
      s.depth_max !== undefined ? Number(s.depth_max) : 0
    ],
    preferredTemperatureRange: s.preferredTemperatureRange || null,
    preferredSalinityRange: s.preferredSalinityRange || null,
    imageUrl: s.imageUrl || s.image_url,
    description: s.description || ''
  };
}

function normalizeOccurrence(o: any, speciesId: string): SpeciesOccurrence {
  return {
    id: String(o.id || ''),
    speciesId: String(o.speciesId || o.species_id || speciesId),
    scientificName: o.scientificName || o.scientific_name || '',
    commonName: o.commonName || o.common_name || '',
    recordedBy: o.recordedBy || o.recorded_by || '',
    eventDate: o.eventDate || o.event_date || o.observed_at || o.time || '',
    latitude: Number(o.latitude ?? 0),
    longitude: Number(o.longitude ?? 0),
    depthMeters: o.depthMeters ?? (o.depth !== undefined ? Number(o.depth) : 0),
    individualCount: o.individualCount ?? (o.individual_count !== undefined ? Number(o.individual_count) : 1),
    basisOfRecord: o.basisOfRecord || o.basis_of_record || 'HumanObservation',
    datasetId: o.datasetId || o.dataset_id || ''
  };
}

export const speciesService = {
  async getSpeciesList(search?: string): Promise<SpeciesRecord[]> {
    const res = await ApiClient.get<any[]>('/species', undefined, search ? { search } : undefined);
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map(normalizeSpecies);
  },

  async getSpeciesById(speciesId: string): Promise<SpeciesRecord> {
    const res = await ApiClient.get<any>(`/species/${speciesId}`);
    if (!res.data) throw new Error(`Species '${speciesId}' not found.`);
    return normalizeSpecies(res.data);
  },

  async getSpeciesOccurrences(speciesId: string): Promise<SpeciesOccurrence[]> {
    const res = await ApiClient.get<any[]>(`/species/${speciesId}/occurrences`);
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map(o => normalizeOccurrence(o, speciesId));
  }
};
