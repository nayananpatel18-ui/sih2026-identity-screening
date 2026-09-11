import React, { useEffect, useState } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { Header } from './components/Header';
import { NewScreeningPage } from './pages/NewScreeningPage';
import { ScreeningHistoryPage } from './pages/ScreeningHistoryPage';
import { EvidenceExplanationPage } from './pages/EvidenceExplanationPage';
import { FraudLabPage } from './pages/FraudLabPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { AuthPanel } from './components/AuthPanel';
import { useAuth } from './auth/AuthContext';
import { api } from './services/api';
import { HealthStatus, CanonicalDocumentSample, MultimodalScreeningResult } from './types';

export const App: React.FC = () => {
  const { user, loading: authLoading, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>('new-screening');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [showAuth, setShowAuth] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState<boolean>(false);

  // Data inspector state
  const [sampleIds, setSampleIds] = useState<string[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('CASE_001_GENUINE');
  const [sampleData, setSampleData] = useState<CanonicalDocumentSample | null>(null);
  const [loadingSample, setLoadingSample] = useState<boolean>(false);

  // The backend pipeline is the sole source of officer-facing screening results.
  const [activeScreeningResult, setActiveScreeningResult] = useState<MultimodalScreeningResult | null>(null);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    setIsRefreshing(true);
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } catch (err) {
      console.error('Failed to fetch backend health:', err);
      setHealth(null);
    } finally {
      setLoadingHealth(false);
      setIsRefreshing(false);
    }
  };

  const fetchSamplesList = async () => {
    try {
      const list = await api.listSamples('synthetic');
      setSampleIds(list);
    } catch (err) {
      console.error('Failed to fetch samples list:', err);
    }
  };

  const fetchSampleDetails = async (id: string): Promise<CanonicalDocumentSample | null> => {
    setLoadingSample(true);
    try {
      const data = await api.getSample(id, 'synthetic');
      setSampleData(data);
      return data;
    } catch (err) {
      console.error(`Failed to fetch sample details for ${id}:`, err);
      return null;
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

  useEffect(() => {
    if (user) setShowAuth(false);
  }, [user]);

  const handleStartScreening = async (sampleId: string) => {
    const result = await api.runScreening(sampleId, 'synthetic');
    setActiveScreeningResult(result);
    setActiveTab('evidence');
  };

  const handleSelectHistoryScreening = async (sampleId: string) => {
    if (!user) {
      setShowAuth(true);
      return;
    }
    await handleStartScreening(sampleId);
  };

  const handleLogout = async () => {
    setAuthError(null);
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      setAuthError('Unable to sign out. Please try again.');
    } finally {
      setLoggingOut(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#090d16', color: '#f1f5f9' }}>
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} health={health} />

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header */}
        <Header
          activeTab={activeTab}
          health={health}
          onRefresh={fetchHealth}
          isRefreshing={isRefreshing}
          userEmail={user?.email ?? null}
          authLoading={authLoading || loggingOut}
          authError={authError}
          onOpenAuth={() => setShowAuth(true)}
          onLogout={() => { void handleLogout(); }}
        />

        {/* Dynamic Page Container */}
        <main style={{ flex: 1, padding: '24px 28px', maxWidth: '1600px', width: '100%', boxSizing: 'border-box' }}>
          {showAuth ? (
            <AuthPanel onCancel={() => setShowAuth(false)} />
          ) : activeTab === 'new-screening' && (
            <NewScreeningPage
              onLoadPreset={fetchSampleDetails}
              onStartScreening={handleStartScreening}
              isAuthenticated={Boolean(user)}
              onRequireAuthentication={() => setShowAuth(true)}
            />
          )}

          {activeTab === 'history' && (
            <ScreeningHistoryPage onSelectScreening={handleSelectHistoryScreening} />
          )}

          {activeTab === 'evidence' && (
            <EvidenceExplanationPage result={activeScreeningResult} />
          )}

          {activeTab === 'fraud-lab' && (
            <FraudLabPage />
          )}

          {activeTab === 'system-status' && (
            <SystemStatusPage
              health={health}
              loadingHealth={loadingHealth}
              sampleIds={sampleIds}
              selectedSampleId={selectedSampleId}
              onSelectSampleId={setSelectedSampleId}
              sampleData={sampleData}
              loadingSample={loadingSample}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
