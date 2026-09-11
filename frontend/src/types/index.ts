export type RiskLevel = 'GREEN' | 'AMBER' | 'RED' | 'GREY';

export interface QualityMetadata {
  blur_score: number;
  glare_detected: boolean;
  is_partial: boolean;
  resolution_w: number;
  resolution_h: number;
  is_sufficient_quality: boolean;
  notes?: string;
}

export interface CanonicalExtractedFields {
  given_names?: string;
  surname?: string;
  full_name?: string;
  dob?: string;
  gender?: string;
  nationality?: string;
  document_number?: string;
  expiry_date?: string;
  issue_date?: string;
  issuing_country?: string;
  mrz_raw?: string;
  raw_ocr_text?: string;
}

export interface GroundTruthMetadata {
  is_tampered: boolean;
  expected_risk: RiskLevel;
  tamper_details?: {
    is_tampered: boolean;
    tamper_types: string[];
    description?: string;
  };
}

export interface CanonicalDocumentSample {
  sample_id: string;
  source_dataset: string;
  document_type: string;
  document_image: string;
  secondary_document_image?: string;
  person_image?: string;
  extracted_fields?: CanonicalExtractedFields;
  quality_metadata: QualityMetadata;
  ground_truth?: GroundTruthMetadata;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  timestamp: string;
  firebase_connected: boolean;
  active_datasets: string[];
  version: string;
}
