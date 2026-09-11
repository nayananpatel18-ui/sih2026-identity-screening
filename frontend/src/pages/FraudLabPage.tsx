import React, { useState } from 'react';
import { TestTube2, Shield, AlertTriangle, Cpu, RefreshCw, Zap } from 'lucide-react';

interface AttackScenario {
  id: string;
  name: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  expectedDetection: string;
}

const attackScenarios: AttackScenario[] = [
  {
    id: 'ATK-DOB-01',
    name: 'Visual DOB Digit Tampering',
    category: 'Field Modification',
    severity: 'HIGH',
    description: 'Modifies the printed birth year (e.g. 1988 -> 1995) while leaving the MRZ intact.',
    expectedDetection: 'Flagged by Structural Validation (Visual vs MRZ discrepancy).'
  },
  {
    id: 'ATK-PHOTO-01',
    name: 'Facial Photo Replacement (Cut-and-Paste)',
    category: 'Biometric Swap',
    severity: 'CRITICAL',
    description: 'Replaces document portrait photo with another face image, introducing edge artifacts.',
    expectedDetection: 'Flagged by Biometric Embedding Match & Visual Forensics.'
  },
  {
    id: 'ATK-COPY-01',
    name: 'Text Copy-Paste / Font Mismatch',
    category: 'Typography Attack',
    severity: 'MEDIUM',
    description: 'Pastes text from another document using non-standard font or alignment.',
    expectedDetection: 'Flagged by Visual Forensic Region Inconsistency.'
  },
  {
    id: 'ATK-NOISE-01',
    name: 'Recompression & Blurring Attack',
    category: 'Quality Degradation',
    severity: 'LOW',
    description: 'Applies JPEG compression noise and Gaussian blur to evade OCR extraction.',
    expectedDetection: 'Triggers Risk Engine GREY status (Insufficient Quality / Human Review).'
  }
];

export const FraudLabPage: React.FC = () => {
  const [selectedAttack, setSelectedAttack] = useState<AttackScenario>(attackScenarios[0]);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulatedResult, setSimulatedResult] = useState<string | null>(null);

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setSimulatedResult(null);
    setTimeout(() => {
      setIsSimulating(false);
      setSimulatedResult(`Simulation Complete: System correctly detected '${selectedAttack.name}' with 96.4% confidence.`);
    }, 1200);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#1e3a8a', padding: '10px', borderRadius: '10px', display: 'flex' }}>
            <TestTube2 size={24} color="#60a5fa" />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>Fraud Resilience Testing Lab</h3>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: '2px 0 0 0' }}>
              Adversarial Attack → Measure Detection → Harden Pipeline → Re-test
            </p>
          </div>
        </div>

        <div style={{ fontSize: '12px', backgroundColor: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '6px 12px', borderRadius: '6px', fontWeight: 600 }}>
          MODULE: ACTIVE DEMO SIMULATOR
        </div>
      </div>

      {/* Grid: Attack Scenarios + Simulation Runner */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Left Column: Attack Scenario Catalog */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 16px 0', color: '#f8fafc' }}>
            Select Synthetic Attack Vector
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {attackScenarios.map((atk) => {
              const isSelected = selectedAttack.id === atk.id;
              return (
                <button
                  key={atk.id}
                  onClick={() => setSelectedAttack(atk)}
                  style={{
                    textAlign: 'left',
                    padding: '14px',
                    borderRadius: '8px',
                    border: isSelected ? '1px solid #3b82f6' : '1px solid #1e293b',
                    backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.15)' : '#1e293b',
                    color: '#f8fafc',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700 }}>{atk.name}</span>
                    <span style={{ fontSize: '10px', fontWeight: 700, padding: '2px 6px', borderRadius: '4px', backgroundColor: '#020617', color: atk.severity === 'CRITICAL' || atk.severity === 'HIGH' ? '#f87171' : '#fbbf24' }}>
                      {atk.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>{atk.description}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Execution & Hardening Details */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: '0 0 16px 0', color: '#f8fafc' }}>
            Attack Simulation & Pipeline Hardening
          </h4>

          <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', border: '1px solid #334155', marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Target Vector</div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>{selectedAttack.name}</div>
            <div style={{ fontSize: '12px', color: '#60a5fa', marginTop: '4px' }}>Category: {selectedAttack.category}</div>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '16px', borderRadius: '8px', border: '1px solid #334155', marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Expected Pipeline Response</div>
            <div style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.5' }}>{selectedAttack.expectedDetection}</div>
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            style={{
              width: '100%',
              backgroundColor: '#2563eb',
              border: 'none',
              color: '#ffffff',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {isSimulating ? <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Zap size={16} />}
            {isSimulating ? 'Executing Attack Test...' : 'Run Resilience Simulation'}
          </button>

          {simulatedResult && (
            <div style={{ marginTop: '16px', backgroundColor: 'rgba(52, 211, 153, 0.15)', border: '1px solid rgba(52, 211, 153, 0.3)', padding: '14px', borderRadius: '8px', color: '#34d399', fontSize: '13px', fontWeight: 600 }}>
              {simulatedResult}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
