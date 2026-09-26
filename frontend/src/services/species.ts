import { ApiClient } from './api';
import { 
  SpeciesRecord, 
  SpeciesOccurrence,
  SpeciesIdentificationResponse,
  SpeciesModelInfoResponse,
} from '../types/species';

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
  },

  async identifySpecies(file: File, topK: number = 3): Promise<SpeciesIdentificationResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await ApiClient.post<any>(`/species/identify?top_k=${topK}`, formData);
    const d = res.data;
    if (!d) throw new Error('No prediction received from species identification model.');

    return {
      species: d.species || '',
      commonName: d.common_name || d.commonName || '',
      family: d.family || '',
      confidence: Number(d.confidence ?? 0),
      confidenceTier: d.confidence_tier || d.confidenceTier || 'LOW',
      confidencePercent: Number(d.confidence_percent ?? (d.confidence ? d.confidence * 100 : 0)),
      wormsAphiaId: d.worms_aphia_id ?? d.wormsAphiaId,
      iucnStatus: d.iucn_status || d.iucnStatus,
      habitat: d.habitat,
      topPredictions: Array.isArray(d.top_predictions)
        ? d.top_predictions.map((p: any) => ({
            species: p.species || '',
            commonName: p.common_name || p.commonName || '',
            family: p.family || '',
            classId: Number(p.class_id ?? p.classId ?? 0),
            confidence: Number(p.confidence ?? 0),
            confidencePercent: Number(p.confidence_percent ?? (p.confidence ? p.confidence * 100 : 0)),
            order: p.order,
            wormsAphiaId: p.worms_aphia_id ?? p.wormsAphiaId,
            iucnStatus: p.iucn_status || p.iucnStatus,
            habitat: p.habitat,
            depthRangeM: p.depth_range_m ?? p.depthRangeM,
          }))
        : [],
      modelVersion: d.model_version || d.modelVersion || '1.0.0',
      modelArchitecture: d.model_architecture || d.modelArchitecture || 'ResNet-18',
      device: d.device || 'cpu',
      inferenceTimeMs: Number(d.inference_time_ms ?? d.inferenceTimeMs ?? 0),
    };
  },

  async getSpeciesModelInfo(): Promise<SpeciesModelInfoResponse> {
    const res = await ApiClient.get<any>('/species/identify/model-info');
    const d = res.data;
    return {
      modelName: d.model_name || d.modelName || 'MarineSpeciesClassifier',
      architecture: d.architecture || 'ResNet-18',
      version: d.version || '1.0.0',
      numClasses: Number(d.num_classes ?? d.numClasses ?? 10),
      classes: Array.isArray(d.classes) ? d.classes : [],
      supportedSpecies: Array.isArray(d.supported_species)
        ? d.supported_species.map((s: any) => ({
            classId: Number(s.class_id ?? s.classId ?? 0),
            scientificName: s.scientific_name || s.scientificName || '',
            commonName: s.common_name || s.commonName || '',
            family: s.family || '',
            order: s.order,
            class: s.class_name || s.class,
            wormsAphiaId: s.worms_aphia_id ?? s.wormsAphiaId,
            iucnStatus: s.iucn_status || s.iucnStatus,
            trophicGuild: s.trophic_guild || s.trophicGuild,
            habitat: s.habitat,
            depthRangeM: s.depth_range_m ?? s.depthRangeM,
          }))
        : [],
      inputResolution: d.input_resolution || [224, 224, 3],
      device: d.device || 'cpu',
      status: d.status || 'ready',
    };
  },

  async getSpeciesHealth(): Promise<{ status: string; model: string; version: string; classes: number }> {
    const res = await ApiClient.get<any>('/species/health');
    return res.data;
  }
};

