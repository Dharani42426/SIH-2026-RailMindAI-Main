import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, CalendarClock, Activity, Map, Zap,
  AlertTriangle, BrainCircuit, GitMerge, LineChart, Bell, Search,
  ShieldCheck, TrainTrack, User, CheckCircle2, XCircle, LogOut, Loader2,
  FileText, Inbox
} from 'lucide-react';
import axios from 'axios';
import './index.css';

// Auth
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy-loaded Pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AIPlanner = lazy(() => import('./pages/AIPlanner'));
const Tasks = lazy(() => import('./pages/Tasks'));
const Trains = lazy(() => import('./pages/Trains'));
const Assets = lazy(() => import('./pages/Assets'));
const Conflicts = lazy(() => import('./pages/Conflicts'));
const WhatIf = lazy(() => import('./pages/WhatIf'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Login = lazy(() => import('./pages/Login'));
const BlockPlans = lazy(() => import('./pages/BlockPlans'));
const Requests = lazy(() => import('./pages/Requests'));

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Premium Loading Fallback
const PageLoader = () => (
  <div className="page-loader">
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <TrainTrack size={24} color="var(--color-primary)" />
      <div style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '0.05em', color: 'var(--color-navy)' }}>
        RAILMIND AI
      </div>
    </div>
    <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
      Loading Console Interface...
    </div>
    <div className="track"><div className="train"></div></div>
  </div>
);

