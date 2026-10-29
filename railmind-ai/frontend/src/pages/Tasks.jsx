import React, { useState, useEffect } from 'react';
import { 
  ClipboardList, Search, Filter, AlertTriangle, ShieldAlert, 
  Activity, CheckCircle2, Clock, Map, Settings, X, RefreshCw,
  Wrench, ActivitySquare, AlertOctagon, FileText, BarChart, Database
} from 'lucide-react';
import axios from 'axios';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Tasks = () => {
  const { user } = useAuth();
  const isDepartmentalUser = ['ENGG', 'SNT', 'TRD'].includes(user?.department);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState(null);
  
  const [searchParams] = useSearchParams();
  const contextTaskId = searchParams.get('taskId');
  const contextRequestId = searchParams.get('requestId');
  const contextRequestCode = searchParams.get('requestCode');
  
  const [filters, setFilters] = useState({
    department: isDepartmentalUser ? user.department : '',
    severity: '',
    status: '',
    overdue_only: false,
    limit: 50
  });

  const [selectedTask, setSelectedTask] = useState(null);
  const [scoringLoading, setScoringLoading] = useState(false);
  const [scoreResult, setScoreResult] = useState(null);

  const fetchTasksData = async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (filters.department) queryParams.append('department', filters.department);
      if (filters.severity) queryParams.append('severity', filters.severity);
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.overdue_only) queryParams.append('overdue_only', 'true');
      queryParams.append('limit', filters.limit);

      const [statsRes, tasksRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/tasks/stats/summary`),
        axios.get(`${BACKEND_URL}/api/tasks/?${queryParams.toString()}`)
      ]);

      setStats(statsRes.data);
      setTasks(tasksRes.data);
    } catch (err) {
      setError("Failed to synchronize with central maintenance database.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasksData();
    if (contextTaskId && !selectedTask) {
      openTaskDetail(parseInt(contextTaskId));
    }
  }, [filters, contextTaskId]);

  const handleScoreTask = async (taskId) => {
    setScoringLoading(true);
    setScoreResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/tasks/${taskId}/score`);
      setScoreResult(res.data);
      setSelectedTask(prev => ({ ...prev, criticality_score: res.data.criticality_score }));
      fetchTasksData();
    } catch (err) {
      alert("Failed to score task.");
    } finally {
      setScoringLoading(false);
    }
  };

  const openTaskDetail = async (taskId) => {
    setSelectedTask({ loading: true, id: taskId });
    setScoreResult(null);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/tasks/${taskId}`);
      setSelectedTask(res.data);
    } catch (err) {
      const fallbackTask = tasks.find(t => t.id === taskId);
      setSelectedTask(fallbackTask || null);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">
            <ClipboardList size={32} color="var(--color-primary)" />
            MAINTENANCE CONTROL BOARD
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <Database size={16} /> Central Infrastructure Register
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-primary" onClick={fetchTasksData} disabled={loading} style={{ fontWeight: 700 }}>
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <RefreshCw size={18} />}
            SYNC REGISTER
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600, borderRadius: 'var(--radius-md)' }}>
          <AlertOctagon size={24} /> {error}
        </div>
      )}

      {/* CONTEXT STRIP */}
      {(contextRequestId || contextTaskId) && (
        <div className="animate-slide-up" style={{ padding: '12px 24px', backgroundColor: 'var(--color-bg-subtle)', border: '1px solid var(--color-border-dark)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600, fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>TRACEABILITY CONTEXT:</span>
          {contextRequestCode ? (
            <span style={{ color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={16} /> REQUEST {contextRequestCode}</span>
          ) : (
            <span style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={16} /> NO REQUEST LINKED</span>
          )}
          <span style={{ color: 'var(--color-text-muted)' }}>→</span>
          {contextTaskId ? (
            <span style={{ color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}><Wrench size={16} /> TASK {contextTaskId}</span>
          ) : (
            <span style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}><Wrench size={16} /> NO TASK LINKED</span>
          )}
        </div>
      )}

      {/* KPI Section */}
      <div className="grid-cols-4 animate-slide-up">
        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>Total Active</div>
            <ActivitySquare size={20} color="var(--color-primary)" />
          </div>
          <div className="kpi-value">{stats ? stats.total : '-'}</div>
        </div>

        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-danger)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-danger-dark)' }}>Critical Priority</div>
            <ShieldAlert size={20} color="var(--color-danger)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-danger-dark)' }}>{stats?.by_severity?.['CRITICAL'] || 0}</div>
        </div>

        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-warning)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-warning-dark)' }}>Deadline Overdue</div>
            <Clock size={20} color="var(--color-warning)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-warning-dark)' }}>{stats ? stats.overdue : '-'}</div>
        </div>

        <div className="card hover-lift" style={{ borderTop: '4px solid var(--color-primary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div className="flex-between">
            <div className="section-heading" style={{ margin: 0, color: 'var(--color-navy)' }}>ENGG Backlog</div>
            <Wrench size={20} color="var(--color-primary)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--color-primary)' }}>{stats?.by_department?.['ENGG'] || 0}</div>
        </div>
      </div>

      {/* Control Panel / Filter Bar */}
      <div className="panel animate-slide-up" style={{ padding: '16px 24px', display: 'flex', flexDirection: 'row', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontWeight: 800, letterSpacing: '0.05em' }}>
          <Filter size={20} color="var(--color-primary)" /> FILTERS
        </div>
        
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border-dark)' }}></div>

        {!isDepartmentalUser && (
          <select className="input-rail" style={{ width: 'auto', fontWeight: 600 }} value={filters.department} onChange={(e) => setFilters(prev => ({...prev, department: e.target.value}))}>
            <option value="">ALL DEPARTMENTS</option>
            <option value="ENGG">ENGINEERING (ENGG)</option>
            <option value="SNT">SIGNAL & TELECOM (SNT)</option>
            <option value="TRD">TRACTION (TRD)</option>
          </select>
        )}

        <select className="input-rail" style={{ width: 'auto', fontWeight: 600 }} value={filters.severity} onChange={(e) => setFilters(prev => ({...prev, severity: e.target.value}))}>
          <option value="">ALL SEVERITIES</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>

        <select className="input-rail" style={{ width: 'auto', fontWeight: 600 }} value={filters.status} onChange={(e) => setFilters(prev => ({...prev, status: e.target.value}))}>
          <option value="">ALL STATUSES</option>
          <option value="PENDING">PENDING</option>
          <option value="SCHEDULED">SCHEDULED</option>
          <option value="COMPLETED">COMPLETED</option>
        </select>

        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 700, color: filters.overdue_only ? 'var(--color-danger-dark)' : 'var(--color-text-main)' }}>
          <input type="checkbox" checked={filters.overdue_only} onChange={(e) => setFilters(prev => ({...prev, overdue_only: e.target.checked}))} style={{ accentColor: 'var(--color-danger)', width: '18px', height: '18px' }} />
          OVERDUE ONLY
        </label>

        <button className="btn btn-outline" style={{ marginLeft: 'auto', fontWeight: 700 }} onClick={() => setFilters({ department: isDepartmentalUser ? user.department : '', severity: '', status: '', overdue_only: false, limit: 50 })}>
          RESET FILTERS
        </button>
      </div>

      {/* High-Density Task Table */}
      <div className="panel animate-slide-up" style={{ padding: 0, overflow: 'hidden' }}>
        {loading && tasks.length === 0 ? (
          <div className="flex-center" style={{ padding: '60px', color: 'var(--color-primary)' }}><Activity className="animate-spin" size={48} /></div>
        ) : tasks.length === 0 ? (
          <div className="empty-state" style={{ padding: '60px' }}>
            <ShieldAlert size={48} />
            <h3>NO CRITICAL TASKS</h3>
            <p>No operational tasks match filter criteria.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="rail-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '32px' }}>Task Code</th>
                  <th>Department</th>
                  <th>Operation Type</th>
                  <th>Severity</th>
                  <th>AI Risk Score</th>
                  <th>Strict Deadline</th>
                  <th style={{ paddingRight: '32px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(task => (
                  <tr key={task.id} onClick={() => openTaskDetail(task.id)} style={{ cursor: 'pointer' }}>
                    <td style={{ paddingLeft: '32px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{task.task_code}</td>
                    <td><span className="badge badge-neutral" style={{ fontWeight: 800 }}>{task.department}</span></td>
                    <td style={{ fontWeight: 600 }}>{task.task_type}</td>
                    <td>
                      <span className={`badge ${task.severity === 'CRITICAL' ? 'badge-danger' : task.severity === 'HIGH' ? 'badge-warning' : 'badge-primary'}`}>
                        {task.severity}
                      </span>
                    </td>
                    <td style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', fontSize: '1.125rem', color: task.criticality_score >= 80 ? 'var(--color-danger-dark)' : task.criticality_score >= 50 ? 'var(--color-warning-dark)' : 'var(--color-navy)' }}>
                      {task.criticality_score ? Math.round(task.criticality_score) : '-'}
                    </td>
                    <td style={{ color: task.is_overdue ? 'var(--color-danger-dark)' : 'var(--color-text-main)', fontWeight: task.is_overdue ? 800 : 600 }}>
                      {task.due_date} {task.is_overdue && <span style={{ fontSize: '0.7rem', marginLeft: '8px', color: 'white', backgroundColor: 'var(--color-danger-dark)', padding: '2px 6px', borderRadius: '4px' }}>OVERDUE</span>}
                    </td>
                    <td style={{ paddingRight: '32px' }}>
                      <span className={`badge ${task.status === 'COMPLETED' ? 'badge-success' : task.status === 'SCHEDULED' ? 'badge-warning' : 'badge-neutral'}`}>
                        {task.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Premium Drawer for Task Detail */}
      {selectedTask && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', justifyContent: 'flex-end' }}>
          <div className="animate-fade-in" style={{ width: '500px', backgroundColor: 'var(--color-bg-main)', borderLeft: '1px solid var(--color-border)', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto', boxShadow: 'var(--shadow-lg)' }}>
            
            {selectedTask.loading ? (
               <div className="flex-center" style={{ height: '100%', color: 'var(--color-primary)' }}><Activity className="animate-spin" size={32} /></div>
            ) : (
              <>
                <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, backgroundColor: 'var(--color-bg-white)', zIndex: 10, boxShadow: 'var(--shadow-sm)' }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-navy)' }}>
                    <FileText color="var(--color-primary)" /> {selectedTask.task_code}
                  </h2>
                  <button onClick={() => setSelectedTask(null)} className="hover-lift" style={{ padding: '8px', backgroundColor: 'var(--color-bg-subtle)', borderRadius: '50%' }}>
                    <X size={20} />
                  </button>
                </div>
                
                <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
                  
                  {/* Tags */}
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <span className="badge badge-primary">{selectedTask.department} DEPARTMENT</span>
                    <span className="badge badge-neutral">{selectedTask.status}</span>
                    {selectedTask.is_overdue && <span className="badge badge-danger">CRITICAL OVERDUE</span>}
                  </div>

                  {/* AI Risk Score Section */}
                  <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', position: 'relative', overflow: 'hidden' }}>
                    <div style={{ position: 'absolute', top: 0, left: 0, width: '6px', height: '100%', backgroundColor: selectedTask.criticality_score >= 80 ? 'var(--color-danger)' : selectedTask.criticality_score >= 50 ? 'var(--color-warning)' : 'var(--color-primary)' }}></div>
                    
                    <div className="flex-between">
                      <div className="section-heading" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
                        <ActivitySquare size={20} /> RAILMIND RISK SCORE
                      </div>
                      <span className={`badge ${selectedTask.severity === 'CRITICAL' ? 'badge-danger' : selectedTask.severity === 'HIGH' ? 'badge-warning' : 'badge-primary'}`}>
                        {selectedTask.severity} SEVERITY
                      </span>
                    </div>

                    <div className="flex-between" style={{ alignItems: 'flex-end' }}>
                      <span style={{ fontSize: '4rem', fontWeight: 800, lineHeight: 1, fontFamily: 'var(--font-mono)', color: selectedTask.criticality_score >= 80 ? 'var(--color-danger-dark)' : selectedTask.criticality_score >= 50 ? 'var(--color-warning-dark)' : 'var(--color-navy)' }}>
                        {selectedTask.criticality_score !== null ? Math.round(selectedTask.criticality_score) : 'N/A'}
                      </span>
                      <span style={{ fontSize: '1rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>/ 100</span>
                    </div>
                    
                    {selectedTask.criticality_score === null && (
                      <button className="btn btn-primary" style={{ justifyContent: 'center', width: '100%', padding: '16px' }} onClick={() => handleScoreTask(selectedTask.id)} disabled={scoringLoading}>
                        {scoringLoading ? <RefreshCw size={18} className="animate-spin" /> : <BarChart size={18} />}
                        ANALYZE CRITICALITY
                      </button>
                    )}

                    {scoreResult && (
                      <div style={{ backgroundColor: 'var(--color-success-bg)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                        <div style={{ color: 'var(--color-success-dark)', fontWeight: 800, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem' }}>
                          <CheckCircle2 size={18} /> INTELLIGENCE UPDATED
                        </div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--color-navy)' }}>Key Risk Factor: <span style={{ fontWeight: 700 }}>{scoreResult.feature_importance?.[0]?.feature || 'N/A'}</span></div>
                      </div>
                    )}
                  </div>

                  {/* Operation Data */}
                  <div>
                    <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Operation Parameters</h3>
                    <div className="card" style={{ padding: 0 }}>
                      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Task Type</span>
                        <span style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{selectedTask.task_type}</span>
                      </div>
                      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Corridor Location</span>
                        <span style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{selectedTask.section_id} (KM {selectedTask.km_from} - {selectedTask.km_to})</span>
                      </div>
                      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Block Type Required</span>
                        <span style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{selectedTask.block_type_required}</span>
                      </div>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Estimated Duration</span>
                        <span style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{selectedTask.estimated_hours} Hours</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Timetable Tracking</h3>
                    <div className="card" style={{ padding: 0 }}>
                      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Detected On</span>
                        <span style={{ fontWeight: 600, color: 'var(--color-navy)' }}>{selectedTask.detected_date}</span>
                      </div>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Strict Deadline</span>
                        <span style={{ fontWeight: 700, color: selectedTask.is_overdue ? 'var(--color-danger-dark)' : 'var(--color-navy)' }}>{selectedTask.due_date}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Execution Traceability</h3>
                    <div className="card" style={{ padding: 0 }}>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg-subtle)' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', fontWeight: 600 }}>Block Plan</span>
                        <span style={{ fontWeight: 600, color: 'var(--color-text-muted)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {selectedTask.block_plan_code ? (
                            <>
                              <AlertOctagon size={16} color="var(--color-primary)" />
                              <span style={{ color: 'var(--color-primary)', fontWeight: 800 }}>{selectedTask.block_plan_code}</span>
                            </>
                          ) : (
                            <>
                              <AlertOctagon size={16} /> UNASSIGNED
                            </>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>

                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;
