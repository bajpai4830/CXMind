import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Navigate, useLocation } from "react-router-dom";
import { login, register } from "../api";
import { ShieldAlert, User as UserIcon } from "lucide-react";
import toast from "react-hot-toast";

export default function Login() {
  const { user, isLoading, refetchUser } = useAuth();
  const location = useLocation();
  const [isRegister, setIsRegister] = useState(false);
  const [isAdminTab, setIsAdminTab] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [adminSecret, setAdminSecret] = useState("");
  const [busy, setBusy] = useState(false);

  if (isLoading) return <div className="loadingScreen">Loading...</div>;

  if (user) {
    const from = location.state?.from?.pathname || (user.role === "admin" ? "/admin" : "/dashboard");
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (isRegister) {
        await register(email, password, isAdminTab ? adminSecret : undefined);
        toast.success("Registration successful");
      }
      await login(email, password);
      // Let the subsequent refetch log the user in context
      await refetchUser();
    } catch (err: any) {
      toast.error(err.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="loginPage">
      <div className="loginBackground">
        <div className="tealGlow"></div>
        <div className="blueGlow"></div>
      </div>
      
      <div className="loginBox glassPanel">
        <div className="brandGroup centered">
          <div className="brandMark" />
          <div className="brandName large">CXMind</div>
        </div>
        <p className="muted textCenter mb-4">Experience Intelligence Platform</p>

        <div className="tabs">
          <button type="button" className={`tab ${!isAdminTab ? "active" : ""}`} onClick={() => setIsAdminTab(false)}>
            <UserIcon size={16} /> Analyst
          </button>
          <button type="button" className={`tab ${isAdminTab ? "active" : ""}`} onClick={() => setIsAdminTab(true)}>
            <ShieldAlert size={16} /> Admin
          </button>
        </div>

        <form onSubmit={handleSubmit} className="loginForm">
          <label className="field">
            <span className="fieldLabel">Work Email</span>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com" />
          </label>
          <label className="field">
            <span className="fieldLabel">Password</span>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </label>
          
          {isAdminTab && isRegister && (
            <label className="field">
              <span className="fieldLabel tealText">Admin Secret Key</span>
              <input type="password" required value={adminSecret} onChange={(e) => setAdminSecret(e.target.value)} placeholder="Required for admin role" />
            </label>
          )}

          <button type="submit" disabled={busy} className="btn btnPrimary mt-2">
            {isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>

        <div className="authToggle">
          <span className="muted">{isRegister ? "Already have an account?" : "Need access?"}</span>
          <button type="button" className="btnText" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? "Sign In" : "Register Now"}
          </button>
        </div>
      </div>
    </div>
  );
}
