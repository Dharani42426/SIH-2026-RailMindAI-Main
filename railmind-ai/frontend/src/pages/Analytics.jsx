import React, { useState, useEffect } from 'react';
import { 
  LineChart as LineChartIcon, TrendingUp, Activity, CheckCircle2, 
  AlertTriangle, Clock, Zap, CheckSquare, ShieldAlert, BarChart2,
  BrainCircuit, Factory, ArrowRight, Gauge
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const COLORS = {
  primary: '#3B82F6',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  saffron: '#F97316',
  navy: '#0F172A',
  white: '#ffffff',
  purple: '#8B5CF6'
};

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [sectionsOverview, setSectionsOverview] = useState([]);
  const [beforeAfterData, setBeforeAfterData] = useState(null);
  const [selectedSectionId, setSelectedSectionId] = useState('');
  const [sections, setSections] = useState([]);

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedSectionId]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const dashboardReq = axios.get(`${BACKEND_URL}/api/analytics/dashboard`, {
        params: selectedSectionId ? { section_id: selectedSectionId } : {}
      });
      const sectionsReq = axios.get(`${BACKEND_URL}/api/analytics/sections/overview`);
      const initialSectionsRes = await axios.get(`${BACKEND_URL}/api/sections/`);
      
      setSections(initialSectionsRes.data);
      const targetSectionId = selectedSectionId || (initialSectionsRes.data.length > 0 ? initialSectionsRes.data[0].id : null);
      
      let beforeAfterReq = null;
      if (targetSectionId) {
        beforeAfterReq = axios.get(`${BACKEND_URL}/api/analytics/before-after`, { params: { section_id: targetSectionId } });
      }

      const [dashRes, overviewRes, baRes] = await Promise.all([
        dashboardReq, sectionsReq, beforeAfterReq ? beforeAfterReq : Promise.resolve({ data: null })
      ]);

      setDashboardData(dashRes.data);
      setSectionsOverview(overviewRes.data);
      if (baRes.data) setBeforeAfterData(baRes.data);
      
    } catch (err) {
      setError("Failed to stream analytics intelligence. Connection dropped.");
    } finally {
      setLoading(false);
    }
  };

  const severityChartData = dashboardData ? Object.entries(dashboardData.severity_breakdown || {}).map(([key, val]) => ({
    name: key, value: val
  })) : [];
  
  const PIE_COLORS = [COLORS.danger, COLORS.warning, COLORS.primary, COLORS.saffron];

  const beforeAfterChartData = beforeAfterData ? beforeAfterData.comparisons.map(c => ({
    name: c.metric,
    'Manual Operations': c.before_value,
    'RailMind AI Operations': c.after_value,
    unit: c.unit
  })) : [];

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px', minHeight: '100%' }}>
      
      {/* HEADER */}
      <div className="flex-between">
        <div>
          <h1 className="page-title" style={{ color: 'var(--color-navy)' }}>
            <BarChart2 size={32} color="var(--color-primary)" /> EXECUTIVE INTELLIGENCE
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, letterSpacing: '0.05em' }}>
            <Gauge size={16} color="var(--color-primary)" /> Network Performance & AI Optimization Impact
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', backgroundColor: 'var(--color-bg-white)', padding: '12px 24px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', textTransform: 'uppercase' }}>Scope:</span>
          <select className="input-rail" value={selectedSectionId} onChange={(e) => setSelectedSectionId(e.target.value)} style={{ minWidth: '200px', fontWeight: 700 }}>
            <option value="">ENTIRE NETWORK</option>
            {sections.map(sec => <option key={sec.id} value={sec.id}>{sec.section_code} CORRIDOR</option>)}
          </select>
        </div>
      </div>

      {error && (
        <div style={{ padding: '24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 700, borderRadius: 'var(--radius-md)' }}>
          <AlertTriangle size={24} /> {error}
        </div>
      )}

      {loading && !dashboardData && (
        <div className="flex-center" style={{ padding: '60px', color: 'var(--color-primary)' }}>
          <Activity className="animate-spin" size={48} />
        </div>
      )}

      {/* BEFORE VS AFTER HERO SECTION */}
      {!loading && !error && beforeAfterData && (
        <div className="card animate-slide-up" style={{ padding: '32px', borderTop: '4px solid #8B5CF6', backgroundColor: 'var(--color-bg-white)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
            <BrainCircuit size={32} color="#8B5CF6" />
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: '#6D28D9' }}>RAILMIND AI IMPACT ASSESSMENT</h2>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '40px' }}>
            {/* Split Screen Metric Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {beforeAfterData.comparisons.map((comp, idx) => (
                <div key={idx} className="hover-lift" style={{ padding: '20px', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: '4px', backgroundColor: comp.improvement_pct > 0 ? 'var(--color-success-dark)' : 'var(--color-warning-dark)' }}></div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--color-navy)', textTransform: 'uppercase', marginBottom: '16px', letterSpacing: '0.05em' }}>{comp.metric}</div>
                  
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 800 }}>Manual</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>{comp.before_value}</div>
                    </div>
                    <ArrowRight size={20} color="#8B5CF6" />
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: '#6D28D9', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 800 }}>RailMind</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#6D28D9' }}>{comp.after_value}</div>
                    </div>
                  </div>
                  
                  <div style={{ backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success-dark)', padding: '8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem', fontWeight: 800, border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                    <TrendingUp size={16} /> +{comp.improvement_pct}% YIELD
                  </div>
                </div>
              ))}
            </div>

            {/* Bar Chart */}
            <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '24px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
              <h3 className="section-heading" style={{ marginBottom: '24px', color: 'var(--color-navy)' }}>DIVERGENT METRIC COMPARISON</h3>
              <div style={{ height: '350px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={beforeAfterChartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="name" stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-main)', fontSize: 12, fontWeight: 700}} />
                    <YAxis stroke="var(--color-text-muted)" tick={{fill: 'var(--color-text-main)', fontSize: 12, fontWeight: 700}} fontFamily="var(--font-mono)" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--color-bg-white)', border: '1px solid var(--color-border)', borderRadius: '4px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}
                      itemStyle={{ color: 'var(--color-navy)' }}
                      cursor={{ fill: 'var(--color-bg-main)' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px', fontWeight: 700, fontSize: '0.875rem', color: 'var(--color-navy)' }} />
                    <Bar dataKey="Manual Operations" fill="var(--color-text-muted)" radius={[4, 4, 0, 0]} barSize={40} />
                    <Bar dataKey="RailMind AI Operations" fill="#8B5CF6" radius={[4, 4, 0, 0]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* EXECUTIVE KPI AREA */}
      {!loading && !error && dashboardData && (
        <div className="grid-cols-4 animate-slide-up">
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-primary)' }}>
            <div className="flex-between" style={{ marginBottom: '16px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Scheduled Operations</div>
              <CheckSquare size={24} color="var(--color-primary)" />
            </div>
            <div className="kpi-value">{dashboardData.tasks_scheduled}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', marginTop: 'auto', paddingTop: '16px', borderTop: '1px dashed var(--color-border)' }}>
              <span>PENDING: {dashboardData.tasks_pending}</span>
              <span>COMPLETED: {dashboardData.tasks_completed}</span>
            </div>
          </div>

          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-danger-dark)' }}>
            <div className="flex-between" style={{ marginBottom: '16px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-danger-dark)' }}>Critical / Overdue</div>
              <ShieldAlert size={24} color="var(--color-danger-dark)" />
            </div>
            <div className="kpi-value" style={{ color: 'var(--color-danger-dark)' }}>
              {dashboardData.severity_breakdown?.CRITICAL || 0} <span style={{ fontSize: '1.5rem', color: 'var(--color-text-muted)' }}>/ {dashboardData.tasks_overdue}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', marginTop: 'auto', paddingTop: '16px', borderTop: '1px dashed var(--color-border)' }}>
              <span>AVG CRITICALITY: {dashboardData.avg_criticality_score}</span>
            </div>
          </div>

          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-success-dark)' }}>
            <div className="flex-between" style={{ marginBottom: '16px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Block Utilization</div>
              <TrendingUp size={24} color="var(--color-success-dark)" />
            </div>
            <div className="kpi-value" style={{ color: 'var(--color-success-dark)' }}>{dashboardData.block_utilization_pct}%</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', marginTop: 'auto', paddingTop: '16px', borderTop: '1px dashed var(--color-border)' }}>
              <span>TOTAL HRS: {dashboardData.total_block_hours}</span>
              <span style={{ color: 'var(--color-success-dark)' }}>INTEGRATION: {dashboardData.integrated_block_pct}%</span>
            </div>
          </div>

          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-accent-saffron)' }}>
            <div className="flex-between" style={{ marginBottom: '16px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Network Health Index</div>
              <Zap size={24} color="var(--color-accent-saffron)" />
            </div>
            <div className="kpi-value">{dashboardData.avg_asset_health}%</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', marginTop: 'auto', paddingTop: '16px', borderTop: '1px dashed var(--color-border)' }}>
              <span>UPTIME: {dashboardData.asset_availability_pct}%</span>
              <span>CRITICAL ASSETS: {dashboardData.critical_assets}</span>
            </div>
          </div>
        </div>
      )}

      {/* LOWER ROW: CHARTS & TABLES */}
      {!loading && !error && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2.5fr', gap: '32px' }}>
          
          {/* SEVERITY DISTRIBUTION */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
            <div className="panel-header" style={{ color: 'var(--color-navy)' }}>
              <Activity color="var(--color-primary)" size={20} /> TASK LOAD DISTRIBUTION
            </div>
            <div style={{ flex: 1, minHeight: '300px', padding: '24px', backgroundColor: 'var(--color-bg-white)' }}>
              {severityChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {severityChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--color-bg-white)', border: '1px solid var(--color-border)', borderRadius: '4px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}
                    />
                    <Legend wrapperStyle={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--color-navy)' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex-center" style={{ height: '100%', color: 'var(--color-text-muted)', fontWeight: 700 }}>NO TASK DATA</div>
              )}
            </div>
          </div>

          {/* SECTION PERFORMANCE */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
            <div className="panel-header" style={{ color: 'var(--color-navy)' }}>
              <Gauge color="var(--color-primary)" size={20} /> CORRIDOR OPERATIONAL TELEMETRY
            </div>
            <div style={{ overflowX: 'auto', flex: 1, backgroundColor: 'var(--color-bg-white)' }}>
              <table className="rail-table">
                <thead>
                  <tr>
                    <th style={{ paddingLeft: '32px' }}>Corridor Identity</th>
                    <th>Tasks ( Pend / Crit / Over )</th>
                    <th>Active Assets</th>
                    <th>Asset Health</th>
                    <th style={{ paddingRight: '32px' }}>System Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sectionsOverview.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ padding: '60px', textAlign: 'center', color: 'var(--color-text-muted)', fontWeight: 700 }}>NO CORRIDOR DATA AVAILABLE</td>
                    </tr>
                  ) : (
                    sectionsOverview.map(sec => {
                      const hasHighRisk = sec.critical_tasks > 0 || sec.overdue_tasks > 0 || sec.avg_health < 80;
                      return (
                        <tr key={sec.id} className="hover-lift">
                          <td style={{ paddingLeft: '32px' }}>
                            <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', fontSize: '1.125rem', color: 'var(--color-navy)' }}>{sec.code}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>{sec.name}</div>
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                            <span style={{ color: 'var(--color-navy)' }}>{sec.pending_tasks}</span> / 
                            <span style={{ color: sec.critical_tasks > 0 ? 'var(--color-danger-dark)' : 'var(--color-text-muted)' }}> {sec.critical_tasks}</span> / 
                            <span style={{ color: sec.overdue_tasks > 0 ? 'var(--color-warning-dark)' : 'var(--color-text-muted)' }}> {sec.overdue_tasks}</span>
                          </td>
                          <td style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{sec.total_assets}</td>
                          <td style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: sec.avg_health < 80 ? 'var(--color-danger-dark)' : 'var(--color-success-dark)' }}>
                            {sec.avg_health}%
                          </td>
                          <td style={{ paddingRight: '32px' }}>
                            {hasHighRisk ? (
                              <span className="badge badge-danger" style={{ padding: '6px 12px', fontSize: '0.75rem', fontWeight: 800 }}>HIGH RISK</span>
                            ) : (
                              <span className="badge badge-success" style={{ padding: '6px 12px', fontSize: '0.75rem', fontWeight: 800 }}>OPTIMAL</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}

    </div>
  );
};

export default Analytics;
