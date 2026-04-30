import React, { useState } from "react";
import { motion } from "framer-motion";

type ParticleSpec = {
  duration: number;
  startX: number;
  startY: number;
  targetY: number;
};

function createParticleSpecs(): ParticleSpec[] {
  const viewportWidth = typeof window === "undefined" ? 1440 : window.innerWidth;
  const viewportHeight = typeof window === "undefined" ? 900 : window.innerHeight;

  return Array.from({ length: 20 }, () => ({
    duration: Math.random() * 8 + 8,
    startX: Math.random() * viewportWidth,
    startY: Math.random() * viewportHeight,
    targetY: Math.random() * viewportHeight - 100,
  }));
}

export function LoginBackground() {
  const [particles] = useState(createParticleSpecs);

  return (
    <motion.div className="loginBackground" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}>
      <motion.div className="tealGlow" animate={{ x: [0, 30, 0], y: [0, 20, 0] }} transition={{ duration: 12, repeat: Infinity, type: "tween", ease: "easeInOut" }} />
      <motion.div className="blueGlow" animate={{ x: [0, -30, 0], y: [0, -20, 0] }} transition={{ duration: 14, repeat: Infinity, type: "tween", ease: "easeInOut" }} />
      <motion.div className="purpleGlow" animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }} transition={{ duration: 10, repeat: Infinity, type: "tween", ease: "easeInOut" }} />

      <div className="particleContainer">
        {particles.map((particle, index) => (
          <motion.div
            key={index}
            className="particle"
            initial={{ x: particle.startX, y: particle.startY, opacity: 0 }}
            animate={{ y: [particle.startY, particle.targetY], opacity: [0, 0.5, 0] }}
            transition={{ duration: particle.duration, repeat: Infinity, type: "tween", ease: "linear" }}
          />
        ))}
      </div>
    </motion.div>
  );
}
