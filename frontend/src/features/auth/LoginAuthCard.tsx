import React, { useState } from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { Eye, EyeOff, Lock, Mail, ShieldAlert, User as UserIcon } from "lucide-react";
import toast from "react-hot-toast";

import { login, register } from "../../api";
import { useLoginCardTilt } from "./useLoginCardTilt";

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, type: "tween", ease: "easeOut" },
  },
};

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
        <motion.button
          type="button"
          className="eyeToggle"
          onClick={(event) => {
            event.preventDefault();
            onToggle();
          }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <AnimatePresence mode="wait">
            {showValue ? (
              <motion.div key="hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <EyeOff size={18} />
              </motion.div>
            ) : (
              <motion.div key="visible" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Eye size={18} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </label>
  );
}

export function LoginAuthCard({ onAuthenticated }: LoginAuthCardProps) {
  const { cardRef, cardRotation, handleMouseMove, handleMouseLeave } = useLoginCardTilt();

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

      await login(email, password, isAdminTab ? "admin" : undefined);
      await onAuthenticated();
    } catch (error: any) {
      toast.error(error.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      className="loginPageContainer"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <motion.div
        ref={cardRef}
        className="loginBox glassPanel"
        style={{ perspective: "1000px" }}
        animate={{ rotateX: cardRotation.x, rotateY: cardRotation.y }}
        whileHover={{ scale: 1.02 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      >
        <motion.div className="brandSection" variants={itemVariants}>
          <motion.div className="brandGroup" animate={{ y: [0, -5, 0] }} transition={{ duration: 3, repeat: Infinity, type: "tween", ease: "easeInOut" }}>
            <motion.div
              className="brandMark"
              animate={{
                boxShadow: [
                  "0 0 20px rgba(45, 212, 191, 0.3)",
                  "0 0 40px rgba(45, 212, 191, 0.6)",
                  "0 0 20px rgba(45, 212, 191, 0.3)",
                ],
              }}
              transition={{ duration: 2, repeat: Infinity, type: "tween", ease: "easeInOut" }}
            />
            <motion.div
              className="brandName large shimmerText"
              initial={{ backgroundPosition: "0% 50%" }}
              animate={{ backgroundPosition: "100% 50%" }}
              transition={{ duration: 3, repeat: Infinity, type: "tween", ease: "easeInOut" }}
            >
              CXMind
            </motion.div>
          </motion.div>
          <motion.p className="muted textCenter mb-4" variants={itemVariants}>
            Experience Intelligence Platform
          </motion.p>
        </motion.div>

        <motion.div className="tabsContainer" variants={itemVariants}>
          <div className="tabs">
            {roleTabs.map((tab) => {
              const TabIcon = tab.icon;
              return (
                <motion.button
                  key={tab.label}
                  type="button"
                  className={`tab ${tab.isActive ? "active" : ""}`}
                  onClick={tab.onClick}
                  aria-selected={tab.isActive}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <motion.span whileHover={{ rotate: 10 }} className="tabIcon">
                    <TabIcon size={16} />
                  </motion.span>
                  {tab.label}
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        <motion.form onSubmit={handleSubmit} className="loginForm" variants={itemVariants}>
          <motion.div className="fieldGroup" variants={itemVariants}>
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
          </motion.div>

          <motion.div className="fieldGroup" variants={itemVariants}>
            <SecureInput
              label="Password"
              placeholder="Enter your password"
              showValue={showPassword}
              value={password}
              disabled={busy}
              onChange={setPassword}
              onToggle={() => setShowPassword((current) => !current)}
            />
          </motion.div>

          <AnimatePresence>
            {isAdminTab && isRegister && (
              <motion.div
                className="fieldGroup"
                variants={itemVariants}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <SecureInput
                  label="Admin Secret Key"
                  placeholder="Enter your admin secret key"
                  showValue={showAdminSecret}
                  value={adminSecret}
                  disabled={busy}
                  onChange={setAdminSecret}
                  onToggle={() => setShowAdminSecret((current) => !current)}
                />
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div variants={itemVariants} className="submitButtonContainer">
            <motion.button
              type="submit"
              disabled={busy}
              className="btn btnPrimary"
              whileHover={{ scale: busy ? 1 : 1.05 }}
              whileTap={{ scale: busy ? 1 : 0.98 }}
            >
              <motion.div className="buttonContent" animate={busy ? { width: "40px" } : { width: "auto" }} transition={{ duration: 0.3 }}>
                {busy ? (
                  <motion.div className="spinner" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} />
                ) : (
                  <>{isRegister ? "Create Account" : "Sign In"}</>
                )}
              </motion.div>
            </motion.button>
          </motion.div>
        </motion.form>

        <motion.div className="authToggle" variants={itemVariants}>
          <span className="muted">{isRegister ? "Already have an account?" : "Need access?"}</span>
          <motion.button
            type="button"
            className="btnText"
            onClick={() => setIsRegister((current) => !current)}
            disabled={busy}
            whileHover={{ x: 5 }}
            whileTap={{ scale: 0.95 }}
          >
            {isRegister ? "Sign In" : "Register Now"}
          </motion.button>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
