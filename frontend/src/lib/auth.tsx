"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { User } from "firebase/auth";
import { setAuthToken } from "./api";

interface AuthState {
  user: User | null;
  loading: boolean;
  /** true when NEXT_PUBLIC_FIREBASE_CONFIG is not set yet */
  firebaseMissing: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  firebaseMissing: true,
  signInWithGoogle: async () => {},
  signOut: async () => {},
});

function hasFirebaseConfig(): boolean {
  try {
    const cfg = JSON.parse(process.env.NEXT_PUBLIC_FIREBASE_CONFIG ?? "{}");
    return Boolean(cfg.apiKey);
  } catch {
    return false;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const firebaseMissing = !hasFirebaseConfig();

  useEffect(() => {
    if (firebaseMissing) {
      setLoading(false);
      return;
    }
    let unsub = () => {};
    (async () => {
      const { auth } = await import("./firebase");
      const { onIdTokenChanged } = await import("firebase/auth");
      unsub = onIdTokenChanged(auth, async (u) => {
        setUser(u);
        setAuthToken(u ? await u.getIdToken() : null);
        setLoading(false);
      });
    })();
    return () => unsub();
  }, [firebaseMissing]);

  const signInWithGoogle = useCallback(async () => {
    const { auth, googleProvider } = await import("./firebase");
    const { signInWithPopup } = await import("firebase/auth");
    await signInWithPopup(auth, googleProvider);
  }, []);

  const signOut = useCallback(async () => {
    const { auth } = await import("./firebase");
    await auth.signOut();
    setAuthToken(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, firebaseMissing, signInWithGoogle, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
