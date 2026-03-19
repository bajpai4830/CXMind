import React, { useEffect, useState } from "react";
import { getSummary, AnalyticsSummary } from "../api";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DashboardSkeleton } from "../components/DashboardSkeleton";
import toast from "react-hot-toast";

const LABEL_COLORS: Record<string, string> = {
  positive: "#2DD4BF",
  neutral: "#94A3B8",
  negative: "#F87171"
};

export default function AdminDashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSummary();
        setSummary(data);
      } catch (err) {
        toast.error("Failed to load analytics");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  if (loading || !summary) return <DashboardSkeleton />;

  return (
    <div className="dashboardGrid">
      {/* Top KPIs */}
      <div className="glassPanel metricCard">
        <div className="metricLabel">Total Interactions</div>
        <div className="metricValue tealText">{summary.total_interactions.toLocaleString()}</div>
      </div>
      <div className="glassPanel metricCard">
        <div className="metricLabel">Average Sentiment</div>
        <div className="metricValue">{(summary.avg_sentiment_compound).toFixed(3)}</div>
      </div>
      <div className="glassPanel metricCard">
        <div className="metricLabel">Top Channel</div>
        <div className="metricValue">{summary.by_channel[0]?.channel || "N/A"}</div>
      </div>

      {/* Charts */}
      <div className="glassPanel">
        <div className="panelHeader">
          <h2>Volume by Channel</h2>
        </div>
        <div className="chartWrapper" style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={summary.by_channel}>
              <XAxis dataKey="channel" stroke="#64748B" fontSize={12} />
              <YAxis stroke="#64748B" fontSize={12} />
              <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
              <Bar dataKey="count" fill="#2DD4BF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glassPanel">
        <div className="panelHeader">
          <h2>Sentiment Distribution</h2>
        </div>
        <div className="chartWrapper" style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={summary.by_label} dataKey="count" nameKey="label" cx="50%" cy="50%" innerRadius={60} outerRadius={90}>
                {summary.by_label.map((x) => (
                  <Cell key={x.label} fill={LABEL_COLORS[x.label] || "#64748B"} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
