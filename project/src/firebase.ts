import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from 'firebase/auth';

// Prefer env vars; fall back to provided config
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyALNHvQEBqX-4EGpOOUbClJATi0unwrLro',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'argo-bce2e.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'argo-bce2e',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'argo-bce2e.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '403771110635',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:403771110635:web:a1960463da8d375b383aae',
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || 'G-BRFTNL2FLF',
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();

export default app;


