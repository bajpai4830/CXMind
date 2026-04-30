import React, { useRef, useState } from "react";

type CardRotation = {
  x: number;
  y: number;
};

/** Tracks a subtle card tilt effect for the animated login panel. */
export function useLoginCardTilt() {
  const cardRef = useRef<HTMLDivElement>(null);
  const [cardRotation, setCardRotation] = useState<CardRotation>({ x: 0, y: 0 });

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) {
      return;
    }

    const bounds = cardRef.current.getBoundingClientRect();
    const centerX = bounds.left + bounds.width / 2;
    const centerY = bounds.top + bounds.height / 2;
    const rotationX = (event.clientY - centerY) * 0.05;
    const rotationY = (centerX - event.clientX) * 0.05;

    setCardRotation({ x: rotationX, y: rotationY });
  };

  const handleMouseLeave = () => {
    setCardRotation({ x: 0, y: 0 });
  };

  return { cardRef, cardRotation, handleMouseMove, handleMouseLeave };
}
