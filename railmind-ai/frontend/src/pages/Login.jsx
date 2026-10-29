import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  TrainTrack, ShieldCheck, AlertTriangle, Activity,
  User, Building2, Radio, KeyRound, ArrowRight
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';



const Login = () => {
  const [employeeId, setEmployeeId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [authStage, setAuthStage] = useState('idle'); // idle -> authenticating -> verifying -> success
  const [backendStatus, setBackendStatus] = useState('checking');
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true });
  }, [isAuthenticated, navigate]);

  // Check backend health
  useEffect(() => {
    const check = async () => {
      try {
        await axios.get(`${BACKEND_URL}/health`);
        setBackendStatus('online');
      } catch {
        setBackendStatus('offline');
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!employeeId.trim()) {
      setError('Please enter your Employee ID.');
      return;
    }
    
    setError('');
    setLoading(true);
    setAuthStage('authenticating');

    try {
      // 1. Fire the actual login request
      await login(employeeId.trim().toUpperCase());
      
      // 2. The request succeeded. Progress visual states without fake delays
      setAuthStage('verifying');
      
      // Give a tiny moment (400ms) to read "VERIFYING OPERATIONS ACCESS..."
      setTimeout(() => {
        setAuthStage('success');
        
        // Give a tiny moment (600ms) to read "IDENTITY VERIFIED ✓" then redirect
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 600);
        
      }, 400);
      
    } catch (err) {
      setAuthStage('idle');
      if (err.response?.status === 401) {
        setError('UNAUTHORIZED: Employee ID not found.');
      } else if (err.response?.status === 403) {
        setError('ACCESS DENIED: Account is deactivated.');
      } else {
        setError('CONNECTION FAILED: Unable to reach core systems.');
      }
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      position: 'relative', height: '100vh', width: '100vw', overflow: 'hidden', 
      display: 'flex', alignItems: 'center', justifyContent: 'flex-start', padding: '5%',
      backgroundColor: '#0B1120'
    }}>
      
      {/* Cinematic Background Image */}
      <div style={{
        position: 'absolute', inset: 0, 
        backgroundImage: 'url(/hero_train.png)', backgroundSize: 'cover', backgroundPosition: 'center',
        animation: 'bgPanIn 2s ease-out both', zIndex: 0
      }} />

      {/* Global CSS for Animations */}
      <style>{`
        @keyframes bgPanIn {
          0% { opacity: 0; transform: scale(1.05); }
          100% { opacity: 1; transform: scale(1); }
        }
        @keyframes glassSlideUp {
          0% { opacity: 0; transform: translateY(40px) scale(0.98); backdrop-filter: blur(0px); }
          100% { opacity: 1; transform: translateY(0) scale(1); backdrop-filter: blur(24px); }
        }
        @keyframes brandFadeIn {
          0% { opacity: 0; transform: translateX(20px); }
          100% { opacity: 1; transform: translateX(0); }
        }
      `}</style>

      {/* Dark Overlay for contrast */}
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(11, 17, 32, 0.7) 0%, rgba(11, 17, 32, 0.2) 50%, rgba(11, 17, 32, 0.8) 100%)', zIndex: 1, animation: 'bgPanIn 2s ease-out both' }} />
      
      {/* Brand Floating Top-Right */}
      <div style={{ position: 'absolute', top: '5%', right: '5%', zIndex: 10, animation: 'brandFadeIn 1.2s ease-out 1s both', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '24px', flexDirection: 'row-reverse' }}>
          <div style={{ width: '96px', height: '96px', backgroundColor: 'var(--color-primary)', borderRadius: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 20px 40px rgba(29, 78, 216, 0.4)' }}>
            <TrainTrack size={56} color="white" />
          </div>
          <h1 style={{ fontSize: '5rem', fontWeight: 900, color: 'white', letterSpacing: '0.02em', margin: 0, lineHeight: 1.1, textShadow: '0 10px 30px rgba(0,0,0,0.6)', textAlign: 'right' }}>
            RAILMIND AI
          </h1>
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-accent-saffron)', letterSpacing: '0.15em', textTransform: 'uppercase', textShadow: '0 4px 15px rgba(0,0,0,0.6)', textAlign: 'right' }}>
          Intelligent Railway Operations
        </div>
      </div>

      {/* Glassmorphism Login Panel */}
      <div style={{ 
        position: 'relative', zIndex: 20, width: '100%', maxWidth: '380px',
        padding: '50px 36px', borderRadius: '80px',
        background: 'rgba(37, 99, 235, 0.2)',
        backdropFilter: 'blur(40px)', WebkitBackdropFilter: 'blur(40px)',
        border: '1px solid rgba(37, 99, 235, 0.4)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.2)',
        animation: 'glassSlideUp 1s cubic-bezier(0.16, 1, 0.3, 1) 3s both'
      }}>
        
        {/* Success Overlay state */}
        {authStage === 'success' && (
          <div className="animate-fade-in" style={{
            position: 'absolute', inset: 0, backgroundColor: 'rgba(5, 150, 105, 0.85)', backdropFilter: 'blur(20px)', borderRadius: '80px',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 50, color: 'white'
          }}>
            <ShieldCheck size={64} style={{ marginBottom: '24px' }} />
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '0.05em' }}>VERIFIED ✓</h2>
            <p style={{ marginTop: '8px', fontSize: '0.75rem', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>Initializing Console...</p>
          </div>
        )}

        <div style={{ width: '100%' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '32px', padding: '8px 16px', backgroundColor: 'rgba(255,255,255,0.4)', borderRadius: 'var(--radius-pill)', border: '1px solid rgba(255,255,255,0.3)', width: 'fit-content', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
            <Building2 size={16} color="var(--color-primary)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              MUMBAI DIV
            </span>
          </div>

          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-navy)', margin: '0 0 8px', letterSpacing: '-0.02em' }}>
            Access
          </h2>
          <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-muted)', margin: '0 0 24px' }}>
            Enter your authorized ID.
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '8px' }}>
                <KeyRound size={14} color="var(--color-text-muted)" /> Employee ID
              </label>
              <div style={{ position: 'relative' }}>
                <User size={18} color="var(--color-text-muted)" style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  value={employeeId}
                  onChange={(e) => { setEmployeeId(e.target.value); setError(''); }}
                  placeholder="e.g. AK001"
                  autoFocus
                  disabled={loading}
                  style={{
                    width: '100%', backgroundColor: 'rgba(255,255,255,0.6)',
                    border: '1px solid rgba(255,255,255,0.5)', borderRadius: 'var(--radius-pill)',
                    padding: '12px 16px 12px 42px', color: 'var(--color-text-main)', fontSize: '1rem', fontWeight: 600,
                    outline: 'none', transition: 'all 0.2s',
                    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
                  }}
                  onFocus={(e) => { e.target.style.backgroundColor = 'rgba(255,255,255,0.9)'; e.target.style.borderColor = 'var(--color-primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(30, 58, 138, 0.1)'; }}
                  onBlur={(e) => { e.target.style.backgroundColor = 'rgba(255,255,255,0.6)'; e.target.style.borderColor = 'rgba(255,255,255,0.5)'; e.target.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.02)'; }}
                />
              </div>
            </div>

            {error && (
              <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', backgroundColor: 'rgba(254, 226, 226, 0.7)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: 'var(--radius-pill)', color: 'var(--color-danger-dark)', fontSize: '0.8rem', fontWeight: 700 }}>
                <AlertTriangle size={18} /> {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !employeeId.trim()}
              className="hover-lift"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                padding: '14px 24px', backgroundColor: loading || !employeeId.trim() ? 'rgba(0,0,0,0.1)' : 'var(--color-primary)',
                color: loading || !employeeId.trim() ? 'var(--color-text-muted)' : 'white', border: 'none', borderRadius: 'var(--radius-pill)', fontSize: '0.9rem', fontWeight: 800, letterSpacing: '0.05em',
                cursor: loading || !employeeId.trim() ? 'not-allowed' : 'pointer', transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: loading || !employeeId.trim() ? 'none' : '0 10px 20px rgba(30, 58, 138, 0.2)'
              }}
            >
              {authStage === 'authenticating' ? (
                <><Activity size={18} className="animate-spin" /> AUTHENTICATING...</>
              ) : authStage === 'verifying' ? (
                <><Activity size={18} className="animate-spin" /> VERIFYING ACCESS...</>
              ) : (
                <>SECURE LOGIN <ArrowRight size={18} /></>
              )}
            </button>
          </form>

          <div style={{ marginTop: '24px', padding: '24px', backgroundColor: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.4)', borderRadius: '40px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--color-navy)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Demo</span>
              <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--color-primary)' }}>AUTO-FILL</span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                { id: 'AK001', role: 'CONTROLLER' },
                { id: 'RS002', role: 'ENGINEERING' },
                { id: 'VP003', role: 'S&T' },
                { id: 'MT004', role: 'TRD' },
              ].map((c) => (
                <button
                  key={c.id} type="button" disabled={loading}
                  onClick={() => { setEmployeeId(c.id); setError(''); }}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '10px 16px', width: '100%',
                    backgroundColor: 'rgba(255,255,255,0.6)',
                    border: '1px solid rgba(255,255,255,0.5)', borderRadius: 'var(--radius-pill)',
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-primary-light)'; e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.6)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.5)'; }}
                >
                  <span style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 700, fontSize: '0.7rem' }}>{c.role}</span>
                  <span style={{ fontWeight: 800, color: 'var(--color-navy)', fontSize: '0.8rem' }}>{c.id}</span>
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '24px' }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: 'var(--radius-pill)',
              backgroundColor: backendStatus === 'online' ? 'rgba(5, 150, 105, 0.15)' : backendStatus === 'offline' ? 'rgba(220, 38, 38, 0.15)' : 'rgba(0,0,0,0.05)',
              border: `1px solid ${backendStatus === 'online' ? 'rgba(5, 150, 105, 0.3)' : backendStatus === 'offline' ? 'rgba(220, 38, 38, 0.3)' : 'rgba(0,0,0,0.1)'}`,
            }}>
              <Radio size={12} className={backendStatus === 'online' ? 'animate-pulse' : ''} color={backendStatus === 'online' ? 'var(--color-success-dark)' : backendStatus === 'offline' ? 'var(--color-danger-dark)' : 'var(--color-text-muted)'} />
              <span style={{
                fontSize: '0.65rem', fontWeight: 800,
                color: backendStatus === 'online' ? 'var(--color-success-dark)' : backendStatus === 'offline' ? 'var(--color-danger-dark)' : 'var(--color-text-muted)',
                letterSpacing: '0.05em',
              }}>
                {backendStatus === 'online' ? 'CORE ONLINE' : backendStatus === 'offline' ? 'OFFLINE' : 'CHECKING'}
              </span>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
};

export default Login;
