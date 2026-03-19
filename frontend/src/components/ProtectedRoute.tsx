import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { DashboardSkeleton } from "./DashboardSkeleton";

export function ProtectedRoute({ children, requiredRole }: { children: React.ReactNode; requiredRole?: string }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== "admin" && user.role !== requiredRole) {
    // Admin covers everything, otherwise exact match required.
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
