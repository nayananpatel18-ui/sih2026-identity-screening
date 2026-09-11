import React, { useState } from 'react';
import { HealthStatus, CanonicalDocumentSample } from '../types';
import { Server, Database, Cpu, Eye, CheckCircle2 } from 'lucide-react';

interface SystemStatusPageProps {
  health: HealthStatus | null;
  loadingHealth: boolean;
  sampleIds: string[];
  selectedSampleId: string;
  onSelectSampleId: (id: string) => void;
  sampleData: CanonicalDocumentSample | null;
  loadingSample: boolean;
}

export const SystemStatusPage: React.FC<SystemStatusPageProps> = ({
  health,
  loadingHealth,
  sampleIds,
  selectedSampleId,
  onSelectSampleId,
  sampleData,
  loadingSample
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Infrastructure Status Banner */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CheckCircle2 size={20} color="#34d399" />
            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>System Infrastructure & Data Adapter Layer</h3>
          </div>
          <span style={{ fontSize: '12px', backgroundColor: 'rgba(52, 211, 153, 0.15)', color: '#34d399', border: '1px solid rgba(52, 211, 153, 0.3)', padding: '4px 10px', borderRadius: '12px', fontWeight: 600 }}>
            HEALTHY
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Data Adapter Registration</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
              SyntheticDataAdapter (Active)
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
              Extensible points: MIDV-500, MIDV-2020, DocTamper, IDNet
            </div>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Backend API Health</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
              {loadingHealth ? 'Checking...' : health ? 'ONLINE (HTTP 200 OK)' : 'OFFLINE'}
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
              Version: {health?.version || '1.0.0'} | Timestamp: {health?.timestamp || 'N/A'}
            </div>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Database Storage Mode</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: health?.firebase_connected ? '#34d399' : '#fbbf24' }}>
              {health?.firebase_connected ? 'Firestore Live Connected' : 'Local Fallback Storage'}
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
              {health?.firebase_connected ? 'Production cloud sync enabled' : 'Safe local memory mode active'}
            </div>
          </div>
        </div>
      </div>

      {/* Data Adapter Inspector (Milestone 1 Preserved) */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
        {/* Left Column: Sample Selector */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginTop: 0, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} color="#60a5fa" /> Data Adapter Samples
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {sampleIds.map((id) => (
              <button
                key={id}
                onClick={() => onSelectSampleId(id)}
                style={{
                  textAlign: 'left',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: selectedSampleId === id ? '1px solid #3b82f6' : '1px solid #1e293b',
                  backgroundColor: selectedSampleId === id ? 'rgba(59, 130, 246, 0.15)' : '#1e293b',
                  color: '#f8fafc',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{id}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                  Synthetic demo input
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right Column: Canonical Data View */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Eye size={18} color="#34d399" /> Canonical Model Inspector: <code style={{ color: '#60a5fa' }}>{selectedSampleId}</code>
            </h3>
          </div>

          {loadingSample ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>Loading Canonical Representation...</div>
          ) : sampleData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Extracted Fields Summary */}
              <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', border: '1px solid #334155' }}>
                <h4 style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 12px 0' }}>
                  Extracted Document Fields (Canonical)
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '13px' }}>
                  <div><span style={{ color: '#64748b' }}>Full Name:</span> <strong>{sampleData.extracted_fields?.full_name || 'N/A'}</strong></div>
                  <div><span style={{ color: '#64748b' }}>Doc Number:</span> <strong>{sampleData.extracted_fields?.document_number || 'N/A'}</strong></div>
                  <div><span style={{ color: '#64748b' }}>Date of Birth:</span> <strong>{sampleData.extracted_fields?.dob || 'N/A'}</strong></div>
                  <div><span style={{ color: '#64748b' }}>Nationality:</span> <strong>{sampleData.extracted_fields?.nationality || 'N/A'}</strong></div>
                  <div><span style={{ color: '#64748b' }}>Expiry Date:</span> <strong>{sampleData.extracted_fields?.expiry_date || 'N/A'}</strong></div>
                  <div><span style={{ color: '#64748b' }}>Doc Type:</span> <strong>{sampleData.document_type}</strong></div>
                </div>
              </div>

              {/* Quality Metadata */}
              <div>
                <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Quality Metadata</div>
                  <div style={{ fontSize: '12px', lineHeight: '1.6' }}>
                    <div>Blur Score: <code>{sampleData.quality_metadata.blur_score}</code></div>
                    <div>Glare Detected: <code>{sampleData.quality_metadata.glare_detected ? 'YES' : 'NO'}</code></div>
                    <div>Sufficient Quality: <strong style={{ color: sampleData.quality_metadata.is_sufficient_quality ? '#34d399' : '#f87171' }}>{sampleData.quality_metadata.is_sufficient_quality ? 'TRUE' : 'FALSE'}</strong></div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: '#94a3b8' }}>Select a sample to inspect details.</div>
          )}
        </div>
      </div>
    </div>
  );
};
