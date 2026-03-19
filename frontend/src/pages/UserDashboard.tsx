import React, { useState, useEffect } from "react";
import { createInteraction, listInteractions, Interaction } from "../api";
import { Send, Clock } from "lucide-react";
import toast from "react-hot-toast";
import { DashboardSkeleton } from "../components/DashboardSkeleton";

export default function UserDashboard() {
  const [channel, setChannel] = useState("support_ticket");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [recent, setRecent] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRecent = async () => {
    try {
      const data = await listInteractions(10);
      setRecent(data);
    } catch {
      toast.error("Failed to load interactions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchRecent();
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    try {
      await createInteraction({ channel, text });
      toast.success("Feedback ingested successfully");
      setText("");
      await fetchRecent();
    } catch (err: any) {
      toast.error(err.message || "Failed to ingest");
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <DashboardSkeleton />;

  return (
    <div className="dashboardGrid">
      <div className="glassPanel span2">
        <div className="panelHeader">
          <h2>Ingest Feedback</h2>
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
              rows={4}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the customer's comment, email, or ticket description here..."
            />
          </label>
          <div className="formActions">
            <button type="submit" disabled={busy || !text.trim()} className="btn btnPrimary">
              <Send size={16} /> Analyze & Ingest
            </button>
          </div>
        </form>
      </div>

      <div className="glassPanel span2">
        <div className="panelHeader">
          <div className="splitHeader">
            <h2><Clock size={18} /> My Recent Submissions</h2>
          </div>
        </div>
        <div className="tableWrap">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Channel</th>
                <th>Sentiment</th>
                <th>Content</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id}>
                  <td className="muted mono">{new Date(r.created_at).toLocaleTimeString()}</td>
                  <td><span className="tag neutral">{r.channel}</span></td>
                  <td><span className={`tag tag-${r.sentiment_label}`}>{r.sentiment_label} ({(r.sentiment_compound).toFixed(2)})</span></td>
                  <td className="textTruncate" style={{maxWidth: "300px"}}>{r.text}</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr><td colSpan={4} className="muted textCenter py-4">No recent submissions found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
