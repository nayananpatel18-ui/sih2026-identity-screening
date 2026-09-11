import React from 'react';
import { FileSearch, Info, Network, ShieldAlert } from 'lucide-react';
import { ConflictItem, EvidenceSignal, MultimodalScreeningResult, RiskLevel } from '../types';

interface EvidenceExplanationPageProps { result: MultimodalScreeningResult | null; }

const riskColors: Record<RiskLevel, string> = { GREEN: '#34d399', AMBER: '#fbbf24', RED: '#f87171', GREY: '#cbd5e1' };

const Card: React.FC<React.PropsWithChildren<{ title: string }>> = ({ title, children }) => (
  <section style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
    <h4 style={{ fontSize: '14px', margin: '0 0 14px', color: '#f8fafc' }}>{title}</h4>{children}
  </section>
);

const SignalRow: React.FC<{ signal: EvidenceSignal }> = ({ signal }) => (
  <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', color: '#f8fafc', fontSize: '12px', fontWeight: 700 }}><span>{signal.title}</span><span>{signal.evidence_state}</span></div>
    <p style={{ color: '#94a3b8', fontSize: '12px', lineHeight: 1.45, margin: '7px 0' }}>{signal.description}</p>
    <div style={{ color: '#cbd5e1', fontSize: '11px' }}>Source: {signal.source} · Confidence: {signal.confidence.toFixed(2)} · Risk contribution: {signal.contribution.toFixed(2)}</div>
    {signal.limitation && <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '5px' }}>Limitation: {signal.limitation}</div>}
  </div>
);

const ConflictRow: React.FC<{ conflict: ConflictItem }> = ({ conflict }) => (
  <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px', color: '#cbd5e1', fontSize: '12px' }}>
    <strong style={{ color: '#f8fafc' }}>{conflict.field_name} — {conflict.conflict_type}</strong><div style={{ marginTop: '5px' }}>{conflict.explanation}</div>
    <div style={{ marginTop: '5px', color: '#94a3b8' }}>{conflict.source_a}: {conflict.value_a ?? 'Unavailable'} · {conflict.source_b}: {conflict.value_b ?? 'Unavailable'} · {conflict.resolution_status}</div>
  </div>
);

export const EvidenceExplanationPage: React.FC<EvidenceExplanationPageProps> = ({ result }) => {
  if (!result) return <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '60px', textAlign: 'center', color: '#94a3b8' }}><FileSearch size={40} color="#475569" style={{ marginBottom: '16px' }} /><h3 style={{ fontSize: '16px', color: '#f8fafc', margin: '0 0 8px' }}>No Screening Result Selected</h3><p style={{ fontSize: '13px', margin: 0 }}>Run a synthetic demo sample to inspect the deterministic backend screening result.</p></div>;

  const fields = result.extracted_fields;
  return <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
    <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '10px', padding: '14px 18px', display: 'flex', gap: '12px' }}><Info size={20} color="#60a5fa" /><div style={{ fontSize: '12px', color: '#93c5fd', lineHeight: 1.5 }}><strong>Synthetic Demo Result:</strong> This view renders the deterministic backend screening result. It is decision support only; final review remains with the officer.</div></div>
    <Card title="Screening Decision"><div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', fontSize: '12px' }}><div><div style={{ color: '#94a3b8' }}>Risk level</div><strong style={{ color: riskColors[result.risk_level], fontSize: '20px' }}>{result.risk_level}</strong></div><div><div style={{ color: '#94a3b8' }}>Risk score</div><strong>{result.risk_score.toFixed(2)}</strong></div><div><div style={{ color: '#94a3b8' }}>Uncertainty</div><strong>{result.uncertainty_score.toFixed(2)}</strong></div><div><div style={{ color: '#94a3b8' }}>Status</div><strong>{result.status}</strong></div></div><div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '14px' }}>Screening ID: {result.screening_id} · Sample ID: {result.sample_id} · Pipeline: {result.pipeline_version}</div></Card>
    <Card title="Officer Explanation & Recommendation"><p style={{ color: '#cbd5e1', fontSize: '13px', lineHeight: 1.55, margin: '0 0 10px' }}>{result.explanation}</p><strong style={{ color: riskColors[result.risk_level], fontSize: '13px' }}>{result.recommendation}</strong></Card>
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}><Card title={`Evidence Signals (${result.evidence_signals.length})`}><div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>{result.evidence_signals.map(signal => <SignalRow key={signal.signal_id} signal={signal} />)}</div></Card><Card title={`Explicit Conflicts (${result.conflicts.length})`}><div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>{result.conflicts.length ? result.conflicts.map(conflict => <ConflictRow key={conflict.conflict_id} conflict={conflict} />) : <div style={{ color: '#94a3b8', fontSize: '12px' }}>No explicit conflicts were identified by this screening result.</div>}</div></Card></div>
    <Card title="Extracted Fields & Quality Metadata"><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', color: '#cbd5e1', fontSize: '12px' }}><div><Network size={15} color="#60a5fa" /> <strong>Fields:</strong> {fields?.full_name ?? 'Unavailable'} · {fields?.document_number ?? 'Unavailable'} · {fields?.nationality ?? 'Unavailable'}</div><div><ShieldAlert size={15} color="#fbbf24" /> <strong>Quality:</strong> blur {result.quality_metadata.blur_score.toFixed(2)} · glare {result.quality_metadata.glare_detected ? 'yes' : 'no'} · sufficient {result.quality_metadata.is_sufficient_quality ? 'yes' : 'no'}</div></div></Card>
  </div>;
};
