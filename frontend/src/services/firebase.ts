import { FirebaseApp, getApp, getApps, initializeApp } from 'firebase/app';
import { Auth, getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const requiredConfigKeys = Object.keys(firebaseConfig) as Array<keyof typeof firebaseConfig>;
export const firebaseConfigurationError = requiredConfigKeys.some((key) => !firebaseConfig[key])
  ? 'Firebase Authentication is not configured. Add the VITE_FIREBASE_* values to your local .env file.'
  : null;

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (!firebaseConfigurationError) {
  app = getApps().length ? getApp() : initializeApp(firebaseConfig);
  auth = getAuth(app);
}

export const firebaseAuth = auth;

export function getCurrentFirebaseUser() {
  return firebaseAuth?.currentUser ?? null;
}