const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Role-aware Navigation Prioritization
  const getNavGroups = () => {
    const isEngg = ['ENGG'].includes(user?.department) || ['DEN', 'SSE', 'PWI'].includes(user?.role);
    const isSnt = ['SNT'].includes(user?.department) || ['DSTE', 'SI'].includes(user?.role);
    const isTrd = ['TRD'].includes(user?.department) || ['DEE'].includes(user?.role);
    const isAdmin = user?.role === 'ADMIN';

    if (isAdmin) {
      return [
        { title: "PRIMARY", items: [
          { name: 'System Control', path: '/', icon: LayoutDashboard },
          { name: 'Request Inbox', path: '/requests', icon: Inbox },
          { name: 'Analytics', path: '/analytics', icon: LineChart }
        ]},
        { title: "SECONDARY", items: [
          { name: 'AI Planner', path: '/planner', icon: BrainCircuit },
          { name: 'Block Plans', path: '/blocks', icon: Map },
          { name: 'Maintenance Board', path: '/tasks', icon: Activity },
          { name: 'Train Dispatch', path: '/trains', icon: CalendarClock },
          { name: 'Asset Health', path: '/assets', icon: Zap },
          { name: 'Safety & Conflicts', path: '/conflicts', icon: AlertTriangle },
          { name: 'What-If Simulator', path: '/what-if', icon: GitMerge }
        ]}
      ];
    }

    if (isEngg) {
      return [
        { title: "PRIMARY", items: [
          { name: 'Engineering Dashboard', path: '/', icon: LayoutDashboard },
          { name: 'Maintenance Requests', path: '/requests', icon: FileText },
          { name: 'Maintenance Board', path: '/tasks', icon: Activity },
          { name: 'Asset Health', path: '/assets', icon: Zap },
          { name: 'Train Dispatch', path: '/trains', icon: CalendarClock }
        ]},
        { title: "SECONDARY", items: [
          { name: 'Block Plans', path: '/blocks', icon: Map },
          { name: 'Safety & Conflicts', path: '/conflicts', icon: AlertTriangle },
          { name: 'Analytics', path: '/analytics', icon: LineChart },
          { name: 'What-If Simulator', path: '/what-if', icon: GitMerge }
        ]}
      ];
    }

    if (isSnt) {
      return [
        { title: "PRIMARY", items: [
          { name: 'Signal & Telecom Control', path: '/', icon: LayoutDashboard },
          { name: 'Maintenance Requests', path: '/requests', icon: FileText },
          { name: 'Maintenance Board', path: '/tasks', icon: Activity },
          { name: 'Train Dispatch', path: '/trains', icon: CalendarClock },
          { name: 'Safety & Conflicts', path: '/conflicts', icon: AlertTriangle }
        ]},
        { title: "SECONDARY", items: [
          { name: 'Asset Health', path: '/assets', icon: Zap },
          { name: 'Block Plans', path: '/blocks', icon: Map },
          { name: 'Analytics', path: '/analytics', icon: LineChart },
          { name: 'What-If Simulator', path: '/what-if', icon: GitMerge }
        ]}
      ];
    }

    if (isTrd) {
      return [
        { title: "PRIMARY", items: [
          { name: 'Traction & Power Control', path: '/', icon: LayoutDashboard },
          { name: 'Maintenance Requests', path: '/requests', icon: FileText },
          { name: 'Maintenance Board', path: '/tasks', icon: Activity },
          { name: 'Asset Health', path: '/assets', icon: Zap },
          { name: 'Train Dispatch', path: '/trains', icon: CalendarClock },
          { name: 'Safety & Conflicts', path: '/conflicts', icon: AlertTriangle }
        ]},
        { title: "SECONDARY", items: [
          { name: 'Block Plans', path: '/blocks', icon: Map },
          { name: 'Analytics', path: '/analytics', icon: LineChart },
          { name: 'What-If Simulator', path: '/what-if', icon: GitMerge }
        ]}
      ];
    }

    // Default: CONTROLLER / GENERAL OPERATIONS
    return [
      { title: "PRIMARY", items: [
        { name: 'Operations Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Request Inbox', path: '/requests', icon: Inbox },
        { name: 'AI Planner', path: '/planner', icon: BrainCircuit },
        { name: 'Block Plans', path: '/blocks', icon: Map },
        { name: 'Train Dispatch', path: '/trains', icon: CalendarClock },
        { name: 'Safety & Conflicts', path: '/conflicts', icon: AlertTriangle }
      ]},
      { title: "SECONDARY", items: [
        { name: 'Maintenance Board', path: '/tasks', icon: Activity },
        { name: 'Asset Health', path: '/assets', icon: Zap },
        { name: 'What-If Simulator', path: '/what-if', icon: GitMerge },
        { name: 'Analytics', path: '/analytics', icon: LineChart }
      ]}
    ];
  };

  const navGroups = getNavGroups();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <aside className="sidebar">
      {/* Brand Identity */}
      <div style={{ padding: '28px 24px', display: 'flex', alignItems: 'center', gap: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{
          width: '40px', height: '40px', backgroundColor: 'var(--color-bg-white)',
          borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 10px rgba(0,0,0,0.2)'
        }}>
          <TrainTrack size={24} color="var(--color-primary)" />
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: '1.25rem', letterSpacing: '0.05em', color: 'var(--color-text-inverse)', lineHeight: 1.2 }}>
            RAILMIND AI
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--color-accent-saffron)', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 700 }}>
            Operations Control
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '32px', flex: 1, overflowY: 'auto' }}>
        {navGroups.map((group, idx) => (
          <div key={idx} className="animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--color-text-muted)', letterSpacing: '0.1em', marginBottom: '12px', paddingLeft: '16px' }}>
              {group.title}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {group.items.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.name} to={item.path}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 16px', borderRadius: 'var(--radius-sm)',
                      color: isActive ? 'var(--color-text-inverse)' : 'var(--color-text-light)',
                      backgroundColor: isActive ? 'var(--color-primary)' : 'transparent',
                      fontWeight: isActive ? 600 : 500, transition: 'all 0.2s ease', fontSize: '0.875rem'
                    }}
                    onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = 'var(--color-navy-hover)'; }}
                    onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <item.icon size={18} color={isActive ? 'white' : 'var(--color-text-muted)'} />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User Profile + Logout */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'var(--color-navy-hover)', padding: '16px' }}>
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px' }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: 'var(--radius-sm)', backgroundColor: 'rgba(255,255,255,0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              <User size={18} color="var(--color-text-light)" />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-inverse)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.full_name}
              </div>
              <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--color-text-muted)', letterSpacing: '0.05em' }}>
                {user.role} · {user.department}
              </div>
            </div>
            <button
              onClick={handleLogout} title="Secure Logout"
              style={{
                padding: '8px', borderRadius: 'var(--radius-sm)', color: 'var(--color-text-light)',
                transition: 'all 0.2s', cursor: 'pointer', flexShrink: 0,
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgba(220,38,38,0.2)'; e.currentTarget.style.color = 'var(--color-danger)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'var(--color-text-light)'; }}
            >
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};

