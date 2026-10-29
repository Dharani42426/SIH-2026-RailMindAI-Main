import React, { useState, useEffect } from 'react';
import { 
  Map, Calendar, Clock, CheckCircle2, XCircle, 
  AlertTriangle, Filter, Search, Loader2, ArrowRight, Activity, X, ShieldAlert,
  BrainCircuit, Database, FileText
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const SECTION_MAP = {
  1: "CSMT to Kalyan (DBL)",
  2: "Kalyan to Kasara (DBL)",
  3: "Kasara to Igatpuri (Ghat)",
  4: "Karjat to Lonavala (Ghat)"
};

const BlockPlans = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [filters, setFilters] = useState({
    status: '',
    section_id: '',
  });

  const [selectedPlan, setSelectedPlan] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionStatus, setActionStatus] = useState(''); // 'APPROVING', 'REJECTING'
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [safetyReport, setSafetyReport] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  const { user } = useAuth();

  const fetchPlans = async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('limit', 50);
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.section_id) queryParams.append('section_id', filters.section_id);

      const res = await axios.get(`${BACKEND_URL}/api/optimizer/plans?${queryParams.toString()}`);
      setPlans(res.data);
    } catch (err) {
      console.error("Failed to fetch block plans", err);
      setError("Failed to synchronize with central block register.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, [filters]);

  const handleApprove = async () => {
    if (!selectedPlan) return;
    setActionLoading(true);
    setActionStatus('APPROVING');
    setSafetyReport(null);
    setSuccessMessage('');
    setErrorMessage('');
    
    try {
      const res = await axios.post(`${BACKEND_URL}/api/optimizer/plans/${selectedPlan.id}/approve?approved_by=${encodeURIComponent(user?.full_name)}`);
      
      // Success
      setSuccessMessage(`SUCCESS: ${res.data.message}`);
      setTimeout(() => setSuccessMessage(''), 3000);
      setSelectedPlan(null);
      fetchPlans();
    } catch (err) {
      if (err.response && err.response.status === 409) {
        // Backend safety validation failed
        setSafetyReport(err.response.data.safety_report || { safe: false, violations: [] });
      } else {
        setErrorMessage(`Approval Failed: ${err.response?.data?.detail || err.message}`);
        setTimeout(() => setErrorMessage(''), 5000);
      }
    } finally {
      setActionLoading(false);
      setActionStatus('');
    }
  };

  const handleReject = async () => {
    if (!selectedPlan) return;
    if (!rejectionReason.trim()) {
      setErrorMessage("A rejection reason is required.");
      setTimeout(() => setErrorMessage(''), 3000);
      return;
    }

    setActionLoading(true);
    setActionStatus('REJECTING');
    setSuccessMessage('');
    setErrorMessage('');
    try {
      const res = await axios.post(`${BACKEND_URL}/api/optimizer/plans/${selectedPlan.id}/reject?reason=${encodeURIComponent(rejectionReason)}`);
      setSuccessMessage(`SUCCESS: ${res.data.message}`);
      setTimeout(() => setSuccessMessage(''), 3000);
      setSelectedPlan(null);
      setShowRejectInput(false);
      setRejectionReason('');
      fetchPlans();
    } catch (err) {
      setErrorMessage(`Rejection Failed: ${err.response?.data?.detail || err.message}`);
      setTimeout(() => setErrorMessage(''), 5000);
    } finally {
      setActionLoading(false);
      setActionStatus('');
    }
  };

  // KPI Metrics calculation
  const totalPlans = plans.length;
  const draftPlans = plans.filter(p => p.status === 'DRAFT').length;
  const approvedPlans = plans.filter(p => p.status === 'APPROVED').length;
  const totalHours = plans.reduce((sum, p) => sum + (p.total_block_hrs || 0), 0);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">
            <Map size={32} color="var(--color-primary)" />
            BLOCK PLAN REGISTER
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <Database size={16} /> AI-generated railway maintenance block plans and operational approval status.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Link to="/planner" className="btn btn-primary hover-lift" style={{ fontWeight: 700, display: 'flex', gap: '8px', boxShadow: '0 4px 14px rgba(29, 78, 216, 0.4)' }}>
            <BrainCircuit size={18} />
            CREATE / OPTIMIZE PLAN
          </Link>
        </div>
      </div>

      {error && (
        <div style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600, borderRadius: 'var(--radius-md)' }}>
          <AlertTriangle size={24} /> {error}
        </div>
      )}

      {/* KPI Section */}
      <div className="grid-cols-4 animate-slide-up">
        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Total Plans</div>
            <FileText size={20} color="var(--color-primary)" />
          </div>
          <div className="kpi-value">{loading ? <Loader2 size={24} className="animate-spin" /> : totalPlans}</div>
        </div>

        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-warning)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-warning-dark)' }}>Draft Pending</div>
            <Clock size={20} color="var(--color-warning)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-warning-dark)' }}>{loading ? <Loader2 size={24} className="animate-spin" /> : draftPlans}</div>
        </div>

        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-success)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-success-dark)' }}>Approved</div>
            <CheckCircle2 size={20} color="var(--color-success)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-success-dark)' }}>{loading ? <Loader2 size={24} className="animate-spin" /> : approvedPlans}</div>
        </div>

        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-navy)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Total Block Hrs</div>
            <Clock size={20} color="var(--color-navy)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-navy)' }}>{loading ? <Loader2 size={24} className="animate-spin" /> : totalHours.toFixed(1)}<span style={{ fontSize: '1rem', marginLeft: '4px' }}>h</span></div>
        </div>
      </div>

      {/* Control Panel / Filter Bar */}
      <div className="panel animate-slide-up" style={{ padding: '16px 24px', display: 'flex', flexDirection: 'row', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontWeight: 800, letterSpacing: '0.05em' }}>
          <Filter size={20} color="var(--color-primary)" /> FILTERS
        </div>
        
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border-dark)' }}></div>

        <select className="input-rail" style={{ width: 'auto', fontWeight: 600 }} value={filters.status} onChange={(e) => setFilters(prev => ({...prev, status: e.target.value}))}>
          <option value="">ALL STATUSES</option>
          <option value="DRAFT">DRAFT</option>
          <option value="APPROVED">APPROVED</option>
          <option value="REJECTED">REJECTED</option>
          <option value="COMPLETED">COMPLETED</option>
        </select>

        <select className="input-rail" style={{ width: 'auto', fontWeight: 600 }} value={filters.section_id} onChange={(e) => setFilters(prev => ({...prev, section_id: e.target.value}))}>
          <option value="">ALL SECTIONS</option>
          <option value="1">1 (CSMT-KYN)</option>
          <option value="2">2 (KYN-KAS)</option>
        </select>

        <button className="btn btn-outline" style={{ marginLeft: 'auto', fontWeight: 700 }} onClick={() => setFilters({ status: '', section_id: '' })}>
          RESET
        </button>
      </div>

      {/* Plan Table */}
      <div className="panel animate-slide-up" style={{ padding: 0, overflow: 'hidden' }}>
        {loading && plans.length === 0 ? (
          <div className="flex-center" style={{ padding: '60px', color: 'var(--color-primary)' }}><Loader2 className="animate-spin" size={48} /></div>
        ) : plans.length === 0 ? (
          <div className="empty-state" style={{ padding: '60px' }}>
            <Map size={48} />
            <h3>BLOCK PLAN REGISTER EMPTY</h3>
            <p>No generated maintenance plans are currently available.</p>
            <Link to="/planner" className="btn btn-primary" style={{ marginTop: '16px' }}>OPEN AI PLANNER</Link>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="rail-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '32px' }}>Plan Code</th>
                  <th>Section ID</th>
                  <th>Plan Type</th>
                  <th>Date Range</th>
                  <th>Blocks</th>
                  <th>Tasks</th>
                  <th>Duration</th>
                  <th>Utilization</th>
                  <th style={{ paddingRight: '32px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {plans.map(plan => (
                  <tr key={plan.id} onClick={() => { setSelectedPlan(plan); setSafetyReport(null); setShowRejectInput(false); setRejectionReason(''); }} style={{ cursor: 'pointer' }}>
                    <td style={{ paddingLeft: '32px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{plan.plan_code}</td>
                    <td style={{ fontWeight: 800, color: 'var(--color-text-main)' }}>{plan.section_id}</td>
                    <td style={{ fontWeight: 600 }}>{plan.plan_type}</td>
                    <td style={{ fontWeight: 600, color: 'var(--color-navy)' }}>{plan.date_range}</td>
                    <td style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{plan.total_blocks}</td>
                    <td style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{plan.tasks_scheduled}</td>
                    <td style={{ fontWeight: 700, color: 'var(--color-warning-dark)' }}>{plan.total_block_hrs}h</td>
                    <td style={{ fontWeight: 700, color: 'var(--color-success-dark)' }}>{plan.utilization_pct}%</td>
                    <td style={{ paddingRight: '32px' }}>
                      <span className={`badge ${plan.status === 'APPROVED' || plan.status === 'COMPLETED' ? 'badge-success' : plan.status === 'REJECTED' ? 'badge-danger' : 'badge-neutral'}`}>
                        {plan.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Plan Detail Drawer */}
      {selectedPlan && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', justifyContent: 'flex-end' }}>
          <div className="animate-fade-in" style={{ width: '500px', backgroundColor: 'var(--color-bg-main)', borderLeft: '1px solid var(--color-border)', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto', boxShadow: 'var(--shadow-lg)' }}>
            
            <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, backgroundColor: 'var(--color-bg-white)', zIndex: 10, boxShadow: 'var(--shadow-sm)' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-navy)' }}>
                <Map color="var(--color-primary)" /> {selectedPlan.plan_code}
              </h2>
              <button onClick={() => setSelectedPlan(null)} className="hover-lift" style={{ padding: '8px', backgroundColor: 'var(--color-bg-subtle)', borderRadius: '50%' }}>
                <X size={20} />
              </button>
            </div>
            
            <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
              
              {/* Status & Identity */}
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
                <span className={`badge ${selectedPlan.status === 'APPROVED' || selectedPlan.status === 'COMPLETED' ? 'badge-success' : selectedPlan.status === 'REJECTED' ? 'badge-danger' : 'badge-neutral'}`} style={{ fontSize: '1rem', padding: '8px 16px' }}>
                  {selectedPlan.status}
                </span>
                <span className="badge badge-primary">{selectedPlan.plan_type} PLAN</span>
              </div>

              {/* Notifications */}
              {successMessage && (
                <div style={{ padding: '16px', backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success-dark)', borderRadius: '6px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <CheckCircle2 size={20} /> {successMessage}
                </div>
              )}
              {errorMessage && (
                <div style={{ padding: '12px', backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger-dark)', borderRadius: '4px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} /> {errorMessage}
                </div>
              )}

              {/* Approval Safety Gate */}
              {selectedPlan.status === 'DRAFT' && (
                <div className="card" style={{ 
                  borderColor: safetyReport ? 'var(--color-danger-dark)' : 'var(--color-primary)', 
                  backgroundColor: safetyReport ? 'var(--color-danger-bg)' : 'var(--color-primary-light)',
                  borderWidth: '2px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' 
                }}>
                  {safetyReport ? (
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-danger-dark)', fontWeight: 800, fontSize: '1.25rem' }}>
                        <ShieldAlert size={24} /> APPROVAL BLOCKED: SAFETY VALIDATION FAILED
                      </div>
                      <div style={{ backgroundColor: 'white', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-danger)' }}>
                        {safetyReport.violations && safetyReport.violations.map((v, i) => (
                          <div key={i} style={{ display: 'flex', gap: '12px', marginBottom: i !== safetyReport.violations.length - 1 ? '12px' : 0, color: 'var(--color-danger-dark)' }}>
                            <XCircle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />
                            <div style={{ fontSize: '0.875rem' }}>
                              <span style={{ fontWeight: 800, display: 'block', marginBottom: '4px' }}>{v.type} ({v.date})</span>
                              {v.description}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--color-danger-dark)', fontWeight: 600 }}>
                        This plan conflicts with active timetables. It must be regenerated.
                      </div>
                    </>
                  ) : (
                    <>
                      {['CONTROLLER', 'ADMIN'].includes(user?.role) ? (
                        <>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-navy)', fontWeight: 800, fontSize: '1.125rem' }}>
                            <ShieldAlert size={20} color="var(--color-primary)" /> CONTROLLER REVIEW
                          </div>
                          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-main)', fontWeight: 600 }}>
                            Clicking approve will trigger a fresh CP-SAT safety validation against live train timetables.
                          </div>
                          
                          {actionLoading ? (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px', backgroundColor: 'var(--color-primary)', color: 'white', borderRadius: 'var(--radius-sm)', fontWeight: 700, gap: '12px' }}>
                              <Loader2 size={20} className="animate-spin" /> REVALIDATING SAFETY...
                            </div>
                          ) : (
                            <div style={{ display: 'flex', gap: '12px' }}>
                              <button className="btn btn-primary" style={{ flex: 1, justifyContent: 'center', fontWeight: 800 }} onClick={handleApprove}>
                                APPROVE & PUBLISH
                              </button>
                              <button className="btn btn-outline" style={{ flex: 1, justifyContent: 'center', borderColor: 'var(--color-danger)', color: 'var(--color-danger)', fontWeight: 800 }} onClick={() => setShowRejectInput(!showRejectInput)}>
                                REJECT PLAN
                              </button>
                            </div>
                          )}
                          
                          {showRejectInput && !actionLoading && (
                            <div className="animate-slide-up" style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px', padding: '16px', backgroundColor: 'white', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-navy)', textTransform: 'uppercase' }}>Rejection Reason</label>
                              <input type="text" className="input-rail" placeholder="Enter reason for rejection..." value={rejectionReason} onChange={(e) => setRejectionReason(e.target.value)} />
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '0.75rem' }} onClick={() => setShowRejectInput(false)}>CANCEL</button>
                                <button className="btn" style={{ padding: '6px 12px', fontSize: '0.75rem', backgroundColor: 'var(--color-danger)', color: 'white' }} onClick={handleReject}>CONFIRM REJECT</button>
                              </div>
                            </div>
                          )}
                        </>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-warning-dark)', fontWeight: 800, fontSize: '1.125rem' }}>
                            <Clock size={20} color="var(--color-warning)" /> AWAITING CONTROLLER APPROVAL
                          </div>
                          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-main)', fontWeight: 600 }}>
                            This draft plan is currently under review by Operations Control.
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Historical Safety Report */}
              {selectedPlan.status !== 'DRAFT' && (
                <div className="card" style={{ padding: '20px', backgroundColor: selectedPlan.status === 'REJECTED' || (selectedPlan.safety_report_data && !selectedPlan.safety_report_data.safe) ? 'var(--color-danger-bg)' : selectedPlan.status === 'APPROVED' || selectedPlan.status === 'COMPLETED' ? 'var(--color-success-bg)' : 'var(--color-bg-subtle)' }}>
                  <div className="section-heading" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: selectedPlan.status === 'REJECTED' || (selectedPlan.safety_report_data && !selectedPlan.safety_report_data.safe) ? 'var(--color-danger-dark)' : selectedPlan.status === 'APPROVED' || selectedPlan.status === 'COMPLETED' ? 'var(--color-success-dark)' : 'var(--color-navy)' }}>
                    {selectedPlan.status === 'REJECTED' || (selectedPlan.safety_report_data && !selectedPlan.safety_report_data.safe) ? (
                      <><XCircle size={24} /> SAFETY STATUS: FAILED / REJECTED</>
                    ) : selectedPlan.status === 'APPROVED' || selectedPlan.status === 'COMPLETED' ? (
                      <><CheckCircle2 size={24} /> SAFETY STATUS: VERIFIED & PASSED</>
                    ) : (
                      'SAFETY STATUS: NOT VERIFIED'
                    )}
                  </div>
                  
                  {selectedPlan.status === 'REJECTED' && selectedPlan.rejection_reason && (
                    <div style={{ marginTop: '12px', padding: '12px', backgroundColor: 'rgba(255,255,255,0.6)', borderRadius: '4px', borderLeft: '3px solid var(--color-danger)' }}>
                      <strong style={{ color: 'var(--color-danger-dark)', fontSize: '0.875rem', display: 'block', marginBottom: '4px' }}>Rejection Reason:</strong>
                      <span style={{ fontSize: '0.875rem', color: 'var(--color-danger-dark)', fontWeight: 600 }}>{selectedPlan.rejection_reason}</span>
                    </div>
                  )}

                  {selectedPlan.safety_report_data && selectedPlan.safety_report_data.safe && (
                    <div style={{ marginTop: '16px' }}>
                      <div style={{ fontSize: '0.875rem', color: 'var(--color-success-dark)', fontWeight: 700, marginBottom: '8px' }}>
                        This plan successfully passed {selectedPlan.safety_report_data.checks_passed} daily safety checks covering the following CP-SAT constraints:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.875rem', color: 'var(--color-success-dark)', fontWeight: 600, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <li><strong>TRAIN_CLASH:</strong> No overlaps with live train schedules.</li>
                        <li><strong>ADJACENT:</strong> Minimum 30-min gap maintained between corridor blocks.</li>
                        <li><strong>DEPT_OVERLAP:</strong> No unsafe multi-department physical collisions.</li>
                        <li><strong>PRIORITY:</strong> Complete precedence given to Express/Superfast routing.</li>
                      </ul>
                    </div>
                  )}
                  
                  {selectedPlan.safety_report_data && !selectedPlan.safety_report_data.safe && selectedPlan.safety_report_data.violations && (
                    <div style={{ marginTop: '16px' }}>
                      <div style={{ fontSize: '0.875rem', color: 'var(--color-danger-dark)', fontWeight: 700, marginBottom: '8px' }}>
                        Safety Validation Violations:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {selectedPlan.safety_report_data.violations.map((v, i) => (
                          <div key={i} style={{ padding: '8px', backgroundColor: 'rgba(255,255,255,0.7)', borderRadius: '4px', fontSize: '0.875rem', color: 'var(--color-danger-dark)', border: '1px solid rgba(220, 38, 38, 0.2)' }}>
                            <strong style={{ display: 'block' }}>{v.type} ({v.date})</strong>
                            <span>{v.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Plan Data */}
              <div>
                <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Operational Metrics</h3>
                <div className="card" style={{ padding: 0 }}>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Section</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{selectedPlan.section_id} ({SECTION_MAP[selectedPlan.section_id] || 'Unknown'})</span>
                  </div>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Date Range</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{selectedPlan.date_range}</span>
                  </div>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Generated At</span>
                    <span style={{ fontWeight: 600, color: 'var(--color-navy)', fontSize: '0.875rem' }}>{new Date(selectedPlan.generated_at).toLocaleString()}</span>
                  </div>
                  <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', backgroundColor: 'var(--color-bg-subtle)' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Tasks Scheduled</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-primary)', fontSize: '1.25rem' }}>{selectedPlan.tasks_scheduled}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Block Allocations</h3>
                <div className="card" style={{ padding: 0 }}>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Total Blocks</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{selectedPlan.total_blocks} Windows</span>
                  </div>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Total Duration</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{selectedPlan.total_block_hrs} Hours</span>
                  </div>
                  <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Window Utilization</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-success-dark)' }}>{selectedPlan.utilization_pct}%</span>
                  </div>
                </div>
              </div>

              {/* AI Insights */}
              <div>
                <h3 className="section-heading" style={{ color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BrainCircuit size={18} /> AI Optimization Insights
                </h3>
                <div className="card" style={{ padding: 0 }}>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Generated By</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-navy)' }}>{selectedPlan.generated_by || 'AI'}</span>
                  </div>
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Optimization Score</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-primary)' }}>{selectedPlan.optimization_score !== null ? selectedPlan.optimization_score : 'N/A'}</span>
                  </div>
                  <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Conflicts Resolved (AI)</span>
                    <span style={{ fontWeight: 800, color: 'var(--color-success-dark)' }}>{selectedPlan.conflicts_resolved || 0}</span>
                  </div>
                </div>
              </div>

              {/* Detailed Block Schedule */}
              {selectedPlan.block_windows && selectedPlan.block_windows.length > 0 && (
                <div>
                  <h3 className="section-heading" style={{ color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Calendar size={18} /> Detailed Block Schedule
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {selectedPlan.block_windows.map((block, idx) => (
                      <div key={idx} className="card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', borderLeft: `4px solid ${block.is_integrated ? 'var(--color-success)' : 'var(--color-primary)'}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 800, color: 'var(--color-navy)', fontFamily: 'var(--font-mono)' }}>{block.block_code}</span>
                          <span className={`badge ${block.is_integrated ? 'badge-success' : 'badge-primary'}`} style={{ fontSize: '0.75rem' }}>
                            {block.block_type}
                          </span>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '0.875rem', color: 'var(--color-text-main)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Calendar size={14} color="var(--color-text-muted)" />
                            <strong>{block.block_date}</strong>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Clock size={14} color="var(--color-text-muted)" />
                            <strong>{block.start_time.substring(0,5)} - {block.end_time.substring(0,5)}</strong> ({block.duration_hrs}h)
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Map size={14} color="var(--color-text-muted)" />
                            Line: <strong>{block.line_blocked}</strong> (KM {block.km_from} - {block.km_to})
                          </div>
                        </div>

                        {block.departments && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                            DEPARTMENTS: {block.departments.split(',').join(' • ')}
                          </div>
                        )}

                        {block.ai_explanation && (
                          <div style={{ padding: '12px', backgroundColor: 'var(--color-bg-subtle)', borderRadius: '4px', fontSize: '0.875rem', color: 'var(--color-navy)', border: '1px solid var(--color-border)', display: 'flex', gap: '8px' }}>
                            <BrainCircuit size={16} color="var(--color-primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
                            <span>{block.ai_explanation}</span>
                          </div>
                        )}

                        {block.task_assignments && block.task_assignments.length > 0 && (
                          <div style={{ marginTop: '8px', borderTop: '1px dashed var(--color-border)', paddingTop: '12px' }}>
                            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', textTransform: 'uppercase', marginBottom: '8px' }}>
                              Tasks Scheduled in this Block ({block.task_assignments.length}):
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                              {block.task_assignments.map((assignment, aIdx) => (
                                <div key={aIdx} style={{ display: 'flex', gap: '12px', alignItems: 'center', backgroundColor: 'var(--color-bg-white)', padding: '10px 12px', borderRadius: '4px', border: '1px solid var(--color-border)' }}>
                                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: '24px', height: '24px', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', borderRadius: '50%', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                                    {assignment.sequence_order}
                                  </div>
                                  <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 700, color: 'var(--color-navy)', fontSize: '0.875rem' }}>
                                      {assignment.task.work_type}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '2px' }}>
                                      <span><strong>ID:</strong> {assignment.task.task_code}</span>
                                      <span>&bull;</span>
                                      <span><strong>Dept:</strong> {assignment.task.department}</span>
                                      <span>&bull;</span>
                                      <span><strong>KM:</strong> {assignment.task.km_from} - {assignment.task.km_to}</span>
                                    </div>
                                  </div>
                                  <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0 }}>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-text-main)', backgroundColor: 'var(--color-bg-subtle)', padding: '2px 6px', borderRadius: '4px' }}>
                                      {assignment.duration_min} min
                                    </span>
                                    <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                                      Starts @ +{assignment.start_offset_min}m
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
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

export default BlockPlans;
