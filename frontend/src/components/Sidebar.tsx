import React from 'react';
import { ShieldCheck, PlusCircle, History, FileSearch, TestTube2, Server } from 'lucide-react';
import { HealthStatus } from '../types';

export type NavTab = 'new-screening' | 'history' | 'evidence' | 'fraud-lab' | 'system-status';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  health: HealthStatus | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, health }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'new-screening', label: 'New Screening', icon: <PlusCircle size={18} /> },
    { id: 'history', label: 'Screening History', icon: <History size={18} />, badge: '3 Demo' },
    { id: 'evidence', label: 'Evidence & Explanation', icon: <FileSearch size={18} /> },
    { id: 'fraud-lab', label: 'Fraud Resilience Lab', icon: <TestTube2 size={18} />, badge: 'Lab' },
    { id: 'system-status', label: 'System Status & Inspector', icon: <Server size={18} /> },
  ];

  return (
    <aside style={{
      width: '260px',
      backgroundColor: '#0b1120',
      borderRight: '1px solid #1e293b',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      height: '100vh',
      position: 'sticky',
      top: 0,
      flexShrink: 0
    }}>
      <div>
        {/* Header / Branding */}
        <div style={{ padding: '20px 18px', borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#1e3a8a', padding: '8px', borderRadius: '8px', display: 'flex' }}>
            <ShieldCheck size={24} color="#60a5fa" />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
              SIH 2026 IDENTITY
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 500 }}>
              MHA / SSB Police II Div
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: isActive ? '1px solid #2563eb' : '1px solid transparent',
                  backgroundColor: isActive ? 'rgba(37, 99, 235, 0.15)' : 'transparent',
                  color: isActive ? '#60a5fa' : '#94a3b8',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 500,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {item.icon}
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: isActive ? '#1e40af' : '#1e293b',
                    color: isActive ? '#93c5fd' : '#64748b'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Pill */}
      <div style={{ padding: '16px', borderTop: '1px solid #1e293b', backgroundColor: '#090d16' }}>
        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '6px' }}>SYSTEM INFRASTRUCTURE</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
          <span style={{ color: '#94a3b8' }}>API Status:</span>
          <strong style={{ color: health ? '#34d399' : '#f87171' }}>
            {health ? 'ONLINE' : 'OFFLINE'}
          </strong>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', marginTop: '4px' }}>
          <span style={{ color: '#94a3b8' }}>Database:</span>
          <strong style={{ color: health?.firebase_connected ? '#34d399' : '#fbbf24' }}>
            {health?.firebase_connected ? 'Firestore' : 'Local Fallback'}
          </strong>
        </div>
      </div>
    </aside>
  );
};
