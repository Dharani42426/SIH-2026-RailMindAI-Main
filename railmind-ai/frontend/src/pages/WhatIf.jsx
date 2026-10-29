import React, { useState, useEffect } from 'react';
import { 
  GitMerge, Activity, FileText, Settings, PlayCircle, 
  ArrowRight, ShieldCheck, ShieldAlert, AlertTriangle, X,
  FlaskConical, ArrowRightLeft, DatabaseZap, Network, FileDigit, CheckCircle2
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const WhatIf = () => {
  const [plans, setPlans] = useState([]);
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [error, setError] = useState(null);
  
  const [changes, setChanges] = useState([]);
  const [actionType, setActionType] = useState('remove_train');
  
  // States for different perturbation actions
  const [trainNo, setTrainNo] = useState('');
  const [taskCode, setTaskCode] = useState('');
  const [taskSeverity, setTaskSeverity] = useState('CRITICAL');
  const [delayMinutes, setDelayMinutes] = useState(30);
  const [addTrainName, setAddTrainName] = useState('Special Express');
  const [addTrainEntry, setAddTrainEntry] = useState('12:00');
  const [addTrainExit, setAddTrainExit] = useState('14:00');
  const [emergencyKmFrom, setEmergencyKmFrom] = useState(10.0);
  const [emergencyKmTo, setEmergencyKmTo] = useState(15.0);
  const [emergencyDuration, setEmergencyDuration] = useState(2.0);
  
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simError, setSimError] = useState(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/optimizer/plans`);
        setPlans(res.data);
      } catch (err) {
        setError("Uplink failed. Cannot load base operations plans.");
      } finally {
        setLoadingPlans(false);
      }
    };
    fetchPlans();
  }, []);

  const addChange = () => {
    if (actionType === 'remove_train' && trainNo.trim()) {
      setChanges([...changes, { action: 'remove_train', train_no: trainNo.trim() }]);
      setTrainNo('');
    } else if (actionType === 'delay_train' && trainNo.trim() && delayMinutes > 0) {
      setChanges([...changes, { action: 'delay_train', train_no: trainNo.trim(), delay_minutes: delayMinutes }]);
      setTrainNo('');
    } else if (actionType === 'add_train' && trainNo.trim()) {
      setChanges([...changes, { 
        action: 'add_train', 
        train_no: trainNo.trim(), 
        train_name: addTrainName, 
        entry_time: addTrainEntry, 
        exit_time: addTrainExit 
      }]);
      setTrainNo('');
    } else if (actionType === 'change_task_severity' && taskCode.trim()) {
      setChanges([...changes, { action: 'change_task_severity', task_code: taskCode.trim(), severity: taskSeverity }]);
      setTaskCode('');
    } else if (actionType === 'add_critical_task' && taskCode.trim()) {
      setChanges([...changes, {
        action: 'add_critical_task',
        task_code: taskCode.trim(),
        km_from: emergencyKmFrom,
        km_to: emergencyKmTo,
        duration: emergencyDuration
      }]);
      setTaskCode('');
    }
  };

  const removeChange = (indexToRemove) => {
    setChanges(changes.filter((_, idx) => idx !== indexToRemove));
  };

  const runSimulation = async () => {
    if (!selectedPlanId) { setSimError("Please select a base plan to simulate."); return; }
    if (changes.length === 0) { setSimError("Please add at least one scenario modification parameter."); return; }
    
    setSimulating(true);
    setSimResult(null);
    setSimError(null);
    
    try {
      const payload = { plan_id: parseInt(selectedPlanId), changes: changes };
      const res = await axios.post(`${BACKEND_URL}/api/optimizer/what-if`, payload);
      setSimResult(res.data);
    } catch (err) {
      if (err.response?.data?.detail) {
        setSimError(err.response.data.detail);
      } else {
        setSimError("Simulation kernel failure. Parameters rejected by optimizer.");
      }
    } finally {
      setSimulating(false);
    }
  };

  const selectedPlan = plans.find(p => p.id.toString() === selectedPlanId);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px', minHeight: '100%' }}>
      
      {/* HEADER */}
      <div className="flex-between">
        <div>
          <h1 className="page-title" style={{ color: 'var(--color-navy)' }}>
            <FlaskConical size={32} color="#8B5CF6" /> 
            CP-SAT SCENARIO SANDBOX
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <Network size={16} /> Multi-Agent Negotiation & Perturbation Testing Engine
          </p>
        </div>
      </div>

      {error && (
        <div style={{ padding: '24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid var(--color-danger)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 700, borderRadius: 'var(--radius-md)' }}>
          <AlertTriangle size={24} /> {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '32px' }} className="animate-slide-up">
        
        {/* LEFT COLUMN: SETUP */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
            <div className="panel-header" style={{ color: 'var(--color-navy)' }}>
              <FileDigit color="var(--color-primary)" size={20} /> BASE OPERATIONS PLAN
            </div>
            
            <div style={{ padding: '24px', backgroundColor: 'var(--color-bg-white)', flex: 1 }}>
              {loadingPlans ? (
                <div className="flex-center" style={{ padding: '20px', color: 'var(--color-primary)' }}><Activity className="animate-spin" size={32} /></div>
              ) : plans.length === 0 ? (
                <div className="flex-center" style={{ padding: '20px', color: 'var(--color-warning-dark)', fontWeight: 700 }}>No base plans found in core.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <select 
                    className="input-rail"
                    value={selectedPlanId}
                    onChange={(e) => { setSelectedPlanId(e.target.value); setSimResult(null); }}
                    style={{ width: '100%', fontSize: '1rem', fontWeight: 700 }}
                  >
                    <option value="" disabled>Select Target Plan Identity</option>
                    {plans.map(p => (
                      <option key={p.id} value={p.id}>{p.plan_code} [ {p.status} ] — {p.date_range}</option>
                    ))}
                  </select>
                  
                  {selectedPlan && (
                    <div className="animate-fade-in" style={{ backgroundColor: 'var(--color-bg-subtle)', padding: '20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '0.875rem' }}>
                        <div><span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 800 }}>Lifecycle Status</span> <strong className={`badge ${selectedPlan.status === 'APPROVED' ? 'badge-success' : selectedPlan.status === 'DRAFT' ? 'badge-warning' : 'badge-neutral'}`} style={{ fontSize: '0.75rem', fontWeight: 800 }}>{selectedPlan.status}</strong></div>
                        <div><span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 800 }}>Date Scope</span> <strong style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{selectedPlan.date_range}</strong></div>
                        <div><span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 800 }}>Blocks</span> <strong style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{selectedPlan.total_blocks}</strong></div>
                        <div><span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 800 }}>Tasks Scheduled</span> <strong style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{selectedPlan.tasks_scheduled}</strong></div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden', border: '2px solid #8B5CF6' }}>
            <div className="panel-header" style={{ color: '#6D28D9', backgroundColor: 'rgba(139, 92, 246, 0.1)', borderBottom: '1px solid rgba(139, 92, 246, 0.2)' }}>
              <ArrowRightLeft color="#8B5CF6" size={20} /> SCENARIO PERTURBATIONS
            </div>
            
            <div style={{ padding: '24px', backgroundColor: 'var(--color-bg-white)', flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Injection Parameter</label>
                  <select className="input-rail" value={actionType} onChange={e => setActionType(e.target.value)} style={{ width: '100%', borderColor: 'rgba(139, 92, 246, 0.4)', fontWeight: 600 }}>
                    <option value="remove_train">Cancel / Divert Live Train</option>
                    <option value="delay_train">Inject Train Delay</option>
                    <option value="add_train">Inject Special Train</option>
                    <option value="change_task_severity">Inject Task Severity Spike</option>
                    <option value="add_critical_task">Inject Emergency Critical Task</option>
                  </select>
                </div>
              </div>
              
              {actionType === 'remove_train' && (
                <div className="animate-fade-in">
                  <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Target Train Identity</label>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <input type="text" className="input-rail" placeholder="e.g. 12124" value={trainNo} onChange={e => setTrainNo(e.target.value)} style={{ flex: 1, fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    <button className="btn btn-outline" onClick={addChange} style={{ borderColor: '#8B5CF6', color: '#6D28D9', fontWeight: 800 }}>INJECT</button>
                  </div>
                </div>
              )}
              
              {actionType === 'delay_train' && (
                <div className="animate-fade-in" style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}>
                    <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Target Train Identity</label>
                    <input type="text" className="input-rail" placeholder="e.g. 12124" value={trainNo} onChange={e => setTrainNo(e.target.value)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                  </div>
                  <div style={{ width: '140px' }}>
                    <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Delay (Minutes)</label>
                    <input type="number" className="input-rail" placeholder="30" value={delayMinutes} onChange={e => setDelayMinutes(parseInt(e.target.value) || 0)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                  </div>
                  <button className="btn btn-outline" onClick={addChange} style={{ borderColor: '#8B5CF6', color: '#6D28D9', fontWeight: 800 }}>INJECT</button>
                </div>
              )}

              {actionType === 'add_train' && (
                <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Special Train No.</label>
                      <input type="text" className="input-rail" placeholder="e.g. SPCL-01" value={trainNo} onChange={e => setTrainNo(e.target.value)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                    <div style={{ flex: 2 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Train Name</label>
                      <input type="text" className="input-rail" placeholder="Special Express" value={addTrainName} onChange={e => setAddTrainName(e.target.value)} style={{ width: '100%', fontWeight: 700 }} />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Entry Time (HH:MM)</label>
                      <input type="time" className="input-rail" value={addTrainEntry} onChange={e => setAddTrainEntry(e.target.value)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Exit Time (HH:MM)</label>
                      <input type="time" className="input-rail" value={addTrainExit} onChange={e => setAddTrainExit(e.target.value)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                    <button className="btn btn-outline" onClick={addChange} style={{ borderColor: '#8B5CF6', color: '#6D28D9', fontWeight: 800 }}>INJECT</button>
                  </div>
                </div>
              )}
              
              {actionType === 'change_task_severity' && (
                <div className="animate-fade-in" style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}>
                    <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Task Code</label>
                    <input type="text" className="input-rail" placeholder="e.g. TRD-001" value={taskCode} onChange={e => setTaskCode(e.target.value)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                  </div>
                  <div style={{ width: '140px' }}>
                    <label className="section-heading" style={{ color: 'var(--color-navy)' }}>New Severity</label>
                    <select className="input-rail" value={taskSeverity} onChange={e => setTaskSeverity(e.target.value)} style={{ width: '100%', fontWeight: 700 }}>
                      <option value="CRITICAL">CRITICAL</option>
                      <option value="HIGH">HIGH</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="LOW">LOW</option>
                    </select>
                  </div>
                  <button className="btn btn-outline" onClick={addChange} style={{ borderColor: '#8B5CF6', color: '#6D28D9', fontWeight: 800 }}>INJECT</button>
                </div>
              )}

              {actionType === 'add_critical_task' && (
                <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Emergency Task Code</label>
                      <input type="text" className="input-rail" placeholder="e.g. EMG-RAIL-01" value={taskCode} onChange={e => setTaskCode(e.target.value)} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>KM From</label>
                      <input type="number" step="0.1" className="input-rail" value={emergencyKmFrom} onChange={e => setEmergencyKmFrom(parseFloat(e.target.value))} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>KM To</label>
                      <input type="number" step="0.1" className="input-rail" value={emergencyKmTo} onChange={e => setEmergencyKmTo(parseFloat(e.target.value))} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label className="section-heading" style={{ color: 'var(--color-navy)' }}>Duration (Hrs)</label>
                      <input type="number" step="0.5" className="input-rail" value={emergencyDuration} onChange={e => setEmergencyDuration(parseFloat(e.target.value))} style={{ width: '100%', fontFamily: 'var(--font-mono)', fontWeight: 700 }} />
                    </div>
                    <button className="btn btn-outline" onClick={addChange} style={{ borderColor: '#8B5CF6', color: '#6D28D9', fontWeight: 800 }}>INJECT</button>
                  </div>
                </div>
              )}
              
              <div style={{ marginTop: '16px', borderTop: '1px solid var(--color-border)', paddingTop: '24px' }}>
                <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Active Scenario Vector</h3>
                {changes.length === 0 ? (
                  <div style={{ padding: '16px', border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-md)', textAlign: 'center', color: 'var(--color-text-muted)', fontWeight: 700, fontSize: '0.875rem' }}>NO PERTURBATIONS INJECTED</div>
                ) : (
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {changes.map((change, idx) => (
                      <li key={idx} className="animate-slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(139, 92, 246, 0.05)', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '12px 16px', borderRadius: 'var(--radius-sm)', fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-navy)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <DatabaseZap size={16} color="#8B5CF6" />
                          {change.action === 'remove_train' && <span>TRAIN SUPPRESSION: <span style={{ fontFamily: 'var(--font-mono)', color: '#6D28D9' }}>{change.train_no}</span></span>}
                          {change.action === 'delay_train' && <span>TRAIN DELAY: <span style={{ fontFamily: 'var(--font-mono)', color: '#6D28D9' }}>{change.train_no} (+{change.delay_minutes} min)</span></span>}
                          {change.action === 'add_train' && <span>SPECIAL TRAIN: <span style={{ fontFamily: 'var(--font-mono)', color: '#6D28D9' }}>{change.train_no} ({change.entry_time}-{change.exit_time})</span></span>}
                          {change.action === 'change_task_severity' && <span>SEVERITY OVERRIDE: <span style={{ fontFamily: 'var(--font-mono)' }}>{change.task_code}</span> &rarr; <span style={{ color: 'var(--color-warning-dark)' }}>{change.severity}</span></span>}
                          {change.action === 'add_critical_task' && <span>EMERGENCY TASK: <span style={{ fontFamily: 'var(--font-mono)' }}>{change.task_code}</span> at KM {change.km_from}-{change.km_to} ({change.duration} Hrs)</span>}
                        </div>
                        <button onClick={() => removeChange(idx)} className="hover-lift" style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}><X size={18} /></button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              
              <button 
                className="btn btn-primary" 
                onClick={runSimulation}
                disabled={simulating || !selectedPlanId || changes.length === 0}
                style={{ width: '100%', justifyContent: 'center', marginTop: 'auto', fontSize: '1rem', padding: '16px', backgroundColor: '#8B5CF6', fontWeight: 800, letterSpacing: '0.05em', border: 'none' }}
              >
                {simulating ? <><Activity size={20} className="animate-spin" style={{ marginRight: '8px' }}/> EXECUTING CP-SAT SOLVER...</> : <><PlayCircle size={20} style={{ marginRight: '8px' }}/> INITIATE SCENARIO SIMULATION</>}
              </button>
              
              {simError && (
                <div className="animate-fade-in" style={{ color: 'var(--color-danger-dark)', fontSize: '0.875rem', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '16px', borderRadius: 'var(--radius-sm)', marginTop: '8px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} /> {simError}
                </div>
              )}
              
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: RESULTS */}
        <div>
          {simulating ? (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '600px', backgroundColor: 'var(--color-bg-white)' }}>
              <div style={{ position: 'relative', width: '120px', height: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '24px' }}>
                <div style={{ position: 'absolute', width: '100%', height: '100%', borderRadius: '50%', border: '4px solid rgba(139, 92, 246, 0.2)', borderTopColor: '#8B5CF6', animation: 'spin 1s linear infinite' }}></div>
                <DatabaseZap size={48} color="#8B5CF6" />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '0 0 12px 0', color: '#6D28D9' }}>RE-OPTIMIZING TRAJECTORY</h2>
              <p style={{ color: 'var(--color-text-muted)', margin: 0, textAlign: 'center', fontWeight: 600, fontSize: '0.875rem', maxWidth: '350px', lineHeight: 1.6 }}>
                Executing Multi-Agent Negotiation protocol and applying CP-SAT constraints for perturbed scenario state.
              </p>
            </div>
          ) : simResult ? (
            <div className="animate-slide-up" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              
              {/* SAFETY AUTHORITATIVE RESULT */}
              <div className="card" style={{ borderLeft: `6px solid ${simResult.safety_report?.safe ? 'var(--color-success-dark)' : 'var(--color-danger-dark)'}`, padding: '32px' }}>
                <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Scenario Safety Kernel</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                  <div style={{ 
                    width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backgroundColor: simResult.safety_report?.safe ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
                    color: simResult.safety_report?.safe ? 'var(--color-success-dark)' : 'var(--color-danger-dark)'
                  }}>
                    {simResult.safety_report?.safe ? <ShieldCheck size={36} /> : <ShieldAlert size={36} />}
                  </div>
                  <div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: simResult.safety_report?.safe ? 'var(--color-success-dark)' : 'var(--color-danger-dark)', letterSpacing: '0.05em' }}>
                      {simResult.safety_report?.safe ? 'VALIDATED SAFE' : 'UNSAFE VECTOR DETECTED'}
                    </div>
                    <div style={{ fontSize: '1rem', color: 'var(--color-text-main)', marginTop: '8px', fontWeight: 600 }}>
                      ConflictResolver verified <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{simResult.safety_report?.checks_passed}</span> block constraints successfully.
                    </div>
                  </div>
                </div>
                
                {!simResult.safety_report?.safe && simResult.safety_report?.violations?.length > 0 && (
                  <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {simResult.safety_report.violations.map((v, i) => (
                      <div key={i} style={{ backgroundColor: 'var(--color-danger-bg)', padding: '16px', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--color-danger)', fontSize: '0.875rem', color: 'var(--color-danger-dark)', fontWeight: 700 }}>
                        <span style={{ fontWeight: 800 }}>{v.type}:</span> {v.description}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* COMPARISON METRICS */}
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '24px 32px', backgroundColor: 'var(--color-bg-subtle)', borderBottom: '1px solid var(--color-border)' }}>
                  <h3 className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Telemetry Variance (Base vs Scenario)</h3>
                </div>
                
                <table className="rail-table">
                  <thead>
                    <tr>
                      <th style={{ paddingLeft: '32px' }}>Optimization Metric</th>
                      <th>Base Trajectory</th>
                      <th></th>
                      <th>Scenario Trajectory</th>
                      <th style={{ paddingRight: '32px' }}>Variance (Δ)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ paddingLeft: '32px', fontWeight: 800, color: 'var(--color-navy)' }}>Operations Generated</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1.125rem', color: 'var(--color-text-main)' }}>{simResult.original_plan.total_blocks}</td>
                      <td style={{ color: '#8B5CF6' }}><ArrowRight size={20} /></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.125rem', color: '#6D28D9' }}>{simResult.modified_plan.total_blocks}</td>
                      <td style={{ paddingRight: '32px', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1rem', color: simResult.modified_plan.total_blocks > simResult.original_plan.total_blocks ? 'var(--color-success-dark)' : simResult.modified_plan.total_blocks < simResult.original_plan.total_blocks ? 'var(--color-danger-dark)' : 'var(--color-text-muted)' }}>
                        {simResult.modified_plan.total_blocks - simResult.original_plan.total_blocks > 0 ? '+' : ''}{simResult.modified_plan.total_blocks - simResult.original_plan.total_blocks}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ paddingLeft: '32px', fontWeight: 800, color: 'var(--color-navy)' }}>Tasks Schedulable</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1.125rem', color: 'var(--color-text-main)' }}>{simResult.original_plan.tasks_scheduled}</td>
                      <td style={{ color: '#8B5CF6' }}><ArrowRight size={20} /></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.125rem', color: '#6D28D9' }}>{simResult.modified_plan.tasks_scheduled}</td>
                      <td style={{ paddingRight: '32px', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1rem', color: simResult.modified_plan.tasks_scheduled > simResult.original_plan.tasks_scheduled ? 'var(--color-success-dark)' : simResult.modified_plan.tasks_scheduled < simResult.original_plan.tasks_scheduled ? 'var(--color-danger-dark)' : 'var(--color-text-muted)' }}>
                        {simResult.modified_plan.tasks_scheduled - simResult.original_plan.tasks_scheduled > 0 ? '+' : ''}{simResult.modified_plan.tasks_scheduled - simResult.original_plan.tasks_scheduled}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ paddingLeft: '32px', fontWeight: 800, color: 'var(--color-navy)' }}>Total Block Hours</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1.125rem', color: 'var(--color-text-main)' }}>{simResult.original_plan.total_block_hrs}H</td>
                      <td style={{ color: '#8B5CF6' }}><ArrowRight size={20} /></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.125rem', color: '#6D28D9' }}>{simResult.modified_plan.total_block_hrs}H</td>
                      <td style={{ paddingRight: '32px', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1rem', color: simResult.modified_plan.total_block_hrs > simResult.original_plan.total_block_hrs ? 'var(--color-success-dark)' : simResult.modified_plan.total_block_hrs < simResult.original_plan.total_block_hrs ? 'var(--color-danger-dark)' : 'var(--color-text-muted)' }}>
                        {simResult.modified_plan.total_block_hrs - simResult.original_plan.total_block_hrs > 0 ? '+' : ''}{(simResult.modified_plan.total_block_hrs - simResult.original_plan.total_block_hrs).toFixed(1)}H
                      </td>
                    </tr>
                    <tr>
                      <td style={{ paddingLeft: '32px', fontWeight: 800, color: 'var(--color-navy)' }}>Network Utilization</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '1.125rem', color: 'var(--color-text-main)' }}>{simResult.original_plan.utilization_pct}%</td>
                      <td style={{ color: '#8B5CF6' }}><ArrowRight size={20} /></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.125rem', color: '#6D28D9' }}>{simResult.modified_plan.utilization_pct}%</td>
                      <td style={{ paddingRight: '32px', fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1rem', color: simResult.modified_plan.utilization_pct > simResult.original_plan.utilization_pct ? 'var(--color-success-dark)' : simResult.modified_plan.utilization_pct < simResult.original_plan.utilization_pct ? 'var(--color-danger-dark)' : 'var(--color-text-muted)' }}>
                        {simResult.modified_plan.utilization_pct - simResult.original_plan.utilization_pct > 0 ? '+' : ''}{(simResult.modified_plan.utilization_pct - simResult.original_plan.utilization_pct).toFixed(1)}%
                      </td>
                    </tr>
                  </tbody>
                </table>
                
                <div style={{ padding: '24px 32px', backgroundColor: 'rgba(139, 92, 246, 0.05)' }}>
                  <div className="section-heading" style={{ color: '#6D28D9' }}>AI Solver Strategic Assessment</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-navy)', lineHeight: 1.6, display: 'flex', alignItems: 'flex-start', gap: '12px', fontWeight: 600 }}>
                    <Network size={20} color="#8B5CF6" style={{ marginTop: '2px' }} />
                    {simResult.explanation}
                  </div>
                </div>
              </div>

              {/* TIMELINE / BLOCKS SUMMARY */}
              <div className="card" style={{ padding: '32px' }}>
                <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Computed Scenario Blocks</h3>
                {simResult.modified_blocks.length === 0 ? (
                  <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)', fontWeight: 700, border: '2px dashed var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                    Optimizer could not generate safe operations under these constraints.
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                    {simResult.modified_blocks.map((b, idx) => (
                      <div key={idx} className="hover-lift" style={{ padding: '20px', backgroundColor: 'var(--color-bg-white)', border: '1px solid var(--color-border)', borderTop: `4px solid #8B5CF6`, borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '12px', boxShadow: 'var(--shadow-sm)' }}>
                        <div className="flex-between">
                          <span className="badge badge-neutral" style={{ fontFamily: 'var(--font-mono)', fontWeight: 800 }}>{b.line} LINE</span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{b.block_type}</span>
                        </div>
                        <div style={{ fontWeight: 800, fontSize: '1.25rem', fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>
                          {b.start_time} - {b.end_time}
                        </div>
                        <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <CheckCircle2 size={16} /> Accommodates {b.tasks_count} Tasks
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '600px', backgroundColor: 'var(--color-bg-white)', border: '2px dashed var(--color-border)' }}>
              <GitMerge size={64} style={{ color: 'var(--color-border-dark)', marginBottom: '24px' }} />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '0 0 12px 0', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>NO ACTIVE SCENARIO</h2>
              <p style={{ color: 'var(--color-text-muted)', margin: 0, textAlign: 'center', maxWidth: '350px', lineHeight: 1.6, fontWeight: 600 }}>
                Awaiting parameters. Select a base plan, inject perturbations, and trigger simulation.
              </p>
            </div>
          )}
        </div>
      </div>

    </div>
  );
};

export default WhatIf;
