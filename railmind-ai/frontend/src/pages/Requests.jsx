import React, { useState, useEffect } from 'react';
import { 
  ClipboardList, Plus, Inbox, FileText, CheckCircle2, 
  XCircle, Clock, Search, AlertCircle, Loader2, ArrowRight
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Requests = () => {
  const { user } = useAuth();
  
  const isController = user?.can_approve_plans;
  
  const [requests, setRequests] = useState([]);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Modals / Drawers state
  const [isNewRequestModalOpen, setIsNewRequestModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  
  // Form State
  const [formData, setFormData] = useState({
    section_id: '',
    work_type: '',
    description: '',
    justification: '',
    km_from: '',
    km_to: '',
    estimated_hours: '',
    block_type_required: 'TRAFFIC',
    preferred_date: ''
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(null);

  // Review State
  const [reviewAction, setReviewAction] = useState(null); // 'ACCEPT' or 'REJECT'
  const [rejectionReason, setRejectionReason] = useState('');
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState(null);
  const [reviewSuccess, setReviewSuccess] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [reqRes, secRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/requests/`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('railmind_token')}` }
        }),
        axios.get(`${BACKEND_URL}/api/sections/`) // public or requires auth depending on setup, usually public in this app
      ]);
      // Filter out requests that have already been scheduled into a block plan
      const activeRequests = reqRes.data.filter(r => r.status !== 'SCHEDULED' && r.status !== 'COMPLETED');
      setRequests(activeRequests);
      setSections(secRes.data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch maintenance requests. Backend may be unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleNewRequestSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    setFormSuccess(null);
    try {
      const payload = {
        department: user.department,
        section_id: parseInt(formData.section_id),
        work_type: formData.work_type,
        description: formData.description,
        justification: formData.justification,
        km_from: parseFloat(formData.km_from),
        km_to: parseFloat(formData.km_to),
        estimated_hours: parseFloat(formData.estimated_hours),
        block_type_required: formData.block_type_required,
        preferred_date: formData.preferred_date
      };
      
      await axios.post(`${BACKEND_URL}/api/requests/`, payload, {
        headers: { Authorization: `Bearer ${localStorage.getItem('railmind_token')}` }
      });
      
      setFormSuccess("Maintenance request submitted successfully.");
      setTimeout(() => {
        setIsNewRequestModalOpen(false);
        setFormData({
          section_id: '', work_type: '', description: '', justification: '',
          km_from: '', km_to: '', estimated_hours: '', block_type_required: 'TRAFFIC', preferred_date: ''
        });
        setFormSuccess(null);
        fetchData();
      }, 1500);
    } catch (err) {
      setFormError(err.response?.data?.detail || "Failed to submit request.");
    } finally {
      setFormLoading(false);
    }
  };

  const handleReviewSubmit = async (actionOverride = null) => {
    const action = actionOverride || reviewAction;
    if (action === 'REJECT' && !rejectionReason.trim()) {
      setReviewError("Rejection reason is required.");
      return;
    }
    
    setReviewLoading(true);
    setReviewError(null);
    setReviewSuccess(null);
    try {
      const payload = {
        action: action,
        rejection_reason: action === 'REJECT' ? rejectionReason : null
      };
      
      await axios.post(`${BACKEND_URL}/api/requests/${selectedRequest.id}/review`, payload, {
        headers: { Authorization: `Bearer ${localStorage.getItem('railmind_token')}` }
      });
      
      setReviewSuccess(action === 'ACCEPT' 
        ? "MAINTENANCE TASK CREATED — READY FOR AI PLANNING" 
        : "REQUEST REJECTED");
        
      setTimeout(() => {
        setIsDrawerOpen(false);
        setSelectedRequest(null);
        setReviewAction(null);
        setRejectionReason('');
        setReviewSuccess(null);
        fetchData();
      }, 2000);
    } catch (err) {
      setReviewError(err.response?.data?.detail || "Failed to process review.");
    } finally {
      setReviewLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'DRAFT': return <span style={{ color: 'var(--color-text-muted)', backgroundColor: 'var(--color-bg-subtle)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>DRAFT</span>;
      case 'SUBMITTED': return <span style={{ color: 'var(--color-info-dark)', backgroundColor: 'var(--color-info-bg)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>SUBMITTED</span>;
      case 'UNDER_REVIEW': return <span style={{ color: 'var(--color-warning-dark)', backgroundColor: 'var(--color-warning-bg)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>UNDER REVIEW</span>;
      case 'ACCEPTED': return <span style={{ color: 'var(--color-success-dark)', backgroundColor: 'var(--color-success-bg)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>ACCEPTED</span>;
      case 'REJECTED': return <span style={{ color: 'var(--color-danger-dark)', backgroundColor: 'var(--color-danger-bg)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>REJECTED</span>;
      default: return <span>{status}</span>;
    }
  };

  const openRequestDrawer = (req) => {
    setSelectedRequest(req);
    setIsDrawerOpen(true);
    setReviewAction(null);
    setRejectionReason('');
    setReviewError(null);
    setReviewSuccess(null);
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px', position: 'relative' }}>
      
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">
            {isController ? <Inbox size={32} color="var(--color-primary)" /> : <FileText size={32} color="var(--color-primary)" />}
            {isController ? 'MAINTENANCE REQUEST INBOX' : 'MY MAINTENANCE REQUESTS'}
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <ClipboardList size={16} /> Departmental Planning Requests
          </p>
        </div>
        {!isController && (
          <button 
            onClick={() => setIsNewRequestModalOpen(true)}
            style={{ 
              backgroundColor: 'var(--color-primary)', color: 'white', padding: '10px 20px', 
              borderRadius: '6px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px'
            }}
            className="hover-lift"
          >
            <Plus size={18} />
            NEW REQUEST
          </button>
        )}
      </div>

      {error && (
        <div style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600, borderRadius: 'var(--radius-md)' }}>
          <AlertCircle size={24} /> {error}
        </div>
      )}

      {/* KPI Section */}
      <div className="grid-cols-4 animate-slide-up">
        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Total Requests</div>
          <div className="kpi-value">{requests.length}</div>
        </div>
        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-info)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-info-dark)' }}>Submitted</div>
          <div className="kpi-value" style={{ color: 'var(--color-info-dark)' }}>
            {requests.filter(r => r.status === 'SUBMITTED').length}
          </div>
        </div>
        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-success)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-success-dark)' }}>Accepted</div>
          <div className="kpi-value" style={{ color: 'var(--color-success-dark)' }}>
            {requests.filter(r => r.status === 'ACCEPTED').length}
          </div>
        </div>
        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-danger)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-danger-dark)' }}>Rejected</div>
          <div className="kpi-value" style={{ color: 'var(--color-danger-dark)' }}>
            {requests.filter(r => r.status === 'REJECTED').length}
          </div>
        </div>
      </div>

      {/* TABLE */}
      <div className="panel animate-slide-up">
        <div className="panel-header">
          <FileText size={18} />
          {isController ? 'REQUEST INBOX' : 'REQUEST LOG'}
        </div>
        {loading ? (
          <div style={{ padding: '60px', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'var(--color-text-muted)' }}>
            <Loader2 className="animate-spin" size={32} />
          </div>
        ) : requests.length === 0 ? (
          <div style={{ padding: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', color: 'var(--color-text-muted)', gap: '16px' }}>
            <Inbox size={48} style={{ opacity: 0.3 }} />
            <p style={{ fontWeight: 600, fontSize: '1.1rem' }}>
              {isController ? 'REQUEST INBOX CLEAR' : 'NO MAINTENANCE REQUESTS'}
            </p>
            <p style={{ fontSize: '0.9rem' }}>
              {isController ? 'No maintenance requests currently require review.' : 'Your department has no active requests.'}
            </p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--color-bg-subtle)', borderBottom: '1px solid var(--color-border)', fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <th style={{ padding: '16px 20px', fontWeight: 700 }}>Request Code</th>
                <th style={{ padding: '16px 20px', fontWeight: 700 }}>Work Type</th>
                {isController && <th style={{ padding: '16px 20px', fontWeight: 700 }}>Department</th>}
                <th style={{ padding: '16px 20px', fontWeight: 700 }}>Section</th>
                <th style={{ padding: '16px 20px', fontWeight: 700 }}>Preferred Date</th>
                <th style={{ padding: '16px 20px', fontWeight: 700 }}>Hours</th>
                <th style={{ padding: '16px 20px', fontWeight: 700 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {requests.map(req => {
                const sec = sections.find(s => s.id === req.section_id);
                return (
                  <tr 
                    key={req.id} 
                    style={{ borderBottom: '1px solid var(--color-border)', transition: 'background-color 0.2s', cursor: 'pointer' }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--color-bg-subtle)'}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                    onClick={() => openRequestDrawer(req)}
                  >
                    <td style={{ padding: '16px 20px', fontWeight: 600, color: 'var(--color-primary)' }}>{req.request_code}</td>
                    <td style={{ padding: '16px 20px', fontWeight: 500 }}>{req.work_type}</td>
                    {isController && <td style={{ padding: '16px 20px', fontWeight: 600 }}>{req.department}</td>}
                    <td style={{ padding: '16px 20px' }}>{sec ? sec.section_code : `Sec ${req.section_id}`}</td>
                    <td style={{ padding: '16px 20px' }}>{new Date(req.preferred_date).toLocaleDateString()}</td>
                    <td style={{ padding: '16px 20px' }}>{req.estimated_hours}h</td>
                    <td style={{ padding: '16px 20px' }}>{getStatusBadge(req.status)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* NEW REQUEST MODAL */}
      {isNewRequestModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(11, 17, 32, 0.7)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card animate-scale-in" style={{ width: '100%', maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)', margin: 0 }}>NEW MAINTENANCE REQUEST</h2>
              <button onClick={() => setIsNewRequestModalOpen(false)} style={{ color: 'var(--color-text-muted)' }}><XCircle size={24} /></button>
            </div>
            
            {formSuccess && (
              <div style={{ padding: '12px', backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success-dark)', borderRadius: '4px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={18} /> {formSuccess}
              </div>
            )}
            
            {formError && (
              <div style={{ padding: '12px', backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger-dark)', borderRadius: '4px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={18} /> {formError}
              </div>
            )}

            <form onSubmit={handleNewRequestSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Railway Section *</label>
                <select name="section_id" value={formData.section_id} onChange={handleInputChange} required style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }}>
                  <option value="">Select Section</option>
                  {sections.map(s => (
                    <option key={s.id} value={s.id}>{s.section_code} - {s.section_name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Work Type *</label>
                <input type="text" name="work_type" value={formData.work_type} onChange={handleInputChange} required placeholder="e.g. Rail Fracture Repair" style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }} />
              </div>

              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>KM From *</label>
                  <input type="number" step="0.1" name="km_from" value={formData.km_from} onChange={handleInputChange} required style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>KM To *</label>
                  <input type="number" step="0.1" name="km_to" value={formData.km_to} onChange={handleInputChange} required style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Estimated Hours *</label>
                  <input type="number" step="0.5" name="estimated_hours" value={formData.estimated_hours} onChange={handleInputChange} required style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Preferred Date *</label>
                  <input type="date" name="preferred_date" value={formData.preferred_date} onChange={handleInputChange} required style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }} />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Block Type Required *</label>
                <select name="block_type_required" value={formData.block_type_required} onChange={handleInputChange} required style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none' }}>
                  <option value="TRAFFIC">TRAFFIC</option>
                  <option value="POWER">POWER</option>
                  <option value="INTEGRATED">INTEGRATED</option>
                  <option value="EMERGENCY">EMERGENCY</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Description</label>
                <textarea name="description" value={formData.description} onChange={handleInputChange} rows="3" style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none', resize: 'vertical' }}></textarea>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-main)', marginBottom: '4px' }}>Justification</label>
                <textarea name="justification" value={formData.justification} onChange={handleInputChange} rows="2" style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--color-border)', outline: 'none', resize: 'vertical' }}></textarea>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '16px' }}>
                <button type="button" onClick={() => setIsNewRequestModalOpen(false)} style={{ padding: '10px 20px', borderRadius: '4px', fontWeight: 600, border: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-main)' }}>Cancel</button>
                <button type="submit" disabled={formLoading} style={{ padding: '10px 20px', borderRadius: '4px', fontWeight: 600, backgroundColor: 'var(--color-primary)', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {formLoading && <Loader2 size={16} className="animate-spin" />}
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DRAWER FOR DETAILS / REVIEW */}
      {isDrawerOpen && selectedRequest && (
        <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: '500px', backgroundColor: 'var(--color-bg-white)', zIndex: 100, boxShadow: '-4px 0 24px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', animation: 'slideInRight 0.3s forwards' }}>
          {/* Drawer Header */}
          <div style={{ padding: '24px', borderBottom: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', letterSpacing: '0.05em', marginBottom: '4px' }}>REQUEST DETAILS</div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)', margin: 0 }}>{selectedRequest.request_code}</h2>
              <div style={{ marginTop: '8px' }}>{getStatusBadge(selectedRequest.status)}</div>
            </div>
            <button onClick={() => setIsDrawerOpen(false)} style={{ color: 'var(--color-text-muted)' }}><XCircle size={24} /></button>
          </div>
          
          {/* Drawer Content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {reviewSuccess && (
              <div style={{ padding: '16px', backgroundColor: reviewSuccess.includes('REJECTED') ? 'var(--color-danger-bg)' : 'var(--color-success-bg)', color: reviewSuccess.includes('REJECTED') ? 'var(--color-danger-dark)' : 'var(--color-success-dark)', borderRadius: '6px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '12px' }}>
                <CheckCircle2 size={20} /> {reviewSuccess}
              </div>
            )}
            
            {reviewError && (
              <div style={{ padding: '12px', backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger-dark)', borderRadius: '4px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={18} /> {reviewError}
              </div>
            )}

            {/* If Accepted, show link to AI Planner */}
            {selectedRequest.status === 'ACCEPTED' && (
              <div style={{ padding: '16px', backgroundColor: 'var(--color-primary-light)', border: '1px solid var(--color-primary)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ fontWeight: 800, color: 'var(--color-primary)' }}>REQUEST ACCEPTED FOR PLANNING</div>
                
                {selectedRequest.maintenance_task_id ? (
                  <>
                    <div style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', fontWeight: 500, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ fontWeight: 700 }}>MAINTENANCE TASK CREATED</div>
                      <div>TASK ID: {selectedRequest.maintenance_task_id}</div>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '4px' }}>
                      <Link to={`/tasks?taskId=${selectedRequest.maintenance_task_id}&requestId=${selectedRequest.id}&requestCode=${selectedRequest.request_code}`} style={{ padding: '8px 16px', backgroundColor: 'white', color: 'var(--color-primary)', border: '1px solid var(--color-primary)', borderRadius: '4px', fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        OPEN MAINTENANCE TASK <ArrowRight size={16} />
                      </Link>
                      <Link to={`/planner?taskId=${selectedRequest.maintenance_task_id}&requestId=${selectedRequest.id}&requestCode=${selectedRequest.request_code}`} style={{ padding: '8px 16px', backgroundColor: 'var(--color-primary)', color: 'white', borderRadius: '4px', fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        OPEN AI PLANNER <ArrowRight size={16} />
                      </Link>
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', fontWeight: 500 }}>
                    TASK CREATED
                  </div>
                )}
              </div>
            )}

            {!isController && selectedRequest.status === 'ACCEPTED' && (
              <div style={{ padding: '16px', backgroundColor: 'var(--color-bg-main)', border: '1px dashed var(--color-border)', borderRadius: '6px' }}>
                <div style={{ fontWeight: 700, color: 'var(--color-text-main)', marginBottom: '8px' }}>APPROVED MAINTENANCE WORK</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertCircle size={16} /> APPROVED WORK DETAILS NOT AVAILABLE FROM CURRENT API
                </div>
              </div>
            )}

            {selectedRequest.status === 'REJECTED' && selectedRequest.rejection_reason && (
              <div style={{ padding: '16px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(220,38,38,0.2)', borderRadius: '6px' }}>
                <div style={{ fontWeight: 700, color: 'var(--color-danger-dark)', marginBottom: '8px' }}>REJECTION REASON</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--color-text-main)' }}>{selectedRequest.rejection_reason}</div>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Department</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{selectedRequest.department}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Work Type</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{selectedRequest.work_type}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Section</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>
                  {sections.find(s => s.id === selectedRequest.section_id)?.section_code || selectedRequest.section_id}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>KM Range</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{selectedRequest.km_from} - {selectedRequest.km_to}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Block Type</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{selectedRequest.block_type_required}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Est. Hours</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{selectedRequest.estimated_hours}h</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Preferred Date</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{new Date(selectedRequest.preferred_date).toLocaleDateString()}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>Created At</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-main)' }}>{new Date(selectedRequest.created_at).toLocaleString()}</div>
              </div>
            </div>

            {selectedRequest.description && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>Description</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', backgroundColor: 'var(--color-bg-main)', padding: '12px', borderRadius: '4px' }}>
                  {selectedRequest.description}
                </div>
              </div>
            )}

            {selectedRequest.justification && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>Justification</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--color-text-main)', backgroundColor: 'var(--color-bg-main)', padding: '12px', borderRadius: '4px' }}>
                  {selectedRequest.justification}
                </div>
              </div>
            )}
          </div>

          {/* Drawer Footer - Review Controls for Controller */}
          {isController && (selectedRequest.status === 'SUBMITTED' || selectedRequest.status === 'UNDER_REVIEW') && (
            <div style={{ padding: '24px', borderTop: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-subtle)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--color-navy)', letterSpacing: '0.05em' }}>CONTROLLER REVIEW</div>
              
              {reviewAction === 'REJECT' && (
                <div>
                  <textarea 
                    value={rejectionReason} 
                    onChange={e => setRejectionReason(e.target.value)} 
                    placeholder="Provide reason for rejection..." 
                    style={{ width: '100%', padding: '12px', borderRadius: '4px', border: '1px solid var(--color-danger)', outline: 'none', resize: 'vertical' }}
                    rows="3"
                  ></textarea>
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px' }}>
                {reviewAction !== 'REJECT' ? (
                  <button 
                    onClick={() => setReviewAction('REJECT')}
                    style={{ flex: 1, padding: '12px', borderRadius: '4px', fontWeight: 700, border: '1px solid var(--color-danger)', color: 'var(--color-danger-dark)', backgroundColor: 'white' }}
                  >
                    REJECT
                  </button>
                ) : (
                  <button 
                    onClick={() => setReviewAction(null)}
                    style={{ flex: 1, padding: '12px', borderRadius: '4px', fontWeight: 700, border: '1px solid var(--color-border)', color: 'var(--color-text-muted)', backgroundColor: 'white' }}
                  >
                    CANCEL REJECT
                  </button>
                )}
                
                <button 
                  onClick={() => reviewAction === 'REJECT' ? handleReviewSubmit('REJECT') : handleReviewSubmit('ACCEPT')}
                  disabled={reviewLoading}
                  style={{ flex: reviewAction === 'REJECT' ? 1 : 2, padding: '12px', borderRadius: '4px', fontWeight: 700, backgroundColor: reviewAction === 'REJECT' ? 'var(--color-danger)' : 'var(--color-success)', color: 'white', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
                >
                  {reviewLoading && <Loader2 size={16} className="animate-spin" />}
                  {reviewAction === 'REJECT' ? 'CONFIRM REJECT' : 'ACCEPT FOR PLANNING'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes slideInRight {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}} />
    </div>
  );
};

export default Requests;
