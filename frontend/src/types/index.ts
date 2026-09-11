export type RiskLevel = 'GREEN' | 'AMBER' | 'RED' | 'GREY';
export type EvidenceState = 'POSITIVE' | 'NEGATIVE' | 'MISSING' | 'UNAVAILABLE' | 'UNRELIABLE' | 'NOT_APPLICABLE';
export type SignalCategory = 'DOCUMENT_INTELLIGENCE' | 'STRUCTURAL_VALIDATION' | 'VISUAL_FORENSIC' | 'BIOMETRIC_VERIFICATION' | 'CROSS_DOCUMENT_CONSISTENCY';
export type SignalSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ConflictType = 'ACTUAL_CONTRADICTION' | 'UNREADABLE_EVIDENCE' | 'UNRELIABLE_EVIDENCE' | 'MISSING_EVIDENCE';
export type BiometricMatchResult = 'MATCH' | 'MISMATCH' | 'INCONCLUSIVE' | 'UNAVAILABLE';

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

export interface CanonicalDocumentSample {
  sample_id: string;
  source_dataset: string;
  document_type: string;
  document_image: string;
  secondary_document_image?: string;
  person_image?: string;
  extracted_fields?: CanonicalExtractedFields;
  quality_metadata: QualityMetadata;
  created_at: string;
}

export interface EvidenceSignal {
  signal_id: string;
  source: string;
  category: SignalCategory;
  evidence_state: EvidenceState;
  severity: SignalSeverity;
  title: string;
  description: string;
  confidence: number;
  contribution: number;
  limitation?: string;
  raw_details: Record<string, unknown>;
}

export interface ConflictItem {
  conflict_id: string;
  source_a: string;
  source_b: string;
  field_name: string;
  value_a?: string;
  value_b?: string;
  conflict_type: ConflictType;
  severity: SignalSeverity;
  confidence: number;
  impact: number;
  resolvable: boolean;
  resolution_status: string;
  explanation: string;
}

export interface MultimodalScreeningResult {
  screening_id: string;
  sample_id: string;
  created_at: string;
  status: string;
  risk_level: RiskLevel;
  risk_score: number;
  uncertainty_score: number;
  extracted_fields?: CanonicalExtractedFields;
  quality_metadata: QualityMetadata;
  evidence_signals: EvidenceSignal[];
  conflicts: ConflictItem[];
  biometric_result: BiometricMatchResult;
  explanation: string;
  recommendation: string;
  pipeline_version: string;
}

export interface UploadFileResponse {
  file_id: string;
  upload_session_id?: string;
  doc_type?: string;
  original_filename: string;
  size_bytes: number;
  content_type: string;
  status: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  timestamp: string;
  firebase_connected: boolean;
  active_datasets: string[];
  version: string;
}
