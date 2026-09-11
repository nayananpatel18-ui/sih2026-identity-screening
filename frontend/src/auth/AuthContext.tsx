import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { User, createUserWithEmailAndPassword, onAuthStateChanged, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { firebaseAuth, firebaseConfigurationError } from '../services/firebase';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  configurationError: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function requireAuth() {
  if (!firebaseAuth) throw new Error(firebaseConfigurationError ?? 'Firebase Authentication is unavailable.');
  return firebaseAuth;
}

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(firebaseAuth));

  useEffect(() => {
    if (!firebaseAuth) {
      setLoading(false);
      return;
    }
    return onAuthStateChanged(firebaseAuth, (nextUser) => {
      setUser(nextUser);
      setLoading(false);
    });
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    configurationError: firebaseConfigurationError,
    login: async (email, password) => { await signInWithEmailAndPassword(requireAuth(), email, password); },
    register: async (email, password) => { await createUserWithEmailAndPassword(requireAuth(), email, password); },
    logout: async () => { await signOut(requireAuth()); },
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}
