import React from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { LoginAuthCard } from "../features/auth/LoginAuthCard";
import { LoginBackground } from "../features/auth/LoginBackground";

export default function Login() {
  const { user, isLoading, refetchUser } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="loadingScreen">Loading...</div>;
  }

  if (user) {
    const from = location.state?.from?.pathname || (user.role === "admin" ? "/admin" : "/dashboard");
    return <Navigate to={from} replace />;
  }

  return (
    <div className="loginPage">
      <LoginBackground />
      <LoginAuthCard onAuthenticated={refetchUser} />
    </div>
  );
}
