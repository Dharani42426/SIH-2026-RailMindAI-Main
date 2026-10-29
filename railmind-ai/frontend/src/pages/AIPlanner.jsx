import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, Send, Calendar, Clock, AlertTriangle, CheckCircle2, 
  ShieldAlert, GitMerge, ShieldCheck, Activity, MapPin, Layers, CheckCircle,
  Wrench, FileText
} from 'lucide-react';
import axios from 'axios';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const AIPlanner = () => {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [nlpResult, setNlpResult] = useState(null);
  const [optimizerResult, setOptimizerResult] = useState(null);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); 
  const [pipelineProgress, setPipelineProgress] = useState(0);

  const [searchParams] = useSearchParams();
  const contextTaskId = searchParams.get('taskId');
  const contextRequestId = searchParams.get('requestId');
  const contextRequestCode = searchParams.get('requestCode');

  useEffect(() => {
    let interval;
    if (loading && step === 2) {
      setPipelineProgress(33);
    } else if (loading && step === 3) {
      setPipelineProgress(66);
      interval = setInterval(() => {
        setPipelineProgress(prev => Math.min(prev + 5, 95));
      }, 500);
    } else if (!loading && optimizerResult) {
      setPipelineProgress(100);
    } else if (!loading && !optimizerResult && nlpResult) {
       setPipelineProgress(33);
    }
    return () => clearInterval(interval);
  }, [loading, step, optimizerResult, nlpResult]);

  const { user } = useAuth();
  const navigate = useNavigate();
  const [approvalLoading, setApprovalLoading] = useState(false);

  const executeCommand = async (cmdToRun) => {
    if (!cmdToRun.trim()) return;

    setCommand(cmdToRun); // Ensure input reflects what's running
    setLoading(true);
    setError(null);
    setStep(2);
    setNlpResult(null);
    setOptimizerResult(null);
    setPipelineProgress(10);

    try {
      const nlpRes = await axios.post(`${BACKEND_URL}/api/nlp/command`, { command: cmdToRun });
      setNlpResult(nlpRes.data);
      
      const sectionCode = nlpRes.data.entities?.section;
      if (!sectionCode) throw new Error("Please specify a railway section.");

      let sectionId;
      try {
        const sectionRes = await axios.get(`${BACKEND_URL}/api/sections/code/${sectionCode}`);
        sectionId = sectionRes.data.id;
      } catch (err) {
        throw new Error(`Invalid or unknown railway section code: ${sectionCode}`);
      }

      setStep(3);

      if (['OPTIMIZE', 'SCHEDULE_BLOCK', 'SCHEDULE'].includes(nlpRes.data.intent)) {
        const optRes = await axios.post(`${BACKEND_URL}/api/optimizer/generate`, {
          section_id: sectionId,
          start_date: new Date().toISOString().split('T')[0],
          plan_type: "WEEKLY"
        });

        if (!optRes.data.blocks || optRes.data.blocks.length === 0) {
            throw new Error("No tasks found or optimizer could not generate a plan.");
        }

        setOptimizerResult(optRes.data);
      } else {
        setStep(2);
      }

    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to process command.");
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const handleAskRailMind = (e) => {
    e.preventDefault();
    executeCommand(command);
  };

  const handleApprovePlan = async () => {
    if (!optimizerResult?.plan_id) return;
    setApprovalLoading(true);
    try {
      const approverName = user?.full_name || 'AI Planner';
      await axios.post(`${BACKEND_URL}/api/optimizer/plans/${optimizerResult.plan_id}/approve?approved_by=${encodeURIComponent(approverName)}`);
      
      // Navigate directly to the Block Register where they can see their new block window
      navigate('/blocks');
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to approve and publish the plan.");
    } finally {
      setApprovalLoading(false);
    }
  };

  const handleRejectPlan = () => {
    // Return to console to generate a new plan
    setCommand('');
    setOptimizerResult(null);
    setNlpResult(null);
    setStep(1);
    setPipelineProgress(0);
    setError(null);
  };

  // Auto-run when context is passed
  useEffect(() => {
    let isMounted = true;
    
    const autoPlan = async () => {
      if (contextTaskId && !loading && !optimizerResult && !nlpResult && !error) {
        try {
          // Fetch task details to get the section
          const taskRes = await axios.get(`${BACKEND_URL}/api/tasks/${contextTaskId}`);
          const task = taskRes.data;
          
          if (task && task.section_id) {
             const sectionsRes = await axios.get(`${BACKEND_URL}/api/sections/`);
             const section = sectionsRes.data.find(s => s.id === task.section_id);
             
             if (section && isMounted) {
               const autoCmd = `Schedule maintenance block for ${section.section_code} covering task ${task.task_code}`;
               executeCommand(autoCmd);
             }
          }
        } catch (err) {
          console.error("Failed to fetch task context for auto-planning", err);
        }
      }
    };
    
    autoPlan();
    
    return () => { isMounted = false; };
  }, [contextTaskId]);

  const primaryBlock = optimizerResult?.blocks?.[0];
  const safetyReport = optimizerResult?.safety_report;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* HERO HEADER */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="page-title">
            <BrainCircuit size={32} color="var(--color-primary)" /> 
            AI PLANNER CONSOLE
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            Powered by Qwen-2.5 NLP and OR-Tools CP-SAT
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', backgroundColor: 'var(--color-bg-white)', padding: '8px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <Activity size={18} color="var(--color-primary)" />
          <span style={{ fontWeight: 800, fontSize: '0.75rem', letterSpacing: '0.05em' }}>NLP ENGINE ONLINE</span>
        </div>
      </div>

      {/* CONTEXT STRIP */}
      {(contextRequestId || contextTaskId) && (
        <div className="animate-slide-up" style={{ padding: '12px 24px', backgroundColor: 'var(--color-bg-subtle)', border: '1px solid var(--color-border-dark)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600, fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>PLANNING CONTEXT:</span>
          {contextRequestCode ? (
            <span style={{ color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={16} /> REQUEST {contextRequestCode}</span>
          ) : (
            <span style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={16} /> NO REQUEST</span>
          )}
          <span style={{ color: 'var(--color-text-muted)' }}>|</span>
          {contextTaskId ? (
            <span style={{ color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}><Wrench size={16} /> TASK {contextTaskId}</span>
          ) : (
            <span style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}><Wrench size={16} /> NO TASK</span>
          )}
        </div>
      )}

      {/* INPUT CONSOLE */}
      <div className="card" style={{ padding: '0', border: '2px solid var(--color-primary)' }}>
        <form onSubmit={handleAskRailMind} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ padding: '24px', flex: 1, display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-primary)', whiteSpace: 'nowrap' }}>Ask RailMind...</span>
            <input 
              type="text" 
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="e.g., 'Optimize maintenance for KYN-KAS tomorrow'"
              style={{
                width: '100%', padding: '16px',
                borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg-main)', color: 'var(--color-navy)',
                fontSize: '1.125rem', outline: 'none', transition: 'all 0.3s'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--color-primary)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--color-border)'}
              disabled={loading}
            />
          </div>
          <button 
            type="submit" 
            style={{ 
              height: '100%', padding: '0 40px', backgroundColor: 'var(--color-primary)', color: 'white',
              border: 'none', fontWeight: 700, fontSize: '1.125rem', display: 'flex', alignItems: 'center', gap: '12px',
              cursor: loading || !command.trim() ? 'not-allowed' : 'pointer', opacity: loading || !command.trim() ? 0.7 : 1
            }}
            disabled={loading || !command.trim()}
          >
            {loading ? <Activity size={24} className="animate-spin" /> : <Send size={24} />}
            EXECUTE
          </button>
        </form>
        {error && (
          <div style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', borderTop: '1px solid var(--color-danger)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600 }}>
            <AlertTriangle size={20} /> {error}
          </div>
        )}
      </div>

      {/* PROCESSING PIPELINE */}
      {(step > 1 || optimizerResult) && (
        <div className="card animate-fade-in" style={{ padding: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative' }}>
            {/* Progress Bar Background */}
            <div style={{ position: 'absolute', top: '24px', left: '40px', right: '40px', height: '4px', backgroundColor: 'var(--color-border)', borderRadius: '2px', zIndex: 0 }}></div>
            {/* Progress Bar Fill */}
            <div style={{ 
              position: 'absolute', top: '24px', left: '40px', height: '4px', 
              backgroundColor: 'var(--color-primary)', borderRadius: '2px', zIndex: 0,
              width: `calc(${pipelineProgress}% - 80px)`,
              transition: 'width 0.5s ease-out',
            }}></div>
            
            {[
              { id: 1, label: 'PLAN GENERATED', icon: BrainCircuit, active: pipelineProgress >= 10, done: pipelineProgress > 33 },
              { id: 2, label: 'SAFETY VALIDATED', icon: ShieldCheck, active: pipelineProgress >= 33, done: pipelineProgress > 66 },
              { id: 3, label: 'CONTROLLER REVIEW', icon: Activity, active: pipelineProgress >= 66, done: pipelineProgress >= 95 },
              { id: 4, label: 'APPROVE & PUBLISH', icon: CheckCircle2, active: pipelineProgress >= 95, done: pipelineProgress === 100 }
            ].map((s, idx) => (
              <div key={s.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', position: 'relative', zIndex: 1, width: '150px' }}>
                <div style={{ 
                  width: '52px', height: '52px', borderRadius: '50%', 
                  backgroundColor: s.done ? 'var(--color-primary)' : (s.active ? 'var(--color-bg-white)' : 'var(--color-bg-white)'), 
                  border: `3px solid ${s.done ? 'var(--color-primary)' : (s.active ? 'var(--color-primary)' : 'var(--color-border)')}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: s.done ? 'white' : (s.active ? 'var(--color-primary)' : 'var(--color-border)'),
                  transition: 'all 0.3s'
                }}>
                  {s.done ? <CheckCircle2 size={24} /> : (s.active ? <Activity size={24} className="animate-spin" /> : <s.icon size={24} />)}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: 800, fontSize: '0.75rem', letterSpacing: '0.05em', color: s.active ? 'var(--color-navy)' : 'var(--color-text-light)' }}>
                    {s.label}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* OPTIMIZATION RESULTS */}
      {optimizerResult && primaryBlock && (
        <div className="grid-cols-2 animate-slide-up">
          
          {/* LEFT: PLAN DETAILS */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="flex-between">
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
                <Layers color="var(--color-primary)" /> PROPOSED BLOCK PLAN
              </h2>
            </div>
            
            <div style={{ backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', padding: '24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div>
                <div className="section-heading">Target Section</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={20} color="var(--color-accent-saffron)" /> {nlpResult.entities?.section}
                </div>
              </div>
              <div>
                <div className="section-heading">Execution Date</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Calendar size={20} color="var(--color-primary)" /> {primaryBlock.date}
                </div>
              </div>
              <div>
                <div className="section-heading">Block Window</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Clock size={20} color="var(--color-warning-dark)" /> {primaryBlock.start_time} - {primaryBlock.end_time}
                </div>
              </div>
              <div>
                <div className="section-heading">Integration Level</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-success-dark)', marginTop: '4px' }}>
                  {primaryBlock.is_integrated ? `MULTI-DEPT (${primaryBlock.departments.length})` : 'SINGLE TASK'}
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '24px' }}>
              <div className="section-heading">AI Strategic Reasoning</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {(optimizerResult.explanations && optimizerResult.explanations.length > 0 ? optimizerResult.explanations : ["Optimized based on predictive health and severity"]).map((reason, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 16px', backgroundColor: 'var(--color-primary-light)', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--color-primary)' }}>
                    <BrainCircuit size={18} color="var(--color-primary)" style={{ marginTop: '2px' }} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-navy)' }}>{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT: SAFETY DOMINANT GATE */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div className="card" style={{ 
              borderColor: safetyReport?.safe ? 'var(--color-success-dark)' : 'var(--color-danger-dark)', 
              backgroundColor: safetyReport?.safe ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
              borderWidth: '2px',
              padding: '32px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center'
            }}>
              {safetyReport?.safe ? <ShieldCheck size={64} color="var(--color-success-dark)" /> : <AlertTriangle size={64} color="var(--color-danger-dark)" />}
              
              <div style={{ fontWeight: 800, fontSize: '2.5rem', letterSpacing: '-0.025em', color: safetyReport?.safe ? 'var(--color-success-dark)' : 'var(--color-danger-dark)', textTransform: 'uppercase', marginTop: '16px' }}>
                {safetyReport?.safe ? 'SAFETY VALIDATED' : 'VALIDATION FAILED'}
              </div>
              
              <div style={{ fontSize: '1.125rem', color: 'var(--color-text-main)', marginTop: '16px', fontWeight: 600, maxWidth: '80%' }}>
                {safetyReport?.safe 
                  ? 'CP-SAT confirms no scheduling conflicts detected. Mandatory safety buffers applied.' 
                  : (safetyReport?.violations?.join(', ') || 'CRITICAL: Block window conflicts with active train schedules.')}
              </div>

              <div style={{ marginTop: '32px', width: '100%', display: 'flex', gap: '16px' }}>
                <button className="btn" style={{ flex: 1, backgroundColor: 'var(--color-bg-white)', border: '1px solid var(--color-border)', color: 'var(--color-navy)', padding: '16px', fontSize: '1.125rem', fontWeight: 700 }} onClick={handleRejectPlan} disabled={approvalLoading}>
                  REJECT
                </button>
                <button className="btn" style={{ flex: 2, backgroundColor: safetyReport?.safe ? 'var(--color-success-dark)' : 'var(--color-danger-dark)', color: 'white', padding: '16px', fontSize: '1.125rem', fontWeight: 700, opacity: safetyReport?.safe ? 1 : 0.5, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }} onClick={handleApprovePlan} disabled={!safetyReport?.safe || approvalLoading}>
                  {approvalLoading && <Activity size={20} className="animate-spin" />}
                  {safetyReport?.safe ? 'APPROVE & PUBLISH' : 'UNSAFE TO PUBLISH'}
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default AIPlanner;
