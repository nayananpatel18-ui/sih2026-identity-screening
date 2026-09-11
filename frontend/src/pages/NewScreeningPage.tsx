import React, { useState } from 'react';
import { Upload, FileText, User, Play, AlertCircle, CheckCircle2, HelpCircle, Info, ShieldAlert } from 'lucide-react';
import { api, getApiErrorMessage } from '../services/api';
import { CanonicalDocumentSample, UploadFileResponse } from '../types';

interface NewScreeningPageProps {
  onLoadPreset: (sampleId: string) => Promise<CanonicalDocumentSample | null>;
  onStartScreening: (sampleId: string) => Promise<void>;
  isAuthenticated: boolean;
  onRequireAuthentication: () => void;
}

export const NewScreeningPage: React.FC<NewScreeningPageProps> = ({ onLoadPreset, onStartScreening, isAuthenticated, onRequireAuthentication }) => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('CASE_001_GENUINE');
  const [activeSample, setActiveSample] = useState<CanonicalDocumentSample | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedUploadFile, setSelectedUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<UploadFileResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [screeningError, setScreeningError] = useState<string | null>(null);

  const handleSelectPreset = async (presetId: string) => {
    setSelectedPresetId(presetId);
    setIsLoading(true);
    const sample = await onLoadPreset(presetId);
    setActiveSample(sample);
    setIsLoading(false);
  };

  React.useEffect(() => {
    handleSelectPreset('CASE_001_GENUINE');
  }, []);

  const handleUploadSelectedFile = async () => {
    if (!selectedUploadFile) {
      return;
    }
    if (!isAuthenticated) {
      onRequireAuthentication();
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      const result = await api.uploadFile(selectedUploadFile, 'primary_document');
      setUploadResult(result);
    } catch (err: unknown) {
      setUploadError(getApiErrorMessage(err, 'Upload failed. Please choose a valid image file.'));
      setUploadResult(null);
    } finally {
      setUploading(false);
    }
  };

  const handleStartScreening = async () => {
    if (!isAuthenticated) {
      onRequireAuthentication();
      return;
    }
    setScreeningError(null);
    try {
      await onStartScreening(selectedPresetId);
    } catch (err: unknown) {
      setScreeningError(getApiErrorMessage(err, 'Screening could not be started.'));
    }
  };

  const handleUploadFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedUploadFile(file);
    setUploadResult(null);
    setUploadError(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Notice Banner - Technical Honesty */}
      <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '10px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Info size={20} color="#60a5fa" />
        <div style={{ fontSize: '12px', color: '#93c5fd', lineHeight: '1.5' }}>
          <strong>Deterministic Demo Pipeline:</strong> Select a synthetic preset and run it through the backend screening API. OCR, face matching, and visual-forensics modules are planned for later milestones.
        </div>
      </div>

      {/* Quick Load Synthetic Presets Bar */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
            Select Synthetic Demo Case (De-identified Dataset)
          </h3>
          <span style={{ fontSize: '10px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', backgroundColor: '#1e293b', color: '#64748b', border: '1px solid #334155' }}>
            DEMO PRESETS
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
          {/* Preset 1: Genuine */}
          <button
            onClick={() => handleSelectPreset('CASE_001_GENUINE')}
            style={{
              textAlign: 'left',
              padding: '14px',
              borderRadius: '8px',
              border: selectedPresetId === 'CASE_001_GENUINE' ? '1px solid #10b981' : '1px solid #1e293b',
              backgroundColor: selectedPresetId === 'CASE_001_GENUINE' ? 'rgba(16, 185, 129, 0.1)' : '#1e293b',
              cursor: 'pointer',
              color: '#f8fafc'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 700 }}>CASE 1 — GENUINE</span>
              <CheckCircle2 size={16} color="#34d399" />
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Valid passport, consistent MRZ, matching face photo, dates consistent.
            </div>
            <div style={{ marginTop: '8px', fontSize: '10px', fontWeight: 700, color: '#34d399' }}>
              EXPECTED: GREEN / LOW RISK
            </div>
          </button>

          {/* Preset 2: Tampered */}
          <button
            onClick={() => handleSelectPreset('CASE_002_TAMPERED')}
            style={{
              textAlign: 'left',
              padding: '14px',
              borderRadius: '8px',
              border: selectedPresetId === 'CASE_002_TAMPERED' ? '1px solid #ef4444' : '1px solid #1e293b',
              backgroundColor: selectedPresetId === 'CASE_002_TAMPERED' ? 'rgba(239, 68, 68, 0.1)' : '#1e293b',
              cursor: 'pointer',
              color: '#f8fafc'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 700 }}>CASE 2 — TAMPERED</span>
              <AlertCircle size={16} color="#f87171" />
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              DOB visual field modified, MRZ checksum mismatch, photo replaced.
            </div>
            <div style={{ marginTop: '8px', fontSize: '10px', fontWeight: 700, color: '#f87171' }}>
              EXPECTED: RED / HIGH RISK
            </div>
          </button>

          {/* Preset 3: Uncertain */}
          <button
            onClick={() => handleSelectPreset('CASE_003_UNCERTAIN')}
            style={{
              textAlign: 'left',
              padding: '14px',
              borderRadius: '8px',
              border: selectedPresetId === 'CASE_003_UNCERTAIN' ? '1px solid #94a3b8' : '1px solid #1e293b',
              backgroundColor: selectedPresetId === 'CASE_003_UNCERTAIN' ? 'rgba(148, 163, 184, 0.1)' : '#1e293b',
              cursor: 'pointer',
              color: '#f8fafc'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 700 }}>CASE 3 — UNCERTAIN</span>
              <HelpCircle size={16} color="#cbd5e1" />
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Motion blur, unreadable MRZ zone, severe glare. Insufficient quality.
            </div>
            <div style={{ marginTop: '8px', fontSize: '10px', fontWeight: 700, color: '#cbd5e1' }}>
              EXPECTED: GREY / HUMAN REVIEW
            </div>
          </button>
        </div>
      </div>

      {/* Uploaded File Intake (Local Temporary Demo Storage) */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', margin: 0 }}>Uploaded File (Local Temporary Demo)</h3>
            <p style={{ fontSize: '11px', color: '#94a3b8', margin: '4px 0 0 0' }}>
              This is a demo-only upload flow. Uploaded images are stored locally and are not processed by real OCR, face matching, or government verification.
            </p>
          </div>
          <span style={{ fontSize: '10px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', backgroundColor: '#1e293b', color: '#cbd5e1', border: '1px solid #334155' }}>
            M3 UPLOAD
          </span>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
          <label
            htmlFor="demo-upload-input"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 16px',
              borderRadius: '8px',
              border: '1px solid #334155',
              backgroundColor: '#1e293b',
              color: '#f8fafc',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Upload size={16} color="#60a5fa" />
            Select Image
          </label>
          <input
            id="demo-upload-input"
            type="file"
            accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
            onChange={handleUploadFileChange}
            style={{ display: 'none' }}
          />

          <button
            onClick={handleUploadSelectedFile}
            disabled={!selectedUploadFile || uploading}
            style={{
              backgroundColor: selectedUploadFile ? '#2563eb' : '#374151',
              border: 'none',
              color: '#ffffff',
              padding: '10px 16px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: selectedUploadFile ? 'pointer' : 'not-allowed',
            }}
          >
            {uploading ? 'Uploading...' : 'Upload Selected File'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px' }}>
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px' }}>
            <div style={{ color: '#94a3b8', marginBottom: '4px' }}>Selected file</div>
            <div style={{ color: '#f8fafc', fontWeight: 600 }}>
              {selectedUploadFile ? selectedUploadFile.name : 'No file selected'}
            </div>
          </div>

          <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px' }}>
            <div style={{ color: '#94a3b8', marginBottom: '4px' }}>Allowed formats</div>
            <div style={{ color: '#f8fafc', fontWeight: 600 }}>PNG, JPG, JPEG, WEBP (demo-safe local upload)</div>
          </div>
        </div>

        {uploadError && (
          <div style={{ marginTop: '14px', backgroundColor: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.5)', borderRadius: '8px', padding: '10px 12px', color: '#fca5a5', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={14} color="#fca5a5" />
              {uploadError}
            </div>
          </div>
        )}

        {uploadResult && (
          <div style={{ marginTop: '14px', backgroundColor: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '8px', padding: '12px', color: '#a7f3d0', fontSize: '12px' }}>
            <div style={{ fontWeight: 700, marginBottom: '6px' }}>Upload confirmed</div>
            <div>file_id: {uploadResult.file_id}</div>
            <div>upload_session_id: {uploadResult.upload_session_id || uploadResult.file_id}</div>
            <div>original_filename: {uploadResult.original_filename}</div>
            <div>size_bytes: {uploadResult.size_bytes}</div>
            <div>content_type: {uploadResult.content_type}</div>
            <div style={{ marginTop: '6px', color: '#d1fae5' }}>
              This upload establishes a local temporary input/session reference only. Synthetic demo screening remains separate and unchanged.
            </div>
          </div>
        )}
      </div>

      {/* Multimodal File Intake Dropzones */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        {/* Dropzone 1: Primary Document */}
        <div style={{ backgroundColor: '#0f172a', border: '1px dashed #334155', borderRadius: '12px', padding: '24px', textAlign: 'center' }}>
          <div style={{ backgroundColor: '#1e293b', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
            <FileText size={22} color="#60a5fa" />
          </div>
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 4px 0' }}>Primary Document</h4>
          <p style={{ fontSize: '11px', color: '#94a3b8', margin: '0 0 16px 0' }}>Passport / National ID Card</p>

          {activeSample?.document_image ? (
            <div style={{ backgroundColor: '#1e293b', padding: '10px', borderRadius: '6px', fontSize: '12px', color: '#34d399', border: '1px solid #334155' }}>
              ✓ Synthetic Loaded: {activeSample.document_image.split('/').pop()}
            </div>
          ) : (
            <div style={{ border: '1px dashed #475569', padding: '16px', borderRadius: '8px', fontSize: '12px', color: '#64748b' }}>
              Drag & drop document image or browse
            </div>
          )}
        </div>

        {/* Dropzone 2: Secondary Document */}
        <div style={{ backgroundColor: '#0f172a', border: '1px dashed #334155', borderRadius: '12px', padding: '24px', textAlign: 'center' }}>
          <div style={{ backgroundColor: '#1e293b', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
            <Upload size={22} color="#a7f3d0" />
          </div>
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 4px 0' }}>Secondary Document</h4>
          <p style={{ fontSize: '11px', color: '#94a3b8', margin: '0 0 16px 0' }}>Visa / Secondary ID (Optional)</p>

          {activeSample?.secondary_document_image ? (
            <div style={{ backgroundColor: '#1e293b', padding: '10px', borderRadius: '6px', fontSize: '12px', color: '#34d399', border: '1px solid #334155' }}>
              ✓ Synthetic Loaded: {activeSample.secondary_document_image.split('/').pop()}
            </div>
          ) : (
            <div style={{ border: '1px dashed #475569', padding: '16px', borderRadius: '8px', fontSize: '12px', color: '#64748b' }}>
              Optional cross-validation document
            </div>
          )}
        </div>

        {/* Dropzone 3: Person Live Photo */}
        <div style={{ backgroundColor: '#0f172a', border: '1px dashed #334155', borderRadius: '12px', padding: '24px', textAlign: 'center' }}>
          <div style={{ backgroundColor: '#1e293b', width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
            <User size={22} color="#fcd34d" />
          </div>
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 4px 0' }}>Live Person Photo</h4>
          <p style={{ fontSize: '11px', color: '#94a3b8', margin: '0 0 16px 0' }}>Biometric Verification Photo</p>

          {activeSample?.person_image ? (
            <div style={{ backgroundColor: '#1e293b', padding: '10px', borderRadius: '6px', fontSize: '12px', color: '#34d399', border: '1px solid #334155' }}>
              ✓ Synthetic Loaded: {activeSample.person_image.split('/').pop()}
            </div>
          ) : (
            <div style={{ border: '1px dashed #475569', padding: '16px', borderRadius: '8px', fontSize: '12px', color: '#64748b' }}>
              Upload live facial capture
            </div>
          )}
        </div>
      </div>

      {/* Loaded Preset Canonical Preview & Action */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 4px 0' }}>
            Selected Synthetic Sample: <code style={{ color: '#60a5fa' }}>{selectedPresetId}</code>
          </h4>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
            Extracted Name: <strong>{activeSample?.extracted_fields?.full_name || 'Loading...'}</strong> | Doc #: <strong>{activeSample?.extracted_fields?.document_number || 'N/A'}</strong>
          </p>
        </div>

        <button
          onClick={handleStartScreening}
          disabled={isLoading || !activeSample}
          style={{
            backgroundColor: '#2563eb',
            border: 'none',
            color: '#ffffff',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
          }}
        >
          <Play size={16} /> [DEMO] Inspect Evidence & Explanation
        </button>
      </div>
      {screeningError && <div style={{ color: '#fca5a5', fontSize: '12px', display: 'flex', gap: '8px' }}><ShieldAlert size={14} />{screeningError}</div>}
    </div>
  );
};
