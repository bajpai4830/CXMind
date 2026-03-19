import { useEffect, useMemo, useRef } from "react";

type ChartType = "line" | "bar" | "pie" | "doughnut";

export default function ChartCanvas(props: {
  type: ChartType;
  data: any;
  options?: any;
  height?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartRef = useRef<any>(null);

  const config = useMemo(() => {
    return {
      type: props.type,
      data: props.data,
      options: props.options ?? {}
    };
  }, [props.type, props.data, props.options]);

  useEffect(() => {
    const Chart = window.Chart;
    if (!Chart) return;
    if (!canvasRef.current) return;

    if (chartRef.current) {
      try {
        chartRef.current.destroy();
      } catch {
        // ignore
      }
      chartRef.current = null;
    }

    chartRef.current = new Chart(canvasRef.current, config);

    return () => {
      if (!chartRef.current) return;
      try {
        chartRef.current.destroy();
      } catch {
        // ignore
      }
      chartRef.current = null;
    };
  }, [config]);

  if (!window.Chart) {
    return (
      <div className="error">
        <div className="errorTitle">Chart.js not loaded</div>
        <div className="errorBody mono">Check your network access or bundle Chart.js in production.</div>
      </div>
    );
  }

  return <canvas ref={canvasRef} height={props.height ?? 260} />;
}

