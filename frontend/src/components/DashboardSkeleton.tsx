import React from "react";

export function DashboardSkeleton() {
  return (
    <div className="skeletonContainer">
      <div className="skeletonHeader glassPanel animatePulse"></div>
      <div className="skeletonGrid">
        <div className="skeletonCard glassPanel animatePulse"></div>
        <div className="skeletonCard glassPanel animatePulse"></div>
        <div className="skeletonCard glassPanel animatePulse"></div>
        <div className="skeletonPanel glassPanel span2 animatePulse"></div>
      </div>
    </div>
  );
}
