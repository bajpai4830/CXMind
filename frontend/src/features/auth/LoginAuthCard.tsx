import React, { useState } from "react";
import { Eye, EyeOff, Lock, Mail, ShieldAlert, User as UserIcon } from "lucide-react";
import toast from "react-hot-toast";

import { login, register } from "../../api";

type LoginAuthCardProps = {
  onAuthenticated: () => Promise<void>;
};

type SecureInputProps = {
  disabled?: boolean;
  label: string;
  placeholder: string;
  showValue: boolean;
  value: string;
  onChange: (value: string) => void;
  onToggle: () => void;
};

function SecureInput({
  disabled = false,
  label,
  placeholder,
  showValue,
  value,
  onChange,
  onToggle,
}: SecureInputProps) {
  return (
    <label className="field">
      <span className="fieldLabel">{label}</span>
      <div className="inputWrapper">
        <Lock className="inputIcon" size={18} />
        <input
          type={showValue ? "text" : "password"}
          required
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="inputField"
        />
        <button
          type="button"
          className="eyeToggle"
          onClick={(event) => {
            event.preventDefault();
            onToggle();
          }}
        >
          {showValue ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
    </label>
  );
}

export function LoginAuthCard({ onAuthenticated }: LoginAuthCardProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [isAdminTab, setIsAdminTab] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [adminSecret, setAdminSecret] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showAdminSecret, setShowAdminSecret] = useState(false);
  const [busy, setBusy] = useState(false);

  const roleTabs = [
    { icon: UserIcon, isActive: !isAdminTab, label: "Analyst", onClick: () => setIsAdminTab(false) },
    { icon: ShieldAlert, isActive: isAdminTab, label: "Admin", onClick: () => setIsAdminTab(true) },
  ];

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);

    try {
      if (isRegister) {
        await register(email, password, isAdminTab ? adminSecret : undefined);
        toast.success("Registration successful");
      }

      const res = await login(email, password, isAdminTab ? "admin" : undefined);
      if (typeof window !== "undefined" && res.access_token) {
        localStorage.setItem("cxmind_token", res.access_token);
      }
      await onAuthenticated();
    } catch (error: any) {
      toast.error(error.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="loginPageContainer">
      <div className="loginBox glassPanel">
        <div className="brandSection">
          <div className="brandGroup">
            <div className="brandMark" />
            <div className="brandName large">CXMind</div>
          </div>
          <p className="muted textCenter mb-4">
            Experience Intelligence Platform
          </p>
        </div>

        <div className="tabsContainer">
          <div className="tabs">
            {roleTabs.map((tab) => {
              const TabIcon = tab.icon;
              return (
                <button
                  key={tab.label}
                  type="button"
                  className={`tab ${tab.isActive ? "active" : ""}`}
                  onClick={tab.onClick}
                  aria-selected={tab.isActive}
                >
                  <span className="tabIcon">
                    <TabIcon size={16} />
                  </span>
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="loginForm">
          <div className="fieldGroup">
            <label className="field">
              <span className="fieldLabel">Email Address</span>
              <div className="inputWrapper">
                <Mail className="inputIcon" size={18} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@company.com"
                  disabled={busy}
                  className="inputField"
                />
              </div>
            </label>
          </div>

          <div className="fieldGroup">
            <SecureInput
              label="Password"
              placeholder="Enter your password"
              showValue={showPassword}
              value={password}
              disabled={busy}
              onChange={setPassword}
              onToggle={() => setShowPassword((current) => !current)}
            />
          </div>

          {isAdminTab && isRegister && (
            <div className="fieldGroup">
                <SecureInput
                  label="Admin Secret Key"
                  placeholder="Enter your admin secret key"
                  showValue={showAdminSecret}
                  value={adminSecret}
                  disabled={busy}
                  onChange={setAdminSecret}
                  onToggle={() => setShowAdminSecret((current) => !current)}
                />
            </div>
          )}

          <div className="submitButtonContainer">
            <button
              type="submit"
              disabled={busy}
              className="btn btnPrimary"
            >
              <div className="buttonContent">
                {busy ? (
                  <div className="spinner" />
                ) : (
                  <>{isRegister ? "Create Account" : "Sign In"}</>
                )}
              </div>
            </button>
          </div>
        </form>

        <div className="authToggle">
          <span className="muted">{isRegister ? "Already have an account?" : "Need access?"}</span>
          <button
            type="button"
            className="btnText"
            onClick={() => setIsRegister((current) => !current)}
            disabled={busy}
          >
            {isRegister ? "Sign In" : "Register Now"}
          </button>
        </div>
      </div>
    </div>
  );
}
