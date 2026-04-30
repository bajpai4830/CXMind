import React, { useState, useEffect } from "react";
import { 
  createInteraction, 
  uploadInteractionsCsv,
  listInteractions, 
  getSummary,
  getSentimentTrend,
  getTopTopics,
  Interaction, 
  AnalyticsSummary,
  SentimentTrendPoint,
  TopicCount
} from "../api";
import { Send, Clock, BarChart3, TrendingUp } from "lucide-react";
import toast from "react-hot-toast";
import { DashboardSkeleton } from "../components/DashboardSkeleton";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend
} from "recharts";

export default function UserDashboard() {
  const [channel, setChannel] = useState("support_ticket");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvBusy, setCsvBusy] = useState(false);
  
  const [recent, setRecent] = useState<Interaction[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trend, setTrend] = useState<SentimentTrendPoint[]>([]);
  const [topics, setTopics] = useState<TopicCount[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async (options?: { keepCurrentData?: boolean; notifyOnPartialFailure?: boolean }) => {
    const keepCurrentData = options?.keepCurrentData ?? false;
    const notifyOnPartialFailure = options?.notifyOnPartialFailure ?? true;

    if (!keepCurrentData) {
      setLoading(true);
    }

    const results = await Promise.allSettled([
      listInteractions(10),
      getSummary(),
      getSentimentTrend(),
      getTopTopics(),
    ]);

    const [recentResult, summaryResult, trendResult, topicsResult] = results;
    const failedSections: string[] = [];

    if (recentResult.status === "fulfilled") {
      setRecent(recentResult.value);
    } else {
      failedSections.push("recent interactions");
    }

    if (summaryResult.status === "fulfilled") {
      setSummary(summaryResult.value);
    } else {
      failedSections.push("summary metrics");
    }

    if (trendResult.status === "fulfilled") {
      setTrend(trendResult.value);
    } else {
      failedSections.push("sentiment trend");
    }

    if (topicsResult.status === "fulfilled") {
      setTopics(topicsResult.value);
    } else {
      failedSections.push("top topics");
    }

    if (failedSections.length > 0 && notifyOnPartialFailure) {
      const message = failedSections.length === results.length
        ? "Failed to load dashboard data"
        : `Some dashboard sections could not be refreshed: ${failedSections.join(", ")}`;
      toast.error(message);
    }

    setLoading(false);
  };

  useEffect(() => {
    void fetchDashboardData();
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    try {
      const created = await createInteraction({ channel, text });
      toast.success("Feedback ingested successfully");
      setText("");
      setRecent((current) => [created, ...current.filter((item) => item.id !== created.id)].slice(0, 10));
      await fetchDashboardData({ keepCurrentData: true, notifyOnPartialFailure: false });
    } catch (err: any) {
      toast.error(err.message || "Failed to ingest");
    } finally {
      setBusy(false);
    }
  };

  const onCsvUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) {
      toast.error("Please select a CSV file first");
      return;
    }

    setCsvBusy(true);
    try {
      const result = await uploadInteractionsCsv(csvFile);
      toast.success(`CSV uploaded. Processed: ${result.processed}, Failed: ${result.failed}`);
      setCsvFile(null);
      await fetchDashboardData({ keepCurrentData: true, notifyOnPartialFailure: false });
    } catch (err: any) {
      toast.error(err.message || "CSV upload failed. Please verify file format and try again.");
    } finally {
      setCsvBusy(false);
    }
  };

  if (loading && !summary && recent.length === 0) return <DashboardSkeleton />;

  return (
    <div className="dashboardGrid">
      {/* Metrics Row */}
      {summary && (
        <div className="metricsRow span2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <div className="glassPanel" style={{ padding: '1.5rem', textAlign: 'center' }}>
            <h3 className="muted">Total Interactions</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{summary.total_interactions.toLocaleString()}</div>
          </div>
          <div className="glassPanel" style={{ padding: '1.5rem', textAlign: 'center' }}>
            <h3 className="muted">Avg Sentiment</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: summary.avg_sentiment_compound > 0 ? '#10b981' : summary.avg_sentiment_compound < 0 ? '#ef4444' : '#f59e0b' }}>
              {summary.avg_sentiment_compound.toFixed(2)}
            </div>
          </div>
          <div className="glassPanel" style={{ padding: '1.5rem', textAlign: 'center' }}>
            <h3 className="muted">Top Channel</h3>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
              {summary.by_channel.length > 0 ? summary.by_channel[0].channel : 'N/A'}
            </div>
          </div>
        </div>
      )}

      {/* Ingest Form */}
      <div className="glassPanel">
        <div className="panelHeader">
          <h2><Send size={18} style={{marginRight: '8px'}}/> Ingest Feedback</h2>
          <p className="muted">Submit customer interactions for AI analysis</p>
        </div>
        <form onSubmit={onSubmit} className="ingestForm">
          <div className="fieldRow">
            <label className="field">
              <span className="fieldLabel">Source Channel</span>
              <select value={channel} onChange={(e) => setChannel(e.target.value)}>
                <option value="support_ticket">Support Ticket</option>
                <option value="email">Email</option>
                <option value="app_review">App Review</option>
                <option value="social_media">Social Media</option>
              </select>
            </label>
          </div>
          <label className="field">
            <span className="fieldLabel">Customer Verbatim</span>
            <textarea
              required
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the customer's comment, email, or ticket description here..."
            />
          </label>
          <div className="formActions mt-2">
            <button type="submit" disabled={busy || !text.trim()} className="btn btnPrimary" style={{width: '100%'}}>
              {busy ? "Processing..." : "Analyze & Ingest"}
            </button>
          </div>
        </form>
      </div>

      {/* Bulk Upload Form */}
      <div className="glassPanel">
        <div className="panelHeader">
          <h2><Send size={18} style={{marginRight: '8px'}}/> Bulk Upload (CSV)</h2>
          <p className="muted">Required columns: channel, message (customer_id is optional)</p>
        </div>
        <form onSubmit={onCsvUpload} className="ingestForm">
          <label className="field">
            <span className="fieldLabel">CSV File</span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
            />
          </label>
          <div className="muted mono" style={{ fontSize: "0.8rem", whiteSpace: "pre-wrap", marginTop: "0.5rem" }}>
            {"Example:\ncustomer_id,channel,message\n1,email,Service was slow\n2,app,Great experience"}
          </div>
          <div className="formActions mt-2">
            <button type="submit" disabled={csvBusy || !csvFile} className="btn btnPrimary" style={{width: '100%'}}>
              {csvBusy ? "Uploading..." : "Upload CSV"}
            </button>
          </div>
        </form>
      </div>

      {/* Top Topics Chart */}
      <div className="glassPanel">
        <div className="panelHeader">
          <h2><BarChart3 size={18} style={{marginRight: '8px'}}/> Top Complaint Topics</h2>
        </div>
        <div style={{ height: 300 }}>
          {topics.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topics} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="topic" opacity={0.8} />
                <YAxis opacity={0.8} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}/>
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center muted">No topic data available</div>
          )}
        </div>
      </div>

      {/* Sentiment Trend */}
      <div className="glassPanel span2">
        <div className="panelHeader">
          <h2><TrendingUp size={18} style={{marginRight: '8px'}}/> Sentiment Trend Over Time</h2>
        </div>
        <div style={{ height: 300 }}>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="date" opacity={0.8} />
                <YAxis domain={[-1, 1]} opacity={0.8} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}/>
                <Legend />
                <Line type="monotone" dataKey="avg_sentiment" stroke="#10b981" activeDot={{ r: 8 }} strokeWidth={2} name="Avg Sentiment" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center muted">No trend data available</div>
          )}
        </div>
      </div>

      {/* Recent Submissions */}
      <div className="glassPanel span2">
        <div className="panelHeader">
          <div className="splitHeader">
            <h2><Clock size={18} style={{marginRight: '8px'}}/> Recent Interactions</h2>
          </div>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Channel</th>
                <th>Topic</th>
                <th>Sentiment</th>
                <th>Content</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id}>
                  <td className="muted mono">{new Date(r.occurred_at || r.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                  <td><span className="tag neutral">{r.channel}</span></td>
                  <td>{r.topic ? <span className="tag info">{r.topic}</span> : <span className="muted">-</span>}</td>
                  <td><span className={`tag tag-${r.sentiment_label}`}>{r.sentiment_label} ({(r.sentiment_compound).toFixed(2)})</span></td>
                  <td className="textTruncate" style={{maxWidth: "300px"}} title={r.text}>{r.text}</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr><td colSpan={5} className="muted textCenter py-4">No recent submissions found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
