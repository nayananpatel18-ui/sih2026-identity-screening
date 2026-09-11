import React, { useState } from 'react';
import { History, Eye, Filter, Info } from 'lucide-react';
import { RiskLevel } from '../types';

interface DemoHistoryItem {
  id: string;
  sampleId: string;
  applicantName: string;
  docNumber: string;
  docType: string;
  riskLevel: RiskLevel;
  riskScore: number;
  uncertaintyScore: number;
  timestamp: string;
  summary: string;
}

const mockHistoryData: DemoHistoryItem[] = [
  {
    id: 'DEMO-SCR-001',
    sampleId: 'CASE_001_GENUINE',
    applicantName: 'RAJESH KUMAR SHARMA',
    docNumber: 'Z1234567',
    docType: 'PASSPORT',
    riskLevel: 'GREEN',
    riskScore: 0.05,
    uncertaintyScore: 0.02,
    timestamp: '2026-09-11 14:10:00',
    summary: 'All OCR, MRZ, dates, and biometric signals passed structural and visual validation.'
  },
  {
    id: 'DEMO-SCR-002',
    sampleId: 'CASE_002_TAMPERED',
    applicantName: 'ANITA ROY',
    docNumber: 'K9876543',
    docType: 'PASSPORT',
    riskLevel: 'RED',
    riskScore: 0.92,
    uncertaintyScore: 0.05,
    timestamp: '2026-09-11 14:22:15',
    summary: 'DOB visual mismatch with MRZ checksum, face embedding disparity, photo replacement signal.'
  },
  {
    id: 'DEMO-SCR-003',
    sampleId: 'CASE_003_UNCERTAIN',
    applicantName: 'VIKRAM S???',
    docNumber: 'J55??89',
    docType: 'PASSPORT',
    riskLevel: 'GREY',
    riskScore: 0.45,
    uncertaintyScore: 0.88,
    timestamp: '2026-09-11 14:35:40',
    summary: 'High motion blur and specular glare. Insufficient visual clarity for automated assessment.'
  }
];

interface ScreeningHistoryPageProps {
  onSelectScreening: (sampleId: string) => void;
}

export const ScreeningHistoryPage: React.FC<ScreeningHistoryPageProps> = ({ onSelectScreening }) => {
  const [filter, setFilter] = useState<string>('ALL');

  const filteredData = mockHistoryData.filter((item) => {
    if (filter === 'ALL') return true;
    return item.riskLevel === filter;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Demo Notice Banner */}
      <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '10px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Info size={20} color="#60a5fa" />
        <div style={{ fontSize: '12px', color: '#93c5fd', lineHeight: '1.5' }}>
          <strong>Synthetic Audit Log Demo:</strong> The records below demonstrate the historical screening trail structure. Risk signals represent decision support flags for human officer review and do not constitute automated legal fraud determinations.
        </div>
      </div>

      {/* Header & Filter Controls */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <History size={20} color="#60a5fa" />
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600, margin: 0 }}>Screening Audit Trail (Synthetic Demo Records)</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: '2px 0 0 0' }}>Sample audit log schema ready for Firestore integration</p>
          </div>
        </div>

        {/* Risk Filter Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={14} color="#64748b" />
          {['ALL', 'GREEN', 'AMBER', 'RED', 'GREY'].map((level) => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: filter === level ? '1px solid #3b82f6' : '1px solid #1e293b',
                backgroundColor: filter === level ? '#1e3a8a' : '#1e293b',
                color: filter === level ? '#ffffff' : '#94a3b8',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* History Log Table */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#1e293b', borderBottom: '1px solid #334155', color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <th style={{ padding: '14px 18px' }}>Audit ID</th>
              <th style={{ padding: '14px 18px' }}>Applicant Name</th>
              <th style={{ padding: '14px 18px' }}>Document #</th>
              <th style={{ padding: '14px 18px' }}>Risk Signal</th>
              <th style={{ padding: '14px 18px' }}>Suspicion Index</th>
              <th style={{ padding: '14px 18px' }}>Uncertainty</th>
              <th style={{ padding: '14px 18px' }}>Timestamp</th>
              <th style={{ padding: '14px 18px', textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr key={item.id} style={{ borderBottom: '1px solid #1e293b', transition: 'background-color 0.15s ease' }}>
                <td style={{ padding: '16px 18px', fontWeight: 600, color: '#60a5fa' }}>{item.id}</td>
                <td style={{ padding: '16px 18px', color: '#f8fafc', fontWeight: 500 }}>{item.applicantName}</td>
                <td style={{ padding: '16px 18px', color: '#cbd5e1', fontFamily: 'monospace' }}>{item.docNumber}</td>
                <td style={{ padding: '16px 18px' }}>
                  <span
                    className={
                      item.riskLevel === 'GREEN' ? 'badge-green' :
                      item.riskLevel === 'RED' ? 'badge-red' : 'badge-grey'
                    }
                    style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 700 }}
                  >
                    {item.riskLevel}
                  </span>
                </td>
                <td style={{ padding: '16px 18px', color: item.riskScore > 0.5 ? '#f87171' : '#34d399', fontWeight: 600 }}>
                  {(item.riskScore * 100).toFixed(0)}%
                </td>
                <td style={{ padding: '16px 18px', color: item.uncertaintyScore > 0.5 ? '#fbbf24' : '#94a3b8' }}>
                  {(item.uncertaintyScore * 100).toFixed(0)}%
                </td>
                <td style={{ padding: '16px 18px', color: '#64748b', fontSize: '12px' }}>{item.timestamp}</td>
                <td style={{ padding: '16px 18px', textAlign: 'right' }}>
                  <button
                    onClick={() => onSelectScreening(item.sampleId)}
                    style={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      color: '#60a5fa',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Eye size={13} /> View Evidence
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