const Header = () => {
  const [health, setHealth] = useState({ status: 'checking' });
  const location = useLocation();
  const { user } = useAuth();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/health`);
        setHealth({ status: 'online', data: res.data });
      } catch (err) {
        setHealth({ status: 'offline' });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000); // Check more frequently
    return () => clearInterval(interval);
  }, []);

  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    const activeRoute = path.substring(1);
    return activeRoute.charAt(0).toUpperCase() + activeRoute.slice(1).replace('-', ' ');
  };

  const currentDate = new Date().toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  });

  return (
    <header className="top-header">
      {/* Left: Breadcrumbs & Identity */}
      <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)', letterSpacing: '-0.025em' }}>
          RAILMIND <span style={{ color: 'var(--color-primary)' }}>AI</span>
        </div>
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }}></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
          <span>{user?.division || 'OPERATIONS'}</span>
          <span>/</span>
          <span style={{ color: 'var(--color-navy)', fontWeight: 800 }}>{getBreadcrumb()}</span>
        </div>
      </div>

      {/* Right: Operations Control */}
      <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>

        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
          {currentDate}
        </div>

        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }}></div>

        {/* Search & Notifications */}
        <div style={{ display: 'flex', gap: '12px', color: 'var(--color-text-muted)' }}>
          <button className="hover-lift" style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-main)' }}><Search size={18} /></button>
          <button className="hover-lift" style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-bg-main)', position: 'relative' }}>
            <Bell size={18} />
            <span style={{ position: 'absolute', top: '6px', right: '8px', width: '8px', height: '8px', backgroundColor: 'var(--color-danger)', borderRadius: '50%', border: '2px solid var(--color-bg-main)' }}></span>
          </button>
        </div>

        {/* Connection Status */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em', padding: '6px 12px', borderRadius: 'var(--radius-sm)',
          backgroundColor: health.status === 'online' ? 'var(--color-success-bg)' : health.status === 'offline' ? 'var(--color-danger-bg)' : 'var(--color-bg-main)',
          border: `1px solid ${health.status === 'online' ? 'rgba(5, 150, 105, 0.3)' : health.status === 'offline' ? 'rgba(220, 38, 38, 0.3)' : 'var(--color-border)'}`
        }}>
          {health.status === 'online' ? (
            <><CheckCircle2 size={14} color="var(--color-success-dark)" /><span style={{ color: 'var(--color-success-dark)' }}>CORE ONLINE</span></>
          ) : health.status === 'offline' ? (
            <><XCircle size={14} color="var(--color-danger-dark)" /><span style={{ color: 'var(--color-danger-dark)' }}>UPLINK LOST</span></>
          ) : (
            <><Loader2 size={14} className="animate-spin" color="var(--color-text-muted)" /><span style={{ color: 'var(--color-text-muted)' }}>CHECKING</span></>
          )}
        </div>

        {/* User Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingLeft: '12px', borderLeft: '1px solid var(--color-border)' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-navy)' }}>
              {user?.full_name || 'AUTHENTICATING...'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-primary)', fontWeight: 700, letterSpacing: '0.05em' }}>
              {user?.role || ''}{user?.department ? ` · ${user.department}` : ''}
            </div>
          </div>
          <div style={{ width: '40px', height: '40px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--color-border-focus)' }}>
            <User size={20} color="var(--color-primary)" />
          </div>
        </div>
      </div>
    </header>
  );
};

const AppLayout = () => {
  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <Header />
        <div className="content-scrollable">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/planner" element={<ProtectedRoute><AIPlanner /></ProtectedRoute>} />
              <Route path="/blocks" element={<ProtectedRoute><BlockPlans /></ProtectedRoute>} />
              <Route path="/tasks" element={<ProtectedRoute><Tasks /></ProtectedRoute>} />
              <Route path="/trains" element={<ProtectedRoute><Trains /></ProtectedRoute>} />
              <Route path="/assets" element={<ProtectedRoute><Assets /></ProtectedRoute>} />
              <Route path="/conflicts" element={<ProtectedRoute><Conflicts /></ProtectedRoute>} />
              <Route path="/what-if" element={<ProtectedRoute><WhatIf /></ProtectedRoute>} />
              <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
              <Route path="/requests" element={<ProtectedRoute><Requests /></ProtectedRoute>} />
            </Routes>
          </Suspense>
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/*" element={<AppLayout />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
