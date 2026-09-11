import React from 'react';
import { HealthStatus } from '../types';
import { RefreshCw, Server, Database, UserCheck, LogOut, LogIn } from 'lucide-react';
import { NavTab } from './Sidebar';

interface HeaderProps {
  activeTab: NavTab;
  health: HealthStatus | null;
  onRefresh: () => void;
  isRefreshing: boolean;
  userEmail: string | null;
  authLoading: boolean;
  authError: string | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, health, onRefresh, isRefreshing, userEmail, authLoading, authError, onOpenAuth, onLogout }) => {
  const titleMap: Record<NavTab, { title: string; subtitle: string }> = {
    'new-screening': {
      title: 'New Screening Intake',
      subtitle: 'Upload primary document, secondary visa/ID, and live photo for multimodal verification.'
    },
    'history': {
      title: 'Screening Audit History',
      subtitle: 'Review past screening logs, risk assessments, and evidence signals.'
    },
    'evidence': {
      title: 'Multimodal Evidence & Explanation Panel',
      subtitle: 'Inspect forensic correlation graph, consistency checks, and officer decision rationale.'
    },
    'fraud-lab': {
      title: 'Fraud Resilience Testing Lab',
      subtitle: 'Simulate adversarial document attacks to measure and harden system resilience.'
    },
    'system-status': {
      title: 'System Health & Data Adapter Inspector',
      subtitle: 'Monitor backend status, Firestore database mode, and inspect canonical data models.'
    }
  };

  const currentInfo = titleMap[activeTab];

  return (
    <header style={{
      backgroundColor: '#0f172a',
      borderBottom: '1px solid #1e293b',
      padding: '16px 28px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#f8fafc', letterSpacing: '-0.01em' }}>
          {currentInfo.title}
        </h1>
        <p style={{ fontSize: '12px', margin: '2px 0 0 0', color: '#94a3b8' }}>
          {currentInfo.subtitle}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <button
          onClick={userEmail ? onLogout : onOpenAuth}
          disabled={authLoading}
          style={{ backgroundColor: '#1e293b', border: '1px solid #334155', color: userEmail ? '#a7f3d0' : '#93c5fd', padding: '7px 10px', borderRadius: '6px', cursor: authLoading ? 'wait' : 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
          title={userEmail ? 'Sign out' : 'Sign in'}
        >
          {userEmail ? <LogOut size={13} /> : <LogIn size={13} />}
          {authLoading ? 'Checking account…' : userEmail || 'Sign in'}
        </button>
        {authError && <span role="alert" style={{ color: '#fca5a5', fontSize: '11px', maxWidth: '180px' }}>{authError}</span>}
        {/* Officer Status Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          backgroundColor: '#1e293b',
          padding: '6px 12px',
          borderRadius: '6px',
          border: '1px solid #334155',
          color: '#cbd5e1'
        }}>
          <UserCheck size={14} color="#60a5fa" />
          <span>Officer: <strong>SSB-DEMO-01</strong></span>
        </div>

        {/* Backend Status Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          backgroundColor: '#1e293b',
          padding: '6px 12px',
          borderRadius: '6px',
          border: '1px solid #334155'
        }}>
          <Server size={14} color={health ? '#34d399' : '#f87171'} />
          <span style={{ color: '#94a3b8' }}>API:</span>
          <strong style={{ color: health ? '#34d399' : '#f87171' }}>
            {health ? '200 OK' : 'Offline'}
          </strong>
        </div>

        {/* Database Status Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          backgroundColor: '#1e293b',
          padding: '6px 12px',
          borderRadius: '6px',
          border: '1px solid #334155'
        }}>
          <Database size={14} color={health?.firebase_connected ? '#34d399' : '#fbbf24'} />
          <span style={{ color: '#94a3b8' }}>DB Mode:</span>
          <strong style={{ color: health?.firebase_connected ? '#34d399' : '#fbbf24' }}>
            {health?.firebase_connected ? 'Firestore' : 'Local Fallback'}
          </strong>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{
            backgroundColor: '#2563eb',
            border: 'none',
            color: '#fff',
            padding: '7px 12px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 600,
            opacity: isRefreshing ? 0.7 : 1
          }}
        >
          <RefreshCw size={13} style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>
    </header>
  );
};
