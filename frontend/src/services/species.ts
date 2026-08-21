import { ApiClient } from './api';
import { SpeciesRecord, SpeciesOccurrence } from '../types/species';
import { MOCK_SPECIES } from './mockData';

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
    const res = await ApiClient.get<SpeciesRecord[]>('/species', fallback, search ? { search } : undefined);
    return res.data;
  },

  async getSpeciesById(speciesId: string): Promise<SpeciesRecord> {
    const fallback = MOCK_SPECIES.find(s => s.id === speciesId) || MOCK_SPECIES[0];
    const res = await ApiClient.get<SpeciesRecord>(`/species/${speciesId}`, fallback);
    return res.data;
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

    const res = await ApiClient.get<SpeciesOccurrence[]>(`/species/${speciesId}/occurrences`, fallback);
    return res.data;
  }
};
