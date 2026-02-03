import React from "react";

export default function KpiCard(props: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="kpi">
      <div className="kpiLabel">{props.label}</div>
      <div className="kpiValue">{props.value}</div>
      {props.hint ? <div className="kpiHint">{props.hint}</div> : null}
    </div>
  );
}

