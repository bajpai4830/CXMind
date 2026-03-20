import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Navigate, useLocation } from "react-router-dom";
import { login, register } from "../api";
import { ShieldAlert, User as UserIcon, Eye, EyeOff, Mail, Lock } from "lucide-react";
import toast from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";

export default function Login() {
  const { user, isLoading, refetchUser } = useAuth();
  const location = useLocation();
  const [isRegister, setIsRegister] = useState(false);
  const [isAdminTab, setIsAdminTab] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [adminSecret, setAdminSecret] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showAdminSecret, setShowAdminSecret] = useState(false);
  const [busy, setBusy] = useState(false);
  const [cardRotation, setCardRotation] = useState({ x: 0, y: 0 });
  const cardRef = useRef<HTMLDivElement>(null);

  if (isLoading) return <div className="loadingScreen">Loading...</div>;

  if (user) {
    const from = location.state?.from?.pathname || (user.role === "admin" ? "/admin" : "/dashboard");
    return <Navigate to={from} replace />;
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;

    const card = cardRef.current.getBoundingClientRect();
    const centerX = card.left + card.width / 2;
    const centerY = card.top + card.height / 2;
    const rotationX = (e.clientY - centerY) * 0.05;
    const rotationY = (centerX - e.clientX) * 0.05;

    setCardRotation({ x: rotationX, y: rotationY });
  };

  const handleMouseLeave = () => {
    setCardRotation({ x: 0, y: 0 });
  };


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (isRegister) {
        await register(email, password, isAdminTab ? adminSecret : undefined);
        toast.success("Registration successful");
      }
      await login(email, password, isAdminTab ? "admin" : "analyst");
      await refetchUser();
    } catch (err: any) {
      toast.error(err.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, type: "tween", ease: "easeOut" },
    },
  };

  return (
    <div className="loginPage">
      {/* Animated Background */}
      <motion.div className="loginBackground" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}>
        <motion.div className="tealGlow" animate={{ x: [0, 30, 0], y: [0, 20, 0] }} transition={{ duration: 12, repeat: Infinity, type: "tween", ease: "easeInOut" }} />
        <motion.div className="blueGlow" animate={{ x: [0, -30, 0], y: [0, -20, 0] }} transition={{ duration: 14, repeat: Infinity, type: "tween", ease: "easeInOut" }} />
        <motion.div className="purpleGlow" animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }} transition={{ duration: 10, repeat: Infinity, type: "tween", ease: "easeInOut" }} />

        {/* Animated Particles */}
        <div className="particleContainer">
          {Array.from({ length: 20 }).map((_, i) => (
            <motion.div
              key={i}
              className="particle"
              initial={{ x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight, opacity: 0 }}
              animate={{
                y: [Math.random() * window.innerHeight, Math.random() * window.innerHeight - 100],
                opacity: [0, 0.5, 0],
              }}
              transition={{
                duration: Math.random() * 8 + 8,
                repeat: Infinity,
                type: "tween",
                ease: "linear",
              }}
            />
          ))}
        </div>
      </motion.div>

      {/* Login Card Container */}
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
          style={{
            perspective: "1000px",
          }}
          animate={{
            rotateX: cardRotation.x,
            rotateY: cardRotation.y,
          }}
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
        >
          {/* Logo & Brand Section */}
          <motion.div className="brandSection" variants={itemVariants}>
            <motion.div
              className="brandGroup"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 3, repeat: Infinity, type: "tween", ease: "easeInOut" }}
            >
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

          {/* Role Toggle Tabs */}
          <motion.div className="tabsContainer" variants={itemVariants}>
            <div className="tabs">
              <motion.button
                type="button"
                className={`tab ${!isAdminTab ? "active" : ""}`}
                onClick={() => setIsAdminTab(false)}
                aria-selected={!isAdminTab}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
              >
                <motion.span whileHover={{ rotate: 10 }} className="tabIcon">
                  <UserIcon size={16} />
                </motion.span>
                Analyst
              </motion.button>
              <motion.button
                type="button"
                className={`tab ${isAdminTab ? "active" : ""}`}
                onClick={() => setIsAdminTab(true)}
                aria-selected={isAdminTab}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
              >
                <motion.span whileHover={{ rotate: 10 }} className="tabIcon">
                  <ShieldAlert size={16} />
                </motion.span>
                Admin
              </motion.button>
            </div>
          </motion.div>

          {/* Login/Register Form */}
          <motion.form onSubmit={handleSubmit} className="loginForm" variants={itemVariants}>
            {/* Email Field */}
            <motion.div className="fieldGroup" variants={itemVariants}>
              <label className="field">
                <span className="fieldLabel">Email Address</span>
                <div className="inputWrapper">
                  <Mail className="inputIcon" size={18} />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    disabled={busy}
                    className="inputField"
                  />
                </div>
              </label>
            </motion.div>

            {/* Password Field */}
            <motion.div className="fieldGroup" variants={itemVariants}>
              <label className="field">
                <span className="fieldLabel">Password</span>
                <div className="inputWrapper">
                  <Lock className="inputIcon" size={18} />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    disabled={busy}
                    className="inputField"
                  />
                  <motion.button
                    type="button"
                    className="eyeToggle"
                    onClick={(e) => {
                      e.preventDefault();
                      setShowPassword(!showPassword);
                    }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <AnimatePresence mode="wait">
                      {showPassword ? (
                        <motion.div key="eye-off" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                          <EyeOff size={18} />
                        </motion.div>
                      ) : (
                        <motion.div key="eye" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                          <Eye size={18} />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.button>
                </div>
              </label>
            </motion.div>

            {/* Admin Secret Field */}
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
                  <label className="field">
                    <span className="fieldLabel tealText">Admin Secret Key</span>
                    <div className="inputWrapper">
                      <Lock className="inputIcon" size={18} />
                      <input
                        type={showAdminSecret ? "text" : "password"}
                        required
                        value={adminSecret}
                        onChange={(e) => setAdminSecret(e.target.value)}
                        placeholder="Enter your admin secret key"
                        disabled={busy}
                        className="inputField"
                      />
                      <motion.button
                        type="button"
                        className="eyeToggle"
                        onClick={(e) => {
                          e.preventDefault();
                          setShowAdminSecret(!showAdminSecret);
                        }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        <AnimatePresence mode="wait">
                          {showAdminSecret ? (
                            <motion.div key="secret-eye-off" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                              <EyeOff size={18} />
                            </motion.div>
                          ) : (
                            <motion.div key="secret-eye" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                              <Eye size={18} />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.button>
                    </div>
                  </label>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit Button */}
            <motion.div variants={itemVariants} className="submitButtonContainer">
              <motion.button
                type="submit"
                disabled={busy}
                className="btn btnPrimary"
                whileHover={{ scale: busy ? 1 : 1.05 }}
                whileTap={{ scale: busy ? 1 : 0.98 }}
              >
                <motion.div
                  className="buttonContent"
                  animate={busy ? { width: "40px" } : { width: "auto" }}
                  transition={{ duration: 0.3 }}
                >
                  {busy ? (
                    <motion.div
                      className="spinner"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    />
                  ) : (
                    <>{isRegister ? "Create Account" : "Sign In"}</>
                  )}
                </motion.div>
              </motion.button>
            </motion.div>
          </motion.form>

          {/* Authentication Toggle */}
          <motion.div className="authToggle" variants={itemVariants}>
            <span className="muted">{isRegister ? "Already have an account?" : "Need access?"}</span>
            <motion.button
              type="button"
              className="btnText"
              onClick={() => setIsRegister(!isRegister)}
              disabled={busy}
              whileHover={{ x: 5 }}
              whileTap={{ scale: 0.95 }}
            >
              {isRegister ? "Sign In" : "Register Now"}
            </motion.button>
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}
