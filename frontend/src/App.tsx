import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { createInteraction, getSummary, listInteractions, type AnalyticsSummary, type Interaction } from "./api";
import KpiCard from "./components/KpiCard";
import StatusPill from "./components/StatusPill";

const LABEL_COLORS: Record<string, string> = {
  positive: "#20c997",
  neutral: "#ffd43b",
  negative: "#ff6b6b"
};

function fmtScore(x: number) {
  return (Math.round(x * 1000) / 1000).toFixed(3);
}

export default function App() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recent, setRecent] = useState<Interaction[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [channel, setChannel] = useState("support_ticket");
  const [text, setText] = useState("");

  async function refresh() {
    setError(null);
    try {
      // If this passes, proxy + backend are up.
      await fetch("/health");
      setBackendOk(true);

      const [s, r] = await Promise.all([getSummary(), listInteractions(25)]);
      setSummary(s);
      setRecent(r);
    } catch (e) {
      setBackendOk(false);
      setSummary(null);
      setRecent([]);
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const avgTone = useMemo(() => {
    const v = summary?.avg_sentiment_compound ?? 0;
    if (v >= 0.1) return "Positive";
    if (v <= -0.1) return "Negative";
    return "Mixed";
  }, [summary]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createInteraction({ channel, text });
      setText("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <div className="brandMark" aria-hidden="true" />
          <div>
            <div className="brandName">CXMind</div>
            <div className="brandTag">Experience Intelligence (MVP)</div>
          </div>
        </div>
        <div className="right">
          {backendOk === null ? (
            <StatusPill ok={true} text="Checking backend..." />
          ) : backendOk ? (
            <StatusPill ok={true} text="Backend: OK" />
          ) : (
            <StatusPill ok={false} text="Backend: DOWN" />
          )}
          <button className="btn" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
      </header>

      <main className="grid">
        <section className="panel hero">
          <h1>Signals into clarity.</h1>
          <p className="muted">
            Ingest multi-channel feedback, score sentiment, and surface friction hotspots. This MVP wires a thin slice:
            <span className="mono"> ingest → score → store → summarize</span>.
          </p>
          {error ? (
            <div className="error">
              <div className="errorTitle">Backend not reachable</div>
              <div className="errorBody mono">{error}</div>
              <div className="errorHint muted">
                Start the API on <span className="mono">http://localhost:8000</span> (see <span className="mono">backend/README.md</span>).
              </div>
            </div>
          ) : null}

          <form className="ingest" onSubmit={onSubmit}>
            <div className="fieldRow">
              <label className="field">
                <span className="fieldLabel">Channel</span>
                <select value={channel} onChange={(e) => setChannel(e.target.value)}>
                  <option value="support_ticket">Support Ticket</option>
                  <option value="email">Email</option>
                  <option value="social">Social</option>
                  <option value="app_review">App Review</option>
                </select>
              </label>
              <button className="btn btnPrimary" type="submit" disabled={!text.trim() || backendOk !== true}>
                Ingest
              </button>
            </div>
            <label className="field">
              <span className="fieldLabel">Customer text</span>
              <textarea
                placeholder="Paste a message, ticket, or review..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={3}
              />
            </label>
          </form>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>Pulse</h2>
            <div className="muted">Last refresh: {new Date().toLocaleTimeString()}</div>
          </div>
          <div className="kpis">
            <KpiCard label="Interactions" value={summary ? summary.total_interactions : "—"} hint="Total stored in SQLite" />
            <KpiCard
              label="Avg sentiment"
              value={summary ? fmtScore(summary.avg_sentiment_compound) : "—"}
              hint={summary ? `Tone: ${avgTone}` : undefined}
            />
            <KpiCard
              label="Top channel"
              value={summary?.by_channel?.[0]?.channel ?? "—"}
              hint={summary?.by_channel?.[0] ? `${summary.by_channel[0].count} events` : undefined}
            />
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>Volume by channel</h2>
            <div className="muted">Count and average sentiment per channel</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={summary?.by_channel ?? []}>
                <XAxis dataKey="channel" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#74c0fc" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader">
            <h2>Sentiment mix</h2>
            <div className="muted">Positive / neutral / negative labels</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={summary?.by_label ?? []} dataKey="count" nameKey="label" outerRadius={90} innerRadius={45}>
                  {(summary?.by_label ?? []).map((x) => (
                    <Cell key={x.label} fill={LABEL_COLORS[x.label] ?? "#868e96"} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel span2">
          <div className="panelHeader">
            <h2>Recent interactions</h2>
            <div className="muted">Most recent 25 ingests</div>
          </div>
          <div className="tableWrap">
            <table className="table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Channel</th>
                  <th>Label</th>
                  <th className="num">Score</th>
                  <th>Text</th>
                </tr>
              </thead>
              <tbody>
                {recent.length ? (
                  recent.map((r) => (
                    <tr key={r.id}>
                      <td className="mono">{new Date(r.created_at).toLocaleString()}</td>
                      <td className="mono">{r.channel}</td>
                      <td>
                        <span className={`tag tag-${r.sentiment_label}`}>{r.sentiment_label}</span>
                      </td>
                      <td className="mono num">{fmtScore(r.sentiment_compound)}</td>
                      <td className="textCell">{r.text}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="muted">
                      {backendOk === false ? "Backend is down." : "No interactions yet. Ingest one above or run the seed script."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer className="footer muted">
        MVP: FastAPI + SQLite + VADER sentiment. Next: identity resolution, journey modeling, and predictive risk scoring.
      </footer>
    </div>
  );
}

