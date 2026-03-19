import React, { useEffect, useState } from "react";
import { getSummary, AnalyticsSummary, listUsers, UserItem, updateUserRole, deactivateUser, listAuditLogs, AuditLogItem, getSystemJobs, retrainTopicModel } from "../api";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DashboardSkeleton } from "../components/DashboardSkeleton";
import toast from "react-hot-toast";
import { Play, Activity, ShieldAlert, Users, Trash2, ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";

const LABEL_COLORS: Record<string, string> = {
  positive: "#2DD4BF",
  neutral: "#94A3B8",
  negative: "#F87171"
};

export default function AdminDashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);

  const fetchUsers = async () => setUsers((await listUsers()).items);
  const fetchLogs = async () => setLogs(await listAuditLogs());
  const fetchJobs = async () => setJobs(await getSystemJobs());
  
  useEffect(() => {
    async function loadAll() {
      try {
        const [sumData] = await Promise.all([getSummary(), fetchUsers(), fetchLogs(), fetchJobs()]);
        setSummary(sumData);
      } catch (err) {
        toast.error("Failed to load admin data completely.");
      } finally {
        setLoading(false);
      }
    }
    void loadAll();
  }, []);

  const handleRoleToggle = async (user: UserItem) => {
    setActionBusy(true);
    try {
      const newRole = user.role === "admin" ? "analyst" : "admin";
      await updateUserRole(user.id, newRole);
      toast.success(`User role updated to ${newRole}`);
      await fetchUsers();
      await fetchLogs();
    } catch(e: any) {
      toast.error(e.message || "Failed to update role");
    } finally {
      setActionBusy(false);
    }
  };

  const handleDeactivate = async (userId: number) => {
    if (!window.confirm("Are you sure you want to deactivate this account?")) return;
    setActionBusy(true);
    try {
      await deactivateUser(userId);
      toast.success("User deactivated successfully");
      await fetchUsers();
      await fetchLogs();
    } catch(e: any) {
      toast.error(e.message || "Failed to deactivate");
    } finally {
      setActionBusy(false);
    }
  };

  const handleRetrain = async () => {
    setActionBusy(true);
    try {
      await retrainTopicModel();
      toast.success("Topic model retraining triggered safely.");
      await fetchJobs();
      await fetchLogs();
    } catch(e: any) {
      toast.error(e.message || "Model retrain blocked.");
    } finally {
      setActionBusy(false);
    }
  };

  if (loading || !summary) return <DashboardSkeleton />;

  const topicJob = jobs.find(j => j.job_name === "retrain_topic_model");

  return (
    <div className="dashboardGrid">
      {/* Top KPIs */}
      <div className="glassPanel metricCard">
        <div className="metricLabel">Platform Interactions</div>
        <div className="metricValue tealText">{summary.total_interactions.toLocaleString()}</div>
      </div>
      <div className="glassPanel metricCard">
        <div className="metricLabel">Registered Users</div>
        <div className="metricValue">{users.length}</div>
      </div>
      <div className="glassPanel metricCard">
        <div className="metricLabel">ML Topic Sync Status</div>
        <div className="metricValue" style={{fontSize: '1.2rem', display: 'flex', alignItems: 'center', height: '100%'}}>
          {topicJob?.status === "running" ? (
             <span className="tealText">Running Active Batch...</span>
          ) : (
             <span className="muted">Idle (Last: {topicJob?.last_run ? new Date(topicJob.last_run).toLocaleTimeString() : 'Never'})</span>
          )}
        </div>
      </div>

      {/* AI Automation Controls */}
      <div className="glassPanel span2" style={{ borderColor: 'rgba(45, 212, 191, 0.4)' }}>
        <div className="panelHeader splitHeader" style={{ paddingBottom: '16px' }}>
          <h2><Activity size={20} className="tealText" /> Embedded ML Operations</h2>
          <button 
            disabled={actionBusy || topicJob?.status === "running"} 
            onClick={handleRetrain} 
            className="btn btnPrimary"
          >
             <Play size={16} /> Force Sync Topic Modeling
          </button>
        </div>
      </div>

      {/* User Directory */}
      <div className="glassPanel span2">
        <div className="panelHeader splitHeader">
          <h2><Users size={18}/> User Directory</h2>
        </div>
        <div className="tableWrap" style={{ maxHeight: "300px" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Identifier</th>
                <th>Role</th>
                <th>State</th>
                <th style={{textAlign: "right"}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>
                    <strong>{u.email}</strong><br/>
                    <small className="muted mono">JOINED: {new Date(u.created_at).toLocaleDateString()}</small>
                  </td>
                  <td><span className={`tag tag-${u.role === 'admin' ? 'positive' : 'neutral'}`}>{u.role}</span></td>
                  <td>{u.is_active ? <span className="tealText">Active</span> : <span className="muted">Deactivated</span>}</td>
                  <td style={{textAlign: "right"}}>
                    <div style={{display: 'inline-flex', gap: '8px'}}>
                       <button disabled={actionBusy || !u.is_active} onClick={() => handleRoleToggle(u)} className="btn" title="Toggle role">
                         {u.role === "admin" ? <ArrowDownRight size={14}/> : <ArrowUpRight size={14}/>}
                       </button>
                       <button disabled={actionBusy || !u.is_active} onClick={() => handleDeactivate(u.id)} className="btn" style={{color: '#F87171'}} title="Deactivate">
                         <Trash2 size={14}/>
                       </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Logs and Analytics */}
      <div className="glassPanel">
        <div className="panelHeader"><h2><ShieldAlert size={18}/> Global Audit Stream</h2></div>
        <div className="scrollArea" style={{ height: "260px", padding: "16px 24px" }}>
          <div style={{display: "flex", flexDirection: "column", gap: "16px"}}>
            {logs.map(log => (
              <div key={log.id} style={{fontSize: "0.85rem", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "12px"}}>
                <div style={{display: "flex", justifyContent: "space-between", marginBottom: "4px"}}>
                  <strong className="tealText">{log.actor_email}</strong>
                  <span className="muted mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="muted">{log.action.toUpperCase()} <span className="mono" style={{float: "right"}}>{log.target}</span></div>
              </div>
            ))}
          </div>
        </div>
      </div>

       <div className="glassPanel">
        <div className="panelHeader"><h2>Sentiment Distribution</h2></div>
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
