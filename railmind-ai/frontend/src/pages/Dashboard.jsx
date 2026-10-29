import React, { useState, useEffect, useMemo } from 'react';
import { 
  Activity, AlertTriangle, Calendar, CheckCircle2, Map, ShieldAlert, 
  ServerCrash, Layers, MapPin, ArrowRight, Train, Radio, 
  ActivitySquare, Zap, Target, Loader2, Wrench, Antenna, BatteryCharging, Shield, Activity as ActivityIcon, Bell, TrendingUp, Check
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ComposedChart } from 'recharts';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const getDashboardType = (user) => {
  if (!user || (!user.role && !user.department)) return 'GENERAL';
  if (user.role === 'ADMIN') return 'ADMIN';
  if (user.role === 'CONTROLLER') return 'CONTROLLER';
  if (['ENGG'].includes(user.department) || ['DEN', 'SSE', 'PWI'].includes(user.role)) return 'ENGG';
  if (['SNT'].includes(user.department) || ['DSTE', 'SI'].includes(user.role)) return 'SNT';
  if (['TRD'].includes(user.department) || ['DEE'].includes(user.role)) return 'TRD';
  return 'GENERAL';
};

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    activeBlocks: [],
    criticalTasks: [],
    trainWindows: [],
    kpis: {}
  });
  
  // New Feature States
  const [forecastData, setForecastData] = useState(null);
  const [validationMetrics, setValidationMetrics] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [liveNotification, setLiveNotification] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  const [error, setError] = useState(null);
  
  const { user } = useAuth();
  const dashboardType = getDashboardType(user);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [blocksRes, tasksRes, kpiRes, trainsRes, forecastRes, valRes, benchRes] = await Promise.allSettled([
          axios.get(`${BACKEND_URL}/api/optimizer/plans`),
          axios.get(`${BACKEND_URL}/api/tasks/critical?top_n=20`),
          axios.get(`${BACKEND_URL}/api/analytics/dashboard`),
          axios.get(`${BACKEND_URL}/api/trains/section/1/windows`),
          axios.get(`${BACKEND_URL}/api/analytics/forecast/goods`),
          axios.get(`${BACKEND_URL}/api/analytics/forecast/validation`),
          axios.get(`${BACKEND_URL}/api/analytics/benchmark`)
        ]);
        
        setData({
          activeBlocks: blocksRes.status === 'fulfilled' && Array.isArray(blocksRes.value.data) ? blocksRes.value.data : [],
          criticalTasks: tasksRes.status === 'fulfilled' && Array.isArray(tasksRes.value.data) ? tasksRes.value.data : [],
          trainWindows: trainsRes.status === 'fulfilled' && trainsRes.value.data.trains ? trainsRes.value.data.trains : [],
          kpis: kpiRes.status === 'fulfilled' ? kpiRes.value.data : {}
        });
        
        if (forecastRes.status === 'fulfilled') setForecastData(forecastRes.value.data);
        if (valRes.status === 'fulfilled') setValidationMetrics(valRes.value.data);
        if (benchRes.status === 'fulfilled') setBenchmark(benchRes.value.data);

        if (blocksRes.status === 'rejected' && tasksRes.status === 'rejected') {
          setError("Failed to establish uplink with core systems. Live data unavailable.");
        } else {
          setError(null);
        }
      } catch (err) {
        console.error("Dashboard fetch error", err);
        setError("Failed to establish uplink with core systems. Live data unavailable.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket Connection
  useEffect(() => {
    let ws;
    let reconnectTimeout;
    
    const connectWs = () => {
      const wsUrl = BACKEND_URL.replace(/^http/, 'ws') + '/ws/notifications';
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => setWsConnected(true);
      
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'PLAN_APPROVED') {
            setLiveNotification({
              title: payload.title,
              message: payload.message,
              section: payload.data?.section || '',
              time: 'Just now'
            });
            setTimeout(() => setLiveNotification(null), 8000);
          }
        } catch (e) { console.error('WS parse error', e); }
      };
      
      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWs, 5000);
      };
    };
    
    connectWs();
    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, []);

  const triggerApprovalDemo = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/analytics/trigger-approval`);
    } catch (err) {
      console.error("Failed to trigger approval", err);
    }
  };

  const stations = ["CSMT", "DADAR", "KURLA", "GHATKOPAR", "THANE", "DOMBIVLI", "KALYAN"];

  const config = useMemo(() => {
    const roleConfigs = {
      CONTROLLER: {
        title: 'OPERATIONS CONTROL',
        subtitle: 'Central Corridor | Real-time Network Monitor',
        icon: <ActivitySquare size={28} color="var(--color-primary)" />,
        kpis: ['blocks', 'conflicts', 'tasks', 'health'],
        panels: ['blocks', 'tasks'],
        quickActions: [
          { label: 'OPEN AI PLANNER', to: '/planner', icon: <Zap size={18} />, primary: true },
          { label: 'VIEW BLOCK PLANS', to: '/blocks', icon: <Layers size={18} />, primary: false },
        ]
      },
      ENGG: {
        title: 'ENGINEERING OPERATIONS',
        subtitle: 'Central Corridor | Infrastructure & Civil Monitor',
        icon: <Wrench size={28} color="var(--color-primary)" />,
        kpis: ['tasks', 'health', 'blocks', 'conflicts'],
        panels: ['tasks', 'blocks'],
        quickActions: [
          { label: 'MAINTENANCE BOARD', to: '/tasks', icon: <Target size={18} />, primary: true },
          { label: 'ASSET HEALTH', to: '/assets', icon: <ActivityIcon size={18} />, primary: false },
        ]
      },
      SNT: {
        title: 'SIGNAL & TELECOM CONTROL',
        subtitle: 'Central Corridor | Signalling & Communications Monitor',
        icon: <Antenna size={28} color="var(--color-primary)" />,
        kpis: ['tasks', 'health', 'conflicts', 'blocks'],
        panels: ['tasks', 'blocks'], // Blocks relevant for signal testing windows
        quickActions: [
          { label: 'MAINTENANCE BOARD', to: '/tasks', icon: <Target size={18} />, primary: true },
          { label: 'SAFETY & CONFLICTS', to: '/conflicts', icon: <ShieldAlert size={18} />, primary: false },
        ]
      },
      TRD: {
        title: 'TRACTION & POWER CONTROL',
        subtitle: 'Central Corridor | OHE & Power Systems Monitor',
        icon: <BatteryCharging size={28} color="var(--color-primary)" />,
        kpis: ['tasks', 'blocks', 'health', 'conflicts'],
        panels: ['tasks', 'blocks'], // Blocks extremely relevant for OHE
        quickActions: [
          { label: 'MAINTENANCE BOARD', to: '/tasks', icon: <Target size={18} />, primary: true },
          { label: 'ASSET HEALTH', to: '/assets', icon: <ActivityIcon size={18} />, primary: false },
        ]
      },
      ADMIN: {
        title: 'RAILMIND SYSTEM CONTROL',
        subtitle: 'Global Operations | Master Overview',
        icon: <Shield size={28} color="var(--color-primary)" />,
        kpis: ['health', 'conflicts', 'blocks', 'tasks'],
        panels: ['blocks', 'tasks'],
        quickActions: [
          { label: 'SYSTEM ANALYTICS', to: '/analytics', icon: <ActivityIcon size={18} />, primary: true },
          { label: 'OPEN AI PLANNER', to: '/planner', icon: <Zap size={18} />, primary: false },
        ]
      },
      GENERAL: {
        title: 'GENERAL OPERATIONS',
        subtitle: 'Corridor Overview',
        icon: <Map size={28} color="var(--color-primary)" />,
        kpis: ['health', 'blocks', 'tasks', 'conflicts'],
        panels: ['blocks', 'tasks'],
        quickActions: [
          { label: 'VIEW TASKS', to: '/tasks', icon: <Target size={18} />, primary: false },
        ]
      }
    };
    return roleConfigs[dashboardType];
  }, [dashboardType]);

  // Derived filtered data
  const filteredTasks = useMemo(() => {
    let tasks = data.criticalTasks || [];
    if (dashboardType === 'ENGG') {
      tasks = tasks.filter(t => t.department === 'ENGG');
    } else if (dashboardType === 'SNT') {
      tasks = tasks.filter(t => t.department === 'SNT');
    } else if (dashboardType === 'TRD') {
      tasks = tasks.filter(t => t.department === 'TRD');
    }
    // CONTROLLER, ADMIN, GENERAL see all top tasks
    return tasks;
  }, [data.criticalTasks, dashboardType]);

  const blocksCount = data.kpis?.active_blocks !== undefined ? data.kpis.active_blocks : (data.activeBlocks ? data.activeBlocks.length : 0);
  const tasksCount = data.kpis?.critical_tasks_pending !== undefined && (dashboardType === 'CONTROLLER' || dashboardType === 'ADMIN' || dashboardType === 'GENERAL') 
                     ? data.kpis.critical_tasks_pending 
                     : filteredTasks.length;
  const conflictsCount = data.kpis?.active_conflicts !== undefined ? data.kpis.active_conflicts : 0;
  const healthCount = data.kpis?.asset_availability_pct !== undefined ? data.kpis.asset_availability_pct : '--';

  const kpiComponents = {
    blocks: (
      <div key="blocks" className="card hover-lift" style={{ borderLeft: '4px solid var(--color-primary)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div className="flex-between" style={{ marginBottom: '16px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-primary)' }}>Active Blocks</div>
          <Layers size={24} color="var(--color-primary-dark)" />
        </div>
        <div className="kpi-value">{loading ? <Loader2 size={24} className="animate-spin" /> : blocksCount}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '16px', fontWeight: 600, textTransform: 'uppercase' }}>System Verified</div>
      </div>
    ),
    tasks: (
      <div key="tasks" className="card hover-lift" style={{ borderLeft: '4px solid var(--color-danger)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div className="flex-between" style={{ marginBottom: '16px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-danger-dark)' }}>{['ENGG','SNT','TRD'].includes(dashboardType) ? `${dashboardType} Tasks` : 'Critical Tasks'}</div>
          <Target size={24} color="var(--color-danger)" />
        </div>
        <div className="kpi-value" style={{ color: 'var(--color-danger-dark)' }}>
          {loading ? <Loader2 size={24} className="animate-spin" /> : tasksCount}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--color-danger-dark)', marginTop: '16px', fontWeight: 700, textTransform: 'uppercase' }}>Action Required</div>
      </div>
    ),
    conflicts: (
      <div key="conflicts" className="card hover-lift" style={{ borderLeft: '4px solid var(--color-warning)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div className="flex-between" style={{ marginBottom: '16px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-warning-dark)' }}>Safety Events</div>
          <ShieldAlert size={24} color="var(--color-warning)" />
        </div>
        <div className="kpi-value" style={{ color: 'var(--color-warning-dark)' }}>
          {loading ? <Loader2 size={24} className="animate-spin" /> : conflictsCount}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '16px', fontWeight: 600, textTransform: 'uppercase' }}>Auto-Mitigated</div>
      </div>
    ),
    health: (
      <div key="health" className="card hover-lift" style={{ borderLeft: '4px solid var(--color-success)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div className="flex-between" style={{ marginBottom: '16px' }}>
          <div className="section-heading" style={{ margin: 0, color: 'var(--color-success-dark)' }}>Network Health</div>
          <Map size={24} color="var(--color-success)" />
        </div>
        <div className="kpi-value" style={{ color: 'var(--color-success-dark)', display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          {loading ? <Loader2 size={24} className="animate-spin" /> : healthCount}<span style={{ fontSize: '1.25rem' }}>%</span>
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--color-success-dark)', marginTop: '16px', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, textTransform: 'uppercase' }}>
          <CheckCircle2 size={14} /> <span>Optimal Operations</span>
        </div>
      </div>
    )
  };

  const panelComponents = {
    blocks: (
      <div key="blocks" className="panel" style={{ flex: 1, minHeight: '350px' }}>
        <div className="panel-header flex-between">
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
            <Layers color="var(--color-primary)" size={18} /> {['ENGG','SNT','TRD'].includes(dashboardType) ? 'APPROVED MAINTENANCE WINDOWS' : 'APPROVED BLOCK PLANS'}
          </span>
          <Link to="/blocks" className="hover-lift" style={{ fontSize: '0.75rem', color: 'var(--color-primary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px', textTransform: 'uppercase' }}>
            View Register <ArrowRight size={14} />
          </Link>
        </div>
        
        <div style={{ flex: 1, backgroundColor: 'var(--color-bg-white)', display: 'flex', flexDirection: 'column' }}>
          {loading ? (
            <div className="flex-center" style={{ flex: 1, color: 'var(--color-primary)' }}><Loader2 size={32} className="animate-spin" /></div>
          ) : data.activeBlocks.length === 0 ? (
            <div className="empty-state" style={{ flex: 1 }}>
              <CheckCircle2 size={48} color="var(--color-success)" />
              <h3 style={{ color: 'var(--color-success-dark)' }}>NETWORK CLEAR</h3>
              <p>No active block operations currently requiring intervention.</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto', flex: 1 }}>
              <table className="rail-table">
                <thead>
                  <tr>
                    <th>Corridor</th>
                    <th>Date Range</th>
                    <th>Duration</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.activeBlocks.slice(0, 5).map((block) => (
                    <tr key={block.id}>
                      <td style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontFamily: 'var(--font-mono)' }}>
                        <MapPin size={14} color="var(--color-text-muted)" /> {block.section_id}
                      </td>
                      <td style={{ color: 'var(--color-text-main)', fontSize: '0.8rem' }}>{block.date_range}</td>
                      <td style={{ color: 'var(--color-text-main)', fontWeight: 600 }}>{block.total_block_hrs}h</td>
                      <td>
                        <span className={`badge ${block.status === 'APPROVED' || block.status === 'ACTIVE' ? 'badge-success' : block.status === 'REJECTED' ? 'badge-danger' : block.status === 'VALIDATED' ? 'badge-info' : 'badge-neutral'}`}>
                          {block.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    ),
    tasks: (
      <div key="tasks" className="panel" style={{ flex: 1, minHeight: '350px' }}>
        <div className="panel-header flex-between">
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
            <Target color="var(--color-danger)" size={18} /> {['ENGG','SNT','TRD'].includes(dashboardType) ? `CRITICAL ${dashboardType} TASKS` : 'CRITICAL INFRASTRUCTURE TASKS'}
          </span>
          <Link to="/tasks" className="hover-lift" style={{ fontSize: '0.75rem', color: 'var(--color-primary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px', textTransform: 'uppercase' }}>
            Maintenance Board <ArrowRight size={14} />
          </Link>
        </div>

        <div style={{ flex: 1, backgroundColor: 'var(--color-bg-white)', padding: '16px', display: 'flex', flexDirection: 'column' }}>
          {loading ? (
            <div className="flex-center" style={{ flex: 1, color: 'var(--color-danger)' }}><Loader2 size={32} className="animate-spin" /></div>
          ) : filteredTasks.length === 0 ? (
             <div className="empty-state" style={{ flex: 1 }}>
              <CheckCircle2 size={48} color="var(--color-success)" />
              <h3 style={{ color: 'var(--color-success-dark)' }}>NO CRITICAL TASKS</h3>
              <p>No high-severity maintenance interventions currently require immediate attention.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {filteredTasks.slice(0, 4).map(task => (
                <div key={task.id} className="hover-lift" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-bg-white)', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger-dark)' }}>
                      <ShieldAlert size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.9rem', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontFamily: 'var(--font-mono)' }}>
                        {task.task_code}
                        <span className="badge badge-neutral" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-sans)' }}>{task.department}</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>Due: <span style={{ color: 'var(--color-text-main)', fontWeight: 700 }}>{task.due_date}</span></div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', backgroundColor: 'var(--color-bg-subtle)', padding: '6px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: task.severity === 'CRITICAL' ? 'var(--color-danger-dark)' : 'var(--color-warning-dark)' }}>
                      {task.criticality_score ? Math.round(task.criticality_score) : 'High'}
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>AI Risk Score</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* HEADER COCKPIT */}
      <div className="animate-fade-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {config.icon}
            {config.title}
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', fontWeight: 600 }}>
            {config.subtitle}
          </p>
          <div style={{ marginTop: '8px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary)', display: 'flex', gap: '16px' }}>
             <span>ROLE: {user?.role || 'UNKNOWN'}</span>
             <span>DEPT: {user?.department || 'UNKNOWN'}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          {config.quickActions.map((action, idx) => (
            <Link 
              key={idx} 
              to={action.to} 
              className={`btn hover-lift ${action.primary ? 'btn-primary' : 'btn-outline'}`} 
              style={action.primary ? { display: 'flex', gap: '8px', boxShadow: '0 4px 14px rgba(29, 78, 216, 0.4)' } : { display: 'flex', gap: '8px' }}
            >
              {action.icon}
              {action.label}
            </Link>
          ))}
        </div>
      </div>

      {error && (
        <div className="animate-slide-up" style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', border: `1px solid rgba(239, 68, 68, 0.3)`, color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 600, borderRadius: 'var(--radius-md)' }}>
          <AlertTriangle size={20} /> {error}
        </div>
      )}

      {/* RAILWAY CORRIDOR HERO VISUALIZATION */}
      <div className="card animate-slide-up" style={{ padding: '32px 40px', backgroundColor: 'var(--color-navy)', position: 'relative', overflow: 'hidden', border: 'none', borderRadius: '16px', boxShadow: '0 10px 30px rgba(11, 17, 32, 0.5)' }}>
        
        {/* Subtle grid background for the hero map */}
        <div style={{ position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.2) 1px, transparent 1px)', backgroundSize: '40px 40px', pointerEvents: 'none' }}></div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '50px', position: 'relative', zIndex: 10 }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', margin: 0, display: 'flex', alignItems: 'center', gap: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <MapPin color="var(--color-accent-saffron)" size={24} /> CENTRAL MAIN LINE CORRIDOR
          </h2>
          <div className="badge badge-success" style={{ fontSize: '0.75rem', padding: '6px 12px', border: 'none', backgroundColor: 'rgba(5, 150, 105, 0.2)', color: '#34D399' }}>
            <Radio size={14} className="animate-pulse" /> LIVE TELEMETRY
          </div>
        </div>

        {/* Dynamic Track Map */}
        <div style={{ position: 'relative', height: '140px', display: 'flex', alignItems: 'center', padding: '0 40px', zIndex: 10 }}>
          
          {/* Main Track Line */}
          <div style={{ position: 'absolute', left: '40px', right: '40px', height: '6px', backgroundColor: 'rgba(255,255,255,0.1)', borderTop: '2px dashed rgba(255,255,255,0.2)', zIndex: 1 }}></div>
          
          {stations.map((station, idx) => (
            <div key={station} style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 3 }}>
              {/* Station Node */}
              <div style={{ width: '20px', height: '20px', backgroundColor: 'var(--color-navy)', border: '4px solid var(--color-primary-light)', borderRadius: '50%', marginBottom: '16px', boxShadow: '0 0 15px rgba(239, 246, 255, 0.5)' }}></div>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'rgba(255,255,255,0.8)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{station}</div>
            </div>
          ))}

          {/* Render Actual Trains from Backend if available */}
          {loading ? (
             <div style={{ position: 'absolute', top: '15px', width: '100%', textAlign: 'center', fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', fontWeight: 600, zIndex: 0 }}>
               FETCHING TELEMETRY...
             </div>
          ) : data.trainWindows && data.trainWindows.length > 0 ? (
            data.trainWindows.slice(0, 3).map((w, i) => (
              <div key={i} className="hover-lift" style={{ position: 'absolute', left: `${25 + (i * 20)}%`, top: '-5px', display: 'flex', flexDirection: 'column', alignItems: 'center', animation: `slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards ${i * 0.1}s`, zIndex: 4, opacity: 0, cursor: 'pointer' }}>
                <div style={{ 
                  padding: '8px 12px', backgroundColor: w.is_high_priority ? 'var(--color-danger)' : 'var(--color-primary)', 
                  color: 'white', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', fontWeight: 800, 
                  display: 'flex', gap: '8px', alignItems: 'center', boxShadow: '0 8px 16px rgba(0,0,0,0.4)',
                  letterSpacing: '0.05em'
                }}>
                  <Train size={16} /> {w.train_no || `TRN-${i+1}`}
                </div>
                <div style={{ width: '2px', height: '24px', backgroundColor: w.is_high_priority ? 'var(--color-danger)' : 'var(--color-primary)' }}></div>
              </div>
            ))
          ) : (
             <div style={{ position: 'absolute', top: '15px', width: '100%', textAlign: 'center', fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', fontWeight: 600, zIndex: 0, letterSpacing: '0.1em' }}>
               AWAITING ACTIVE TRAIN TELEMETRY
             </div>
          )}

          {/* Render Active Block if available */}
          {!loading && data.activeBlocks.length > 0 && data.activeBlocks.some(b => b.status === 'ACTIVE' || b.status === 'APPROVED') && (
            <div className="animate-pulse" style={{ position: 'absolute', left: '35%', width: '20%', height: '14px', backgroundColor: 'var(--color-warning)', borderRadius: '7px', zIndex: 2, opacity: 0.9, top: 'calc(50% - 7px)', border: '2px solid var(--color-warning-dark)', boxShadow: '0 0 15px rgba(245, 158, 11, 0.5)' }} title="Active Block Window"></div>
          )}
        </div>
      </div>

      {/* KPI METRICS (Config-driven) */}
      <div className="grid-cols-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
        {config.kpis.map((kpiKey, idx) => {
           // We clone the element to inject animation delays that cascade naturally
           const element = kpiComponents[kpiKey];
           if (!element) return null;
           return React.cloneElement(element, { style: { ...element.props.style, animationDelay: `${0.1 + (idx * 0.1)}s` } });
        })}
      </div>

      {/* DYNAMIC PANELS (Config-driven) */}
      <div className="grid-cols-2 animate-slide-up" style={{ animationDelay: '0.3s' }}>
        {config.panels.map(panelKey => panelComponents[panelKey])}
      </div>

      {/* SIH 2026 ADVANCED AI MODULES */}
      <div className="section-heading" style={{ marginTop: '24px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-primary)' }}>
        <Zap size={20} /> RAILMIND AI FORECASTING & VALIDATION
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '0.7rem', color: wsConnected ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 700 }}>
            ● WS {wsConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
          <button onClick={triggerApprovalDemo} className="btn btn-outline" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', padding: '6px 12px' }}>
            <Check size={14} /> DEMO: APPROVE PLAN
          </button>
        </div>
      </div>

      <div className="grid-cols-2 animate-slide-up" style={{ animationDelay: '0.4s' }}>
        
        {/* Goods Train Forecast Card */}
        <div className="card hover-lift" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="flex-between" style={{ marginBottom: '16px' }}>
             <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp color="var(--color-primary)" size={20} /> Goods Train Forecast
             </h3>
             <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>SYNTHETIC FORECAST</span>
          </div>
          
          <div style={{ flex: 1, minHeight: '200px' }}>
            {forecastData ? (
              <ResponsiveContainer width="100%" height={200}>
                <ComposedChart data={[
                  ...(forecastData.historical || []).map(d => ({ date: d.date.substring(5), count: d.count })),
                  ...(forecastData.forecast.predictions || []).map(d => ({ 
                    date: d.date.substring(5), 
                    forecast: d.predicted_count, 
                    range: [d.expected_lower, d.expected_upper] 
                  }))
                ]}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                  <XAxis dataKey="date" tick={{fontSize: 10}} />
                  <YAxis tick={{fontSize: 10}} />
                  <Tooltip />
                  <Area type="monotone" dataKey="range" fill="var(--color-primary-light)" stroke="none" opacity={0.3} name="Uncertainty Range" />
                  <Line type="monotone" dataKey="count" stroke="var(--color-navy)" strokeWidth={2} dot={false} name="Historical" />
                  <Line type="monotone" dataKey="forecast" stroke="var(--color-primary)" strokeWidth={2} strokeDasharray="5 5" name="Forecast" />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex-center" style={{ height: '100%', color: 'var(--color-text-muted)' }}><Loader2 className="animate-spin" /></div>
            )}
          </div>
          
          {forecastData && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>PREDICTED GOODS TRAINS</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-navy)' }}>{forecastData.forecast.summary.avg_predicted_goods_trains}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>EXPECTED RANGE</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-primary)' }}>{forecastData.forecast.summary.expected_range}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>UNCERTAINTY</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-danger)' }}>{forecastData.forecast.summary.uncertainty_level}</div>
              </div>
            </div>
          )}
        </div>

        {/* Validation & Benchmark */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Model Validation */}
          <div className="card hover-lift" style={{ flex: 1, backgroundColor: 'var(--color-navy)', color: 'white' }}>
            <div className="flex-between" style={{ marginBottom: '16px' }}>
               <h3 style={{ margin: 0, fontSize: '1rem', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ActivityIcon color="var(--color-accent-saffron)" size={20} /> Model Validation
               </h3>
               <span className="badge" style={{ fontSize: '0.65rem', backgroundColor: 'rgba(255,255,255,0.1)', color: 'white', border: 'none' }}>SYNTHETIC HOLDOUT</span>
            </div>
            
            {validationMetrics ? (
              <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', height: 'calc(100% - 40px)' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'white' }}>{validationMetrics.mae}</div>
                  <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.7)', fontWeight: 600 }}>MAE (Trains)</div>
                </div>
                <div style={{ width: '1px', height: '40px', backgroundColor: 'rgba(255,255,255,0.2)' }}></div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'white' }}>{validationMetrics.rmse}</div>
                  <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.7)', fontWeight: 600 }}>RMSE (Trains)</div>
                </div>
                <div style={{ width: '1px', height: '40px', backgroundColor: 'rgba(255,255,255,0.2)' }}></div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-accent-saffron)' }}>{validationMetrics.r2}</div>
                  <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.7)', fontWeight: 600 }}>R² Score</div>
                </div>
              </div>
            ) : (
              <div className="flex-center" style={{ height: '100%' }}><Loader2 className="animate-spin" /></div>
            )}
          </div>

          {/* Benchmark */}
          <div className="card hover-lift" style={{ flex: 1, borderLeft: '4px solid var(--color-primary)' }}>
            <div className="flex-between" style={{ marginBottom: '16px' }}>
               <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Target color="var(--color-primary)" size={20} /> Planning Performance
               </h3>
               <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>SIMULATED DEMO</span>
            </div>
            
            {benchmark ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>MANUAL PLANNING</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-text-main)' }}>{benchmark.manual_downtime_hrs} <span style={{fontSize: '0.8rem', fontWeight: 600}}>hrs</span></div>
                </div>
                <ArrowRight size={24} color="var(--color-text-muted)" />
                <div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', fontWeight: 700 }}>RAILMIND AI</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-primary)' }}>{benchmark.railmind_downtime_hrs} <span style={{fontSize: '0.8rem', fontWeight: 600}}>hrs</span></div>
                </div>
                <div style={{ backgroundColor: 'var(--color-success-bg)', padding: '12px 16px', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.65rem', color: 'var(--color-success-dark)', fontWeight: 700 }}>DOWNTIME REDUCTION</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-success-dark)' }}>{benchmark.improvement_pct}%</div>
                </div>
              </div>
            ) : (
              <div className="flex-center" style={{ height: '100%' }}><Loader2 className="animate-spin" /></div>
            )}
          </div>
        </div>
      </div>

      {/* Live Notification Toast */}
      {liveNotification && (
        <div className="animate-slide-up" style={{
          position: 'fixed', bottom: '24px', right: '24px', 
          backgroundColor: 'white', 
          borderLeft: '4px solid var(--color-success)',
          padding: '16px 24px', borderRadius: 'var(--radius-md)',
          boxShadow: '0 10px 25px rgba(0,0,0,0.15)', zIndex: 9999,
          display: 'flex', alignItems: 'center', gap: '16px'
        }}>
          <div style={{ backgroundColor: 'var(--color-success-bg)', padding: '8px', borderRadius: '50%', color: 'var(--color-success-dark)' }}>
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div style={{ fontWeight: 800, color: 'var(--color-navy)', fontSize: '0.9rem' }}>{liveNotification.title}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>{liveNotification.section}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Bell size={12} /> {liveNotification.time}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
