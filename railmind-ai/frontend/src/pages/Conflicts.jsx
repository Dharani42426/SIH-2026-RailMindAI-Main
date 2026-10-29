import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, ShieldCheck, AlertTriangle, PlayCircle, 
  CheckCircle2, XCircle, Clock, Map, Info, FileText, Activity,
  AlertOctagon, ServerCrash, Radar, Zap, X, BrainCircuit
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Conflicts = () => {
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [error, setError] = useState(null);
  
  const [validatingAction, setValidatingAction] = useState(false);
  const [approvalError, setApprovalError] = useState(null);
  const [approvalBlockedReport, setApprovalBlockedReport] = useState(null);
  
  const [sections, setSections] = useState([]);
  
  // Validation Simulator State
  const [simulatorSection, setSimulatorSection] = useState('');
  const [simulatorDate, setSimulatorDate] = useState('');
  const [simulatorStart, setSimulatorStart] = useState('10:00');
  const [simulatorEnd, setSimulatorEnd] = useState('12:00');
  const [simulatorResult, setSimulatorResult] = useState(null);
  const [runningSimulator, setRunningSimulator] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoadingPlans(true);
        const [plansRes, sectionsRes] = await Promise.all([
          axios.get(`${BACKEND_URL}/api/optimizer/plans`),
          axios.get(`${BACKEND_URL}/api/sections/`)
        ]);
        
        setPlans(plansRes.data);
        setSections(sectionsRes.data);
        
        if (sectionsRes.data.length > 0) {
          setSimulatorSection(sectionsRes.data[0].id.toString());
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          setSimulatorDate(tomorrow.toISOString().split('T')[0]);
        }
      } catch (err) {
        setError("CRITICAL: FAILED TO ESTABLISH UPLINK WITH SECURITY CORE.");
      } finally {
        setLoadingPlans(false);
      }
    };
    fetchInitialData();
  }, []);

  const handleApprove = async (planId) => {
    try {
      setValidatingAction(true);
      setApprovalError(null);
      setApprovalBlockedReport(null);
      await axios.post(`${BACKEND_URL}/api/optimizer/plans/${planId}/approve?approved_by=Chief_Controller`);
      
      const plansRes = await axios.get(`${BACKEND_URL}/api/optimizer/plans`);
      setPlans(plansRes.data);
      if (selectedPlan && selectedPlan.id === planId) {
        setSelectedPlan(plansRes.data.find(p => p.id === planId));
      }
    } catch (err) {
      if (err.response && err.response.status === 409) {
          setApprovalError("AUTHORIZATION DENIED: FATAL SAFETY CONFLICT");
          if (err.response.data.safety_report) {
              setApprovalBlockedReport(err.response.data.safety_report);
          }
      } else {
          setApprovalError("System error during authorization sequence.");
      }
      
      const plansRes = await axios.get(`${BACKEND_URL}/api/optimizer/plans`);
      setPlans(plansRes.data);
      if (selectedPlan && selectedPlan.id === planId) {
        setSelectedPlan(plansRes.data.find(p => p.id === planId));
      }
    } finally {
      setValidatingAction(false);
    }
  };

  const handleReject = async (planId) => {
    try {
      setValidatingAction(true);
      await axios.post(`${BACKEND_URL}/api/optimizer/plans/${planId}/reject?reason=Controller_Rejected`);
      const plansRes = await axios.get(`${BACKEND_URL}/api/optimizer/plans`);
      setPlans(plansRes.data);
      if (selectedPlan && selectedPlan.id === planId) {
        setSelectedPlan(plansRes.data.find(p => p.id === planId));
      }
    } catch (err) {
      alert("Failed to reject plan.");
    } finally {
      setValidatingAction(false);
    }
  };

  const runLiveValidation = async (e) => {
    e.preventDefault();
    if (!simulatorSection || !simulatorDate || !simulatorStart || !simulatorEnd) return;
    
    setRunningSimulator(true);
    setSimulatorResult(null);
    
    try {
      const res = await axios.get(
        `${BACKEND_URL}/api/trains/section/${simulatorSection}/conflicts`, 
        { params: { block_date: simulatorDate, block_start: simulatorStart, block_end: simulatorEnd, line: "BOTH" } }
      );
      setSimulatorResult(res.data);
    } catch (err) {
      alert("Failed to run safety validation check.");
    } finally {
      setRunningSimulator(false);
    }
  };

  const draftPlans = plans.filter(p => p.status === 'DRAFT').length;
  const approvedPlans = plans.filter(p => p.status === 'APPROVED').length;
  const rejectedPlans = plans.filter(p => p.status === 'REJECTED').length;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px', position: 'relative', minHeight: '100%' }}>
      
      {/* HEADER */}
      <div className="flex-between">
        <div>
          <h1 className="page-title" style={{ color: 'var(--color-danger-dark)' }}>
            <AlertOctagon size={32} /> SAFETY COMMAND CENTER
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, letterSpacing: '0.05em' }}>
            <Radar size={16} color="var(--color-danger)" /> ACTIVE COLLISION AVOIDANCE & AUTHORIZATION GATES
          </p>
        </div>
      </div>

      {error && (
        <div style={{ padding: '24px', backgroundColor: 'var(--color-danger-bg)', border: '2px solid var(--color-danger)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '16px', fontWeight: 800, borderRadius: 'var(--radius-md)', fontSize: '1.25rem', textTransform: 'uppercase' }}>
          <ServerCrash size={32} />
          {error}
        </div>
      )}

      {/* KPIs */}
      <div className="grid-cols-4 animate-slide-up">
        <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-primary)' }}>
          <div className="flex-between" style={{ marginBottom: '12px' }}>
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Registered Plans</div>
            <FileText size={24} color="var(--color-primary)" />
          </div>
          <div className="kpi-value">{plans.length}</div>
        </div>
        
        <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-warning-dark)' }}>
          <div className="flex-between" style={{ marginBottom: '12px' }}>
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-warning-dark)' }}>Pending Clearance</div>
            <Clock size={24} color="var(--color-warning)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-warning-dark)' }}>{draftPlans}</div>
        </div>

        <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-success-dark)' }}>
          <div className="flex-between" style={{ marginBottom: '12px' }}>
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-success-dark)' }}>Safety Confirmed</div>
            <ShieldCheck size={24} color="var(--color-success)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-success-dark)' }}>{approvedPlans}</div>
        </div>

        <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-danger-dark)', backgroundColor: 'var(--color-danger-bg)' }}>
          <div className="flex-between" style={{ marginBottom: '12px' }}>
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-danger-dark)' }}>Critical Violations</div>
            <XCircle size={24} color="var(--color-danger-dark)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-danger-dark)' }}>{rejectedPlans}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '32px' }} className="animate-slide-up">
        
        {/* PLAN HISTORY TABLE */}
        <div className="panel" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div className="panel-header" style={{ color: 'var(--color-navy)' }}>
            <Activity color="var(--color-primary)" size={20} /> AUTHORIZATION REGISTRY
          </div>
          
          <div style={{ overflowX: 'auto', flex: 1, backgroundColor: 'var(--color-bg-white)' }}>
            <table className="rail-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '32px' }}>Clearance Code</th>
                  <th>Target Window</th>
                  <th>Operations</th>
                  <th style={{ paddingRight: '32px' }}>Authorization Status</th>
                </tr>
              </thead>
              <tbody>
                {loadingPlans ? (
                  <tr>
                    <td colSpan="4" style={{ padding: '60px', textAlign: 'center', color: 'var(--color-primary)' }}><Activity className="animate-spin" size={48} /></td>
                  </tr>
                ) : plans.length === 0 ? (
                  <tr>
                    <td colSpan="4" style={{ padding: '60px', textAlign: 'center', color: 'var(--color-text-muted)', fontWeight: 700 }}>NO PLANS REGISTERED IN SYSTEM</td>
                  </tr>
                ) : (
                  plans.map(plan => (
                    <tr 
                      key={plan.id}
                      onClick={() => setSelectedPlan(plan)}
                      style={{ cursor: 'pointer', backgroundColor: selectedPlan?.id === plan.id ? 'var(--color-primary-light)' : 'transparent', borderLeft: selectedPlan?.id === plan.id ? '4px solid var(--color-primary)' : '4px solid transparent' }}
                      className="hover-lift"
                    >
                      <td style={{ paddingLeft: '32px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{plan.plan_code}</td>
                      <td style={{ fontWeight: 600 }}>{plan.date_range}</td>
                      <td>
                        <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{plan.tasks_scheduled}</span> TASKS
                      </td>
                      <td style={{ paddingRight: '32px' }}>
                        <span className={`badge ${
                          plan.status === 'APPROVED' ? 'badge-success' : 
                          plan.status === 'REJECTED' ? 'badge-danger' : 
                          plan.status === 'DRAFT' ? 'badge-warning' : 'badge-neutral'
                        }`} style={{ padding: '6px 12px', fontSize: '0.75rem', fontWeight: 800 }}>
                          {plan.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* LIVE SAFETY SIMULATOR */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', borderColor: 'var(--color-danger)', border: '2px solid var(--color-danger)' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-danger)', backgroundColor: 'var(--color-danger-bg)' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-danger-dark)', textTransform: 'uppercase' }}>
              <Zap size={24} />
              LIVE SAFETY OVERRIDE SIMULATOR
            </h2>
          </div>
          
          <div style={{ padding: '24px', backgroundColor: 'var(--color-bg-white)', flex: 1 }}>
            <form onSubmit={runLiveValidation} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-danger-dark)', marginBottom: '8px', textTransform: 'uppercase' }}>Target Corridor</label>
                <select className="input-rail" value={simulatorSection} onChange={e => setSimulatorSection(e.target.value)} required style={{ borderColor: 'var(--color-border)', fontWeight: 600 }}>
                  {sections.map(sec => <option key={sec.id} value={sec.id}>{sec.section_code}</option>)}
                </select>
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-danger-dark)', marginBottom: '8px', textTransform: 'uppercase' }}>Simulation Date</label>
                <input type="date" className="input-rail" value={simulatorDate} onChange={e => setSimulatorDate(e.target.value)} required style={{ borderColor: 'var(--color-border)', fontWeight: 600 }} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-danger-dark)', marginBottom: '8px', textTransform: 'uppercase' }}>Start (HH:MM)</label>
                  <input type="time" className="input-rail" value={simulatorStart} onChange={e => setSimulatorStart(e.target.value)} required style={{ borderColor: 'var(--color-border)', fontWeight: 600 }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-danger-dark)', marginBottom: '8px', textTransform: 'uppercase' }}>End (HH:MM)</label>
                  <input type="time" className="input-rail" value={simulatorEnd} onChange={e => setSimulatorEnd(e.target.value)} required style={{ borderColor: 'var(--color-border)', fontWeight: 600 }} />
                </div>
              </div>
              
              <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '8px', padding: '16px', backgroundColor: 'var(--color-danger-dark)', fontWeight: 800, fontSize: '1rem' }} disabled={runningSimulator}>
                {runningSimulator ? <Activity size={20} className="animate-spin" /> : <Radar size={20} />}
                {runningSimulator ? 'RUNNING AI SAFETY ANALYSIS...' : 'INITIATE SAFETY SCAN'}
              </button>
            </form>

            {/* SIMULATOR RESULTS */}
            {simulatorResult && (
              <div className="animate-fade-in" style={{ marginTop: '24px', paddingTop: '24px', borderTop: '2px solid var(--color-border)' }}>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                  <div style={{ 
                    width: '48px', height: '48px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backgroundColor: simulatorResult.has_conflicts ? 'var(--color-danger-dark)' : 'var(--color-success-dark)', color: 'white'
                  }}>
                    {simulatorResult.has_conflicts ? <XCircle size={28} /> : <ShieldCheck size={28} />}
                  </div>
                  <div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: simulatorResult.has_conflicts ? 'var(--color-danger-dark)' : 'var(--color-success-dark)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {simulatorResult.has_conflicts ? 'CRITICAL SAFETY VIOLATION' : 'CLEARANCE VERIFIED'}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--color-text-main)', fontWeight: 700, marginTop: '4px' }}>
                      {simulatorResult.has_conflicts ? `${simulatorResult.total_conflicts} CONFLICTS DETECTED` : 'No overlapping schedules found.'}
                    </div>
                  </div>
                </div>

                {simulatorResult.has_conflicts && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflowY: 'auto', paddingRight: '8px' }}>
                    
                    {/* AI MITIGATION SECTION */}
                    {simulatorResult.ai_mitigation && (
                      <div className="animate-slide-up" style={{ backgroundColor: 'var(--color-navy)', padding: '16px', borderRadius: 'var(--radius-sm)', borderLeft: '6px solid var(--color-primary)', color: 'white', marginBottom: '8px' }}>
                        <div style={{ fontWeight: 800, fontSize: '1rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-primary-light)', textTransform: 'uppercase' }}>
                          <BrainCircuit size={20} /> AI MITIGATION STRATEGY
                        </div>
                        <div style={{ fontSize: '0.9rem', lineHeight: '1.5', fontWeight: 600 }}>
                          {simulatorResult.ai_mitigation}
                        </div>
                      </div>
                    )}

                    {simulatorResult.conflicts.map((c, idx) => (
                      <div key={idx} style={{ backgroundColor: 'var(--color-bg-white)', padding: '16px', borderRadius: 'var(--radius-sm)', border: `1px solid ${c.is_high_priority ? 'var(--color-danger)' : 'var(--color-warning)'}`, borderLeft: `6px solid ${c.is_high_priority ? 'var(--color-danger-dark)' : 'var(--color-warning-dark)'}` }}>
                        <div style={{ fontWeight: 800, fontSize: '1rem', marginBottom: '4px', display: 'flex', justifyContent: 'space-between', color: 'var(--color-navy)' }}>
                          <span>{c.train_name} ({c.train_no})</span>
                          <span className={`badge ${c.is_high_priority ? 'badge-danger' : 'badge-warning'}`}>P-{c.priority}</span>
                        </div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                          {c.description}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* PLAN DETAIL DRAWER */}
      {selectedPlan && (
        <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', justifyContent: 'flex-end' }}>
          
          <div className="animate-fade-in" style={{ width: '600px', backgroundColor: 'var(--color-bg-main)', borderLeft: '1px solid var(--color-danger)', boxShadow: 'var(--shadow-lg)', display: 'flex', flexDirection: 'column' }}>
            
            <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-danger)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-danger-bg)' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-danger-dark)', fontFamily: 'var(--font-mono)' }}>
                  <AlertOctagon size={28} /> {selectedPlan.plan_code}
                </h2>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-danger-dark)', marginTop: '8px', fontWeight: 700, letterSpacing: '0.05em' }}>
                  TIMESTAMP: {new Date(selectedPlan.generated_at).toLocaleString()}
                </div>
              </div>
              <button onClick={() => { setSelectedPlan(null); setApprovalError(null); setApprovalBlockedReport(null); }} className="hover-lift" style={{ padding: '8px', backgroundColor: 'var(--color-bg-white)', color: 'var(--color-danger-dark)', borderRadius: '50%' }}><X size={20} /></button>
            </div>

            <div style={{ padding: '32px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '32px' }}>
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <span className={`badge ${selectedPlan.status === 'APPROVED' ? 'badge-success' : selectedPlan.status === 'REJECTED' ? 'badge-danger' : selectedPlan.status === 'DRAFT' ? 'badge-warning' : 'badge-neutral'}`} style={{ padding: '8px 16px', fontSize: '0.875rem', fontWeight: 800 }}>
                  STATUS: {selectedPlan.status}
                </span>
                <span className="badge badge-neutral" style={{ padding: '8px 16px', fontSize: '0.875rem', fontWeight: 800 }}>TYPE: {selectedPlan.plan_type}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div className="card" style={{ padding: '24px', borderRadius: 'var(--radius-md)' }}>
                  <div className="section-heading" style={{ color: 'var(--color-navy)' }}>Total Operations</div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-primary)' }}>{selectedPlan.total_blocks}</div>
                </div>
                <div className="card" style={{ padding: '24px', borderRadius: 'var(--radius-md)' }}>
                  <div className="section-heading" style={{ color: 'var(--color-navy)' }}>Scheduled Tasks</div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-primary)' }}>{selectedPlan.tasks_scheduled}</div>
                </div>
              </div>

              {/* SECURITY WARNING */}
              <div style={{ backgroundColor: 'var(--color-danger-bg)', border: '2px solid var(--color-danger)', padding: '24px', borderRadius: 'var(--radius-md)' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-danger-dark)', textTransform: 'uppercase', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={24} /> SAFETY GATE PROTOCOL
                </h3>
                
                <div style={{ fontSize: '0.875rem', color: 'var(--color-text-main)', lineHeight: '1.6', fontWeight: 600 }}>
                  <p style={{ margin: '0 0 16px 0' }}>The AI Optimizer conducts preliminary safety checks during generation. However, <strong>AUTHORITATIVE RE-VALIDATION IS MANDATORY</strong> prior to network deployment.</p>
                  <p style={{ margin: '0 0 16px 0' }}>Approval will trigger an immediate, live scan against the most current dispatch timetable. If overlaps are detected, the system will block authorization.</p>
                  <div style={{ padding: '12px', backgroundColor: 'var(--color-bg-white)', borderLeft: '4px solid var(--color-danger)', fontWeight: 800, color: 'var(--color-danger-dark)' }}>
                    ACTION REQUIRED: AUTHORIZE OR REJECT THIS DRAFT.
                  </div>
                </div>
              </div>

              {/* ACTION CONTROLS */}
              {selectedPlan.status === 'DRAFT' && (
                <div style={{ marginTop: 'auto', paddingTop: '24px' }}>
                  {approvalError && (
                    <div className="animate-slide-up" style={{ marginBottom: '24px', backgroundColor: 'var(--color-danger-dark)', color: 'white', padding: '24px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '16px', boxShadow: 'var(--shadow-md)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 800, fontSize: '1.25rem', letterSpacing: '0.05em' }}>
                        <XCircle size={32} /> {approvalError}
                      </div>
                      {approvalBlockedReport && approvalBlockedReport.violations.length > 0 && (
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.1)', padding: '16px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.875rem', fontWeight: 700 }}>
                          {approvalBlockedReport.violations.map((v, i) => (
                            <div key={i} style={{ marginBottom: '8px' }}>{`> ${v.type}: ${v.description}`}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <button 
                      className="btn btn-outline" 
                      onClick={() => handleReject(selectedPlan.id)}
                      disabled={validatingAction}
                      style={{ justifyContent: 'center', padding: '20px', fontSize: '1.125rem', borderColor: 'var(--color-danger)', color: 'var(--color-danger-dark)', fontWeight: 800, backgroundColor: 'var(--color-bg-white)' }}
                    >
                      {validatingAction ? 'PROCESSING...' : 'REJECT PLAN'}
                    </button>
                    <button 
                      className="btn btn-primary" 
                      onClick={() => handleApprove(selectedPlan.id)}
                      disabled={validatingAction}
                      style={{ justifyContent: 'center', padding: '20px', fontSize: '1.125rem', backgroundColor: 'var(--color-success-dark)', fontWeight: 800 }}
                    >
                      {validatingAction ? (
                        <><Activity size={24} className="animate-spin" style={{ marginRight: '12px' }}/> EXECUTING SCAN...</>
                      ) : (
                        <><ShieldCheck size={24} style={{ marginRight: '12px' }}/> APPROVE & DEPLOY</>
                      )}
                    </button>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Conflicts;
