import React, { createContext, useContext, useEffect, useState } from "react";
import { getMe, logout as apiLogout } from "../api";

export type AuthUser = { id: number; email: string; role: string };

type AuthContextType = {
  user: AuthUser | null;
  isLoading: boolean;
  refetchUser: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refetchUser = async () => {
    setIsLoading(true);
    try {
      const data = await getMe();
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch {
      // ignore
    }
    setUser(null);
  };

  useEffect(() => {
    void refetchUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, refetchUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
