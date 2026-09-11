import React, { useState } from 'react';
import { AlertCircle, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

interface AuthPanelProps { onCancel: () => void; }

const authErrorMessage = (error: unknown): string => {
  const code = (error as { code?: string })?.code;
  if (code === 'auth/email-already-in-use') return 'An account already exists for this email address.';
  if (code === 'auth/invalid-credential' || code === 'auth/wrong-password' || code === 'auth/user-not-found') return 'Invalid email address or password.';
  if (code === 'auth/weak-password') return 'Choose a password with at least six characters.';
  if (code === 'auth/invalid-email') return 'Enter a valid email address.';
  return (error as Error)?.message || 'Authentication could not be completed.';
};

export const AuthPanel: React.FC<AuthPanelProps> = ({ onCancel }) => {
  const { login, register, configurationError } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === 'login') await login(email, password);
      else await register(email, password);
    } catch (authError) {
      setError(authErrorMessage(authError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ maxWidth: '420px', margin: '48px auto', backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px' }}>
      <h2 style={{ margin: 0, fontSize: '20px' }}>{mode === 'login' ? 'Sign in' : 'Create account'}</h2>
      <p style={{ color: '#94a3b8', fontSize: '13px', lineHeight: 1.5 }}>
        Sign in to upload a document or run a protected screening request.
      </p>
      {configurationError ? (
        <div style={{ color: '#fbbf24', backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.35)', borderRadius: '8px', padding: '12px', fontSize: '12px' }}>{configurationError}</div>
      ) : (
        <form onSubmit={submit} style={{ display: 'grid', gap: '12px' }}>
          <label style={{ fontSize: '12px', color: '#cbd5e1' }}>Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: '5px', padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#1e293b', color: '#f8fafc' }} /></label>
          <label style={{ fontSize: '12px', color: '#cbd5e1' }}>Password<input required minLength={6} type="password" value={password} onChange={(event) => setPassword(event.target.value)} style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: '5px', padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#1e293b', color: '#f8fafc' }} /></label>
          {error && <div style={{ color: '#fca5a5', fontSize: '12px', display: 'flex', gap: '6px' }}><AlertCircle size={15} />{error}</div>}
          <button disabled={loading} type="submit" style={{ padding: '10px', border: 0, borderRadius: '6px', background: '#2563eb', color: '#fff', fontWeight: 700, cursor: loading ? 'wait' : 'pointer' }}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      )}
      <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
        {!configurationError && <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }} style={{ border: 0, background: 'transparent', color: '#60a5fa', cursor: 'pointer' }}>{mode === 'login' ? <><UserPlus size={14} /> Create account</> : <><LogIn size={14} /> Use existing account</>}</button>}
        <button onClick={onCancel} style={{ border: 0, background: 'transparent', color: '#94a3b8', cursor: 'pointer' }}>Back to dashboard</button>
      </div>
    </section>
  );
};
