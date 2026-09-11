import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { HealthStatus, CanonicalDocumentSample } from './types';
import { ShieldCheck, AlertTriangle, FileText, Database, Server, Cpu, CheckCircle, RefreshCw, Eye } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sampleIds, setSampleIds] = useState<string[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('CASE_001_GENUINE');
  const [sampleData, setSampleData] = useState<CanonicalDocumentSample | null>(null);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    setError(null);
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend API');
    } finally {
      setLoadingHealth(false);
    }
  };

  const fetchSamplesList = async () => {
    try {
      const samples = await api.listSamples('synthetic');
      setSampleIds(samples);
      if (samples.length > 0 && !selectedSampleId) {
        setSelectedSampleId(samples[0]);
      }
    } catch (err) {
      console.error('Failed to list samples:', err);
    }
  };

  const fetchSampleDetails = async (id: string) => {
    setLoadingSample(true);
    try {
      const sample = await api.getSample(id, 'synthetic');
      setSampleData(sample);
    } catch (err) {
      console.error(`Failed to fetch sample ${id}:`, err);
    } finally {
      setLoadingSample(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchSamplesList();
  }, []);

  useEffect(() => {
    if (selectedSampleId) {
      fetchSampleDetails(selectedSampleId);
    }
  }, [selectedSampleId]);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#090d16', color: '#f1f5f9', fontFamily: 'Inter, sans-serif' }}>
      {/* Header Bar */}
      <header style={{ backgroundColor: '#0f172a', borderBottom: '1px solid #1e293b', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#1e3a8a', padding: '8px', borderRadius: '8px', display: 'flex' }}>
            <ShieldCheck size={24} color="#60a5fa" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, margin: 0, letterSpacing: '0.02em', color: '#f8fafc' }}>
              SIH 2026 — AI Identity Screening & Fraud Resilience System
            </h1>
            <p style={{ fontSize: '12px', margin: 0, color: '#94a3b8' }}>
              Ministry of Home Affairs (MHA) | Sashastra Seema Bal (SSB)
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', backgroundColor: '#1e293b', padding: '6px 12px', borderRadius: '6px', border: '1px solid #334155' }}>
            <Server size={14} color={health ? '#34d399' : '#f87171'} />
            <span>Backend: </span>
            <strong style={{ color: health ? '#34d399' : '#f87171' }}>
              {loadingHealth ? 'Checking...' : health ? 'ONLINE' : 'DISCONNECTED'}
            </strong>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', backgroundColor: '#1e293b', padding: '6px 12px', borderRadius: '6px', border: '1px solid #334155' }}>
            <Database size={14} color={health?.firebase_connected ? '#34d399' : '#fbbf24'} />
            <span>Database: </span>
            <strong style={{ color: health?.firebase_connected ? '#34d399' : '#fbbf24' }}>
              {health?.firebase_connected ? 'Firestore Connected' : 'Local Fallback'}
            </strong>
          </div>

          <button
            onClick={fetchHealth}
            style={{ backgroundColor: '#3b82f6', border: 'none', color: '#fff', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600 }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Status / Milestone Banner */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle size={20} color="#34d399" />
              <h2 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>Milestone 1: Foundation & Data Layer Architecture</h2>
            </div>
            <span style={{ fontSize: '12px', backgroundColor: 'rgba(52, 211, 153, 0.15)', color: '#34d399', border: '1px solid rgba(52, 211, 153, 0.3)', padding: '4px 10px', borderRadius: '12px', fontWeight: 600 }}>
              VERIFIED ACTIVE
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '16px' }}>
            <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Canonical Data Adapter</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                SyntheticDataAdapter (Registered)
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                Extensible points: MIDV-500, MIDV-2020, DocTamper, IDNet
              </div>
            </div>

            <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>FastAPI Endpoint Status</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                {health ? `/api/health (HTTP 200)` : 'Offline'}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                CORS, Settings, & OpenAPI Swagger Configured
              </div>
            </div>

            <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Ground-Truth Evaluation</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                3 Core Demo Cases (GREEN, RED, GREY)
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                Deterministic demonstration dataset initialized
              </div>
            </div>
          </div>
        </div>

        {/* Data Adapter Inspector */}
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
                  onClick={() => setSelectedSampleId(id)}
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
                    {id.includes('GENUINE') ? '🟢 GREEN / Low Risk' : id.includes('TAMPERED') ? '🔴 RED / High Risk' : '⚪ GREY / Quality Issue'}
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

              {sampleData?.ground_truth && (
                <span
                  className={
                    sampleData.ground_truth.expected_risk === 'GREEN' ? 'badge-green' :
                    sampleData.ground_truth.expected_risk === 'RED' ? 'badge-red' : 'badge-grey'
                  }
                  style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 700 }}
                >
                  EXPECTED: {sampleData.ground_truth.expected_risk}
                </span>
              )}
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

                {/* Quality & Tamper Metadata */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Quality Metadata</div>
                    <div style={{ fontSize: '12px', lineHeight: '1.6' }}>
                      <div>Blur Score: <code>{sampleData.quality_metadata.blur_score}</code></div>
                      <div>Glare Detected: <code>{sampleData.quality_metadata.glare_detected ? 'YES' : 'NO'}</code></div>
                      <div>Sufficient Quality: <strong style={{ color: sampleData.quality_metadata.is_sufficient_quality ? '#34d399' : '#f87171' }}>{sampleData.quality_metadata.is_sufficient_quality ? 'TRUE' : 'FALSE'}</strong></div>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#1e293b', padding: '14px', borderRadius: '8px', border: '1px solid #334155' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Ground Truth Tampering</div>
                    <div style={{ fontSize: '12px', lineHeight: '1.6' }}>
                      <div>Is Tampered: <strong style={{ color: sampleData.ground_truth?.is_tampered ? '#f87171' : '#34d399' }}>{sampleData.ground_truth?.is_tampered ? 'YES' : 'NO'}</strong></div>
                      <div>Tamper Types: <code>{sampleData.ground_truth?.tamper_details?.tamper_types.join(', ') || 'None'}</code></div>
                      {sampleData.ground_truth?.tamper_details?.description && (
                        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>{sampleData.ground_truth.tamper_details.description}</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Raw JSON View */}
                <div>
                  <h4 style={{ fontSize: '13px', color: '#94a3b8', margin: '8px 0 8px 0' }}>Raw Canonical JSON</h4>
                  <pre style={{ backgroundColor: '#020617', padding: '14px', borderRadius: '8px', border: '1px solid #1e293b', overflowX: 'auto', fontSize: '12px', color: '#a7f3d0' }}>
                    {JSON.stringify(sampleData, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div style={{ color: '#94a3b8' }}>Select a sample to inspect details.</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
