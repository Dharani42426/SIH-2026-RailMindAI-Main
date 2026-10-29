import React, { useState, useEffect } from 'react';
import { 
  Activity, Map, AlertTriangle, ShieldAlert, CheckCircle2, 
  TrendingDown, TrendingUp, Info, X, Zap, RefreshCw,
  Cpu, Radio, Hammer, ShieldCheck
} from 'lucide-react';
import axios from 'axios';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, ReferenceLine 
} from 'recharts';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Assets = () => {
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Data states
  const [assetsData, setAssetsData] = useState(null);
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [riskSummary, setRiskSummary] = useState(null);
  
  // Filters
  const [filterRisk, setFilterRisk] = useState('');
  const [filterType, setFilterType] = useState('');
  
  // Detail state
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [activeTab, setActiveTab] = useState('GRID'); // GRID or ANOMALIES

  // Initial load: Fetch sections
  useEffect(() => {
    const fetchSections = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/sections/`);
        setSections(res.data);
        if (res.data.length > 0) {
          setSelectedSection(res.data[0].id.toString());
        }
      } catch (err) {
        setError("RailMind Backend Offline or Unreachable");
      }
    };
    fetchSections();
  }, []);

  // Fetch asset and prediction data when section changes
  useEffect(() => {
    if (!selectedSection) return;
    
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setSelectedAsset(null);
      
      try {
        const sid = parseInt(selectedSection);
        
        // Parallel fetch for predictions, risk summary, and anomalies
        const [predRes, sumRes, anomRes] = await Promise.allSettled([
          axios.get(`${BACKEND_URL}/api/predictions/section/${sid}?update_tasks=false`),
          axios.get(`${BACKEND_URL}/api/predictions/section/${sid}/risk-summary`),
          axios.get(`${BACKEND_URL}/api/predictions/section/${sid}/anomalies`)
        ]);

        if (predRes.status === 'fulfilled') setAssetsData(predRes.value.data);
        else setAssetsData(null);

        if (sumRes.status === 'fulfilled') setRiskSummary(sumRes.value.data);
        else setRiskSummary(null);

        if (anomRes.status === 'fulfilled') setAnomaliesData(anomRes.value.data);
        else setAnomaliesData({ total_anomalies: 0, anomalies: [] });

      } catch (err) {
        setError("Failed to fetch asset data");
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [selectedSection]);

  // Derived filtered data
  const filteredAssets = assetsData?.predictions?.filter(asset => {
    if (filterRisk && asset.risk_level !== filterRisk) return false;
    if (filterType && asset.asset_type !== filterType) return false;
    return true;
  }) || [];

  const uniqueAssetTypes = assetsData 
    ? [...new Set(assetsData.predictions.map(a => a.asset_type))] 
    : [];

  // Helper for colors
  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL': return 'var(--color-danger-dark)';
      case 'HIGH': return 'var(--color-warning-dark)';
      case 'MEDIUM': return 'var(--color-primary)';
      case 'LOW': return 'var(--color-success-dark)';
      default: return 'var(--color-text-muted)';
    }
  };

  const getAssetIcon = (type) => {
    switch (type) {
      case 'TRACK': return <Map size={20} />;
      case 'SIGNAL': return <Radio size={20} />;
      case 'OHE': return <Zap size={20} />;
      default: return <Cpu size={20} />;
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', minHeight: '100%', position: 'relative' }}>
      
      {/* HEADER & CONTROLS */}
      <div className="flex-between">
        <div>
          <h1 className="page-title">
            <Activity size={32} color="var(--color-primary)" /> INFRASTRUCTURE TELEMETRY
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, letterSpacing: '0.05em' }}>
            <Cpu size={16} /> LSTM Predictive Maintenance & Anomaly Detection
          </p>
        </div>
      </div>

      <div className="card" style={{ padding: '20px 24px', display: 'flex', gap: '32px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontWeight: 800, letterSpacing: '0.05em' }}>
            <Map size={20} color="var(--color-primary)" /> TARGET CORRIDOR
          </div>
          <select className="input-rail" value={selectedSection} onChange={(e) => setSelectedSection(e.target.value)} style={{ width: '300px', fontWeight: 700 }}>
            {sections.map(sec => (
              <option key={sec.id} value={sec.id}>{sec.section_code} — {sec.section_name}</option>
            ))}
          </select>
        </div>

        {loading && (
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-primary)', fontWeight: 700, fontSize: '0.875rem' }}>
            <RefreshCw className="animate-spin" size={18} /> SYNCING TELEMETRY...
          </div>
        )}
      </div>

      {error && (
        <div style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 700, borderRadius: 'var(--radius-md)' }}>
          <AlertTriangle size={24} /> {error}
        </div>
      )}

      {/* KPI OVERVIEW */}
      {!error && riskSummary && (
        <div className="grid-cols-4 animate-slide-up">
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-primary)' }}>
            <div className="flex-between" style={{ marginBottom: '12px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Monitored Assets</div>
              <Activity size={24} color="var(--color-primary)" />
            </div>
            <div className="kpi-value">{riskSummary.total_assets}</div>
          </div>
          
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-danger-dark)', backgroundColor: riskSummary.assets_needing_attention > 0 ? 'var(--color-danger-bg)' : 'var(--color-bg-white)' }}>
            <div className="flex-between" style={{ marginBottom: '12px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-danger-dark)' }}>Critical / High Risk</div>
              <ShieldAlert size={24} color="var(--color-danger)" />
            </div>
            <div className="kpi-value" style={{ color: 'var(--color-danger-dark)' }}>{riskSummary.assets_needing_attention}</div>
          </div>

          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-success-dark)' }}>
            <div className="flex-between" style={{ marginBottom: '12px' }}>
              <div className="section-heading" style={{ margin: 0, color: 'var(--color-success-dark)' }}>Network Health Index</div>
              <TrendingUp size={24} color="var(--color-success-dark)" />
            </div>
            <div className="kpi-value" style={{ color: riskSummary.avg_health > 70 ? 'var(--color-success-dark)' : 'var(--color-warning-dark)' }}>
              {riskSummary.avg_health}%
            </div>
          </div>

          <div className="card hover-lift" style={{ borderLeft: anomaliesData?.total_anomalies > 0 ? '4px solid var(--color-warning-dark)' : '4px solid var(--color-border-dark)' }}>
            <div className="flex-between" style={{ marginBottom: '12px' }}>
              <div className="section-heading" style={{ margin: 0, color: anomaliesData?.total_anomalies > 0 ? 'var(--color-warning-dark)' : 'var(--color-text-muted)' }}>Detected Anomalies</div>
              <Zap size={24} color={anomaliesData?.total_anomalies > 0 ? 'var(--color-warning-dark)' : 'var(--color-text-muted)'} />
            </div>
            <div className="kpi-value" style={{ color: anomaliesData?.total_anomalies > 0 ? 'var(--color-warning-dark)' : 'var(--color-text-muted)' }}>
              {anomaliesData?.total_anomalies || 0}
            </div>
          </div>
        </div>
      )}

      {!error && assetsData && (
        <div className="card animate-slide-up" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          
          {/* TAB NAV */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-subtle)' }}>
            <button 
              style={{ 
                padding: '20px 32px', 
                background: 'none', 
                border: 'none', 
                borderBottom: activeTab === 'GRID' ? '4px solid var(--color-primary)' : '4px solid transparent',
                color: activeTab === 'GRID' ? 'var(--color-navy)' : 'var(--color-text-muted)',
                fontWeight: 800,
                fontSize: '1rem',
                letterSpacing: '0.05em',
                cursor: 'pointer',
                transition: 'all 0.2s',
                textTransform: 'uppercase'
              }}
              onClick={() => setActiveTab('GRID')}
            >
              Asset Telemetry Grid
            </button>
            <button 
              style={{ 
                padding: '20px 32px', 
                background: 'none', 
                border: 'none', 
                borderBottom: activeTab === 'ANOMALIES' ? '4px solid var(--color-warning-dark)' : '4px solid transparent',
                color: activeTab === 'ANOMALIES' ? 'var(--color-warning-dark)' : 'var(--color-text-muted)',
                fontWeight: 800,
                fontSize: '1rem',
                letterSpacing: '0.05em',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                transition: 'all 0.2s',
                textTransform: 'uppercase'
              }}
              onClick={() => setActiveTab('ANOMALIES')}
            >
              Isolation Forest Anomalies
              {anomaliesData?.total_anomalies > 0 && (
                <span style={{ backgroundColor: 'var(--color-warning-dark)', color: 'white', padding: '4px 12px', borderRadius: '12px', fontSize: '0.875rem' }}>
                  {anomaliesData.total_anomalies}
                </span>
              )}
            </button>
          </div>

          {activeTab === 'GRID' && (
            <div style={{ backgroundColor: 'var(--color-bg-white)', padding: '32px' }}>
              {/* FILTERS */}
              <div style={{ display: 'flex', gap: '20px', marginBottom: '32px' }}>
                <select className="input-rail" value={filterRisk} onChange={e => setFilterRisk(e.target.value)} style={{ padding: '12px 24px', fontWeight: 600 }}>
                  <option value="">All Risk Levels</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
                <select className="input-rail" value={filterType} onChange={e => setFilterType(e.target.value)} style={{ padding: '12px 24px', fontWeight: 600 }}>
                  <option value="">All Component Types</option>
                  {uniqueAssetTypes.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>

              {/* ASSET GRID */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
                {filteredAssets.map(asset => (
                  <div 
                    key={asset.asset_code}
                    className="card hover-lift"
                    onClick={() => setSelectedAsset(asset)}
                    style={{ 
                      cursor: 'pointer', 
                      display: 'flex', 
                      flexDirection: 'column', 
                      gap: '16px',
                      borderTop: `4px solid ${getRiskColor(asset.risk_level)}`,
                      backgroundColor: 'var(--color-bg-white)',
                      boxShadow: 'var(--shadow-sm)'
                    }}
                  >
                    <div className="flex-between">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ color: getRiskColor(asset.risk_level) }}>{getAssetIcon(asset.asset_type)}</div>
                        <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', fontSize: '1.125rem', color: 'var(--color-navy)' }}>{asset.asset_code}</span>
                      </div>
                      <span className={`badge ${asset.risk_level === 'CRITICAL' ? 'badge-danger' : asset.risk_level === 'HIGH' ? 'badge-warning' : asset.risk_level === 'MEDIUM' ? 'badge-primary' : 'badge-success'}`}>
                        {asset.risk_level}
                      </span>
                    </div>

                    <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '16px', borderRadius: 'var(--radius-sm)' }}>
                      <div className="flex-between" style={{ marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 800 }}>Health Score</span>
                        <span style={{ fontWeight: 800, color: getRiskColor(asset.risk_level), fontFamily: 'var(--font-mono)' }}>{asset.current_health.toFixed(1)}%</span>
                      </div>
                      <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--color-border)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${asset.current_health}%`, height: '100%', backgroundColor: getRiskColor(asset.risk_level), transition: 'width 1s ease-in-out' }}></div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '0.875rem' }}>
                      <div>
                        <div style={{ color: 'var(--color-text-muted)', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, marginBottom: '4px' }}>Useful Life</div>
                        <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{asset.remaining_life_days} DAYS</div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--color-text-muted)', textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, marginBottom: '4px' }}>Failure Horizon</div>
                        <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: asset.risk_level === 'CRITICAL' ? 'var(--color-danger-dark)' : 'var(--color-navy)' }}>{asset.predicted_failure_date}</div>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredAssets.length === 0 && (
                  <div style={{ gridColumn: '1 / -1', padding: '60px', textAlign: 'center', color: 'var(--color-text-muted)', fontWeight: 700, border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                    NO TELEMETRY SIGNALS DETECTED FOR CURRENT FILTERS
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'ANOMALIES' && anomaliesData && (
            <div style={{ padding: '32px', backgroundColor: 'var(--color-bg-white)' }}>
              {anomaliesData.anomalies.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '60px', border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                  <ShieldCheck size={64} style={{ margin: '0 auto 24px auto', color: 'var(--color-success-dark)', opacity: 0.8 }} />
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-success-dark)' }}>SYSTEM NOMINAL</h3>
                  <p style={{ marginTop: '8px', fontWeight: 600 }}>Isolation Forest ML model detects no structural anomalies in historical maintenance patterns.</p>
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '24px' }}>
                  {anomaliesData.anomalies.map((anom, idx) => (
                    <div key={idx} className="animate-slide-up card" style={{ padding: '24px', backgroundColor: 'var(--color-bg-white)', border: `1px solid var(--color-border)`, borderLeft: `6px solid ${anom.severity === 'HIGH' ? 'var(--color-danger)' : 'var(--color-warning)'}` }}>
                      
                      <div className="flex-between" style={{ alignItems: 'flex-start', marginBottom: '20px' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                            <span className={`badge ${anom.severity === 'HIGH' ? 'badge-danger' : 'badge-warning'}`} style={{ fontSize: '0.875rem', fontWeight: 800 }}>
                              {anom.severity} SEVERITY ANOMALY
                            </span>
                            <span style={{ fontSize: '1.125rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{anom.asset_key}</span>
                          </div>
                          <p style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-main)' }}>{anom.description}</p>
                        </div>
                        
                        <div style={{ textAlign: 'right', backgroundColor: 'var(--color-bg-subtle)', padding: '12px 20px', borderRadius: 'var(--radius-sm)' }}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '4px' }}>Isolation Score</div>
                          <div style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: anom.severity === 'HIGH' ? 'var(--color-danger-dark)' : 'var(--color-warning-dark)' }}>
                            {anom.anomaly_score}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', borderTop: '1px solid var(--color-border)', paddingTop: '20px' }}>
                        <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Defect Frequency</div>
                          <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{anom.pattern_features.defect_frequency}</div>
                        </div>
                        <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Health Drop Rate</div>
                          <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{anom.pattern_features.health_drop_rate.toFixed(1)}/MO</div>
                        </div>
                        <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Avg Days Between</div>
                          <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{anom.pattern_features.days_between_defects.toFixed(1)}</div>
                        </div>
                        <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Speed Restrictions</div>
                          <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{anom.pattern_features.speed_restrictions}</div>
                        </div>
                      </div>

                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      )}

      {/* ASSET DETAIL DRAWER (PREDICTIVE CHART) */}
      {selectedAsset && (
        <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', justifyContent: 'flex-end' }}>
          
          <div className="animate-fade-in" style={{ width: '600px', backgroundColor: 'var(--color-bg-white)', borderLeft: `6px solid ${getRiskColor(selectedAsset.risk_level)}`, display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)' }}>
            
            <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg-subtle)' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>
                  {getAssetIcon(selectedAsset.asset_type)} {selectedAsset.asset_code}
                </h2>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '8px', fontWeight: 800, letterSpacing: '0.05em' }}>
                  LSTM PREDICTIVE ENGINE | CONFIDENCE: {(selectedAsset.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <button onClick={() => setSelectedAsset(null)} className="hover-lift" style={{ padding: '8px', backgroundColor: 'var(--color-bg-white)', borderRadius: '50%' }}><X size={20} /></button>
            </div>

            <div style={{ padding: '32px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '32px' }}>
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <span className={`badge ${selectedAsset.risk_level === 'CRITICAL' ? 'badge-danger' : selectedAsset.risk_level === 'HIGH' ? 'badge-warning' : selectedAsset.risk_level === 'MEDIUM' ? 'badge-primary' : 'badge-success'}`} style={{ padding: '8px 16px', fontSize: '0.875rem', fontWeight: 800 }}>
                  {selectedAsset.risk_level} RISK
                </span>
                <span className="badge badge-neutral" style={{ padding: '8px 16px', fontSize: '0.875rem', fontWeight: 800 }}>{selectedAsset.asset_type} COMPONENT</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '24px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                  <div className="section-heading" style={{ color: 'var(--color-navy)' }}>Current Health Index</div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 800, color: getRiskColor(selectedAsset.risk_level), fontFamily: 'var(--font-mono)' }}>
                    {selectedAsset.current_health.toFixed(1)} <span style={{ fontSize: '1.25rem', color: 'var(--color-text-muted)' }}>/ 100</span>
                  </div>
                </div>
                
                <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '24px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                  <div className="section-heading" style={{ color: 'var(--color-navy)' }}>Remaining Life Span</div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>
                    {selectedAsset.remaining_life_days} <span style={{ fontSize: '1.25rem', color: 'var(--color-text-muted)' }}>DAYS</span>
                  </div>
                </div>
              </div>

              {/* Predictive Chart */}
              <div>
                <h3 className="section-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px', color: 'var(--color-navy)' }}>
                  <TrendingDown size={20} /> DEGRADATION TRAJECTORY (12 MONTHS)
                </h3>
                
                <div style={{ height: '300px', width: '100%', backgroundColor: 'var(--color-bg-white)', padding: '24px 24px 24px 0', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={selectedAsset.health_trajectory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                      <XAxis dataKey="month" stroke="var(--color-text-muted)" fontSize={12} tickFormatter={(val) => `M+${val}`} fontWeight={700} fontFamily="var(--font-mono)" />
                      <YAxis domain={[0, 100]} stroke="var(--color-text-muted)" fontSize={12} fontWeight={700} fontFamily="var(--font-mono)" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: 'var(--color-bg-white)', border: '1px solid var(--color-border)', borderRadius: '4px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}
                        labelFormatter={(val) => `MONTH +${val}`}
                      />
                      <ReferenceLine y={30} stroke="var(--color-danger-dark)" strokeDasharray="4 4" label={{ position: 'top', value: 'FAILURE THRESHOLD', fill: 'var(--color-danger-dark)', fontSize: 10, fontWeight: 800 }} />
                      <ReferenceLine y={50} stroke="var(--color-warning-dark)" strokeDasharray="4 4" label={{ position: 'top', value: 'CRITICAL THRESHOLD', fill: 'var(--color-warning-dark)', fontSize: 10, fontWeight: 800 }} />
                      
                      <Line 
                        type="monotone" 
                        dataKey="predicted_health" 
                        stroke="var(--color-primary)" 
                        strokeWidth={4}
                        dot={{ r: 5, fill: 'var(--color-bg-white)', strokeWidth: 2, stroke: 'var(--color-primary)' }}
                        activeDot={{ r: 8, fill: 'var(--color-primary)', stroke: 'white', strokeWidth: 2 }}
                        name="Health Score"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '12px', textAlign: 'center', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  KERNEL: {selectedAsset.model_used} | DECAY RATE VECTOR: {selectedAsset.decay_rate}
                </div>
              </div>

              {/* Actionable Insights */}
              <div>
                <h3 className="section-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', color: 'var(--color-navy)' }}>
                  <Hammer size={20} /> RECOMMENDED ACTION
                </h3>
                <div style={{ backgroundColor: selectedAsset.risk_level === 'CRITICAL' ? 'var(--color-danger-bg)' : 'var(--color-bg-subtle)', padding: '24px', borderRadius: 'var(--radius-md)', border: `1px solid ${selectedAsset.risk_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.3)' : 'var(--color-border)'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px dashed var(--color-border)' }}>
                    <span style={{ fontWeight: 700, color: 'var(--color-text-muted)' }}>Predicted Failure Date</span>
                    <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{selectedAsset.predicted_failure_date}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 700, color: 'var(--color-text-muted)' }}>MANDATORY MAINTENANCE BY</span>
                    <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-primary)' }}>{selectedAsset.maintenance_recommended_date}</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Assets;
