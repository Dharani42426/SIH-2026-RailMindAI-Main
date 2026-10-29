import React, { useState, useEffect } from 'react';
import { 
  Train, Calendar, Map, Activity, ShieldAlert, AlertTriangle, 
  CheckCircle2, Clock, Info, X, Route as RouteIcon, Focus,
  Compass, ShieldCheck
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const parseTimeToMinutes = (timeStr) => {
  if (!timeStr) return 0;
  const [hours, minutes] = timeStr.split(':').map(Number);
  return (hours * 60) + minutes;
};

const clamp = (val, min, max) => Math.max(min, Math.min(max, val));

const Trains = () => {
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState('');
  const [targetDate, setTargetDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [windowsData, setWindowsData] = useState(null);
  const [availableData, setAvailableData] = useState(null);
  const [trainsList, setTrainsList] = useState([]);

  const [selectedTrainId, setSelectedTrainId] = useState(null);
  const [trainDetail, setTrainDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [simBlockStart, setSimBlockStart] = useState('11:00');
  const [simBlockEnd, setSimBlockEnd] = useState('12:00');
  const [simLine, setSimLine] = useState('BOTH');
  const [conflictResult, setConflictResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  useEffect(() => {
    const fetchSections = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/sections/`);
        setSections(res.data);
        if (res.data.length > 0) setSelectedSection(res.data[0].id.toString());
      } catch (err) {
        setError("Network connection to dispatch servers offline.");
      }
    };
    fetchSections();
  }, []);

  useEffect(() => {
    if (!selectedSection || !targetDate) return;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setConflictResult(null);
      try {
        const sid = parseInt(selectedSection);
        const [winRes, availRes, trainsRes] = await Promise.all([
          axios.get(`${BACKEND_URL}/api/trains/section/${sid}/windows?target_date=${targetDate}`),
          axios.get(`${BACKEND_URL}/api/trains/section/${sid}/available?target_date=${targetDate}`),
          axios.get(`${BACKEND_URL}/api/trains/?section_id=${sid}`)
        ]);
        setWindowsData(winRes.data);
        setAvailableData(availRes.data);
        setTrainsList(trainsRes.data);
      } catch (err) {
        setError("Failed to fetch operational train schedule data.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedSection, targetDate]);

  const handleTrainClick = async (trainId) => {
    setSelectedTrainId(trainId);
    setDetailLoading(true);
    setTrainDetail(null);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/trains/${trainId}`);
      setTrainDetail(res.data);
    } catch (err) {
      setTrainDetail(trainsList.find(t => t.id === trainId));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCheckConflict = async (e) => {
    e.preventDefault();
    if (!selectedSection) return;
    setSimLoading(true);
    try {
      const sid = parseInt(selectedSection);
      const res = await axios.get(`${BACKEND_URL}/api/trains/section/${sid}/conflicts`, {
        params: { block_date: targetDate, block_start: simBlockStart, block_end: simBlockEnd, line: simLine }
      });
      setConflictResult(res.data);
    } catch (err) {
      alert("Failed to run safety simulation.");
    } finally {
      setSimLoading(false);
    }
  };

  const TL_START = 10 * 60; // 600 mins
  const TL_END = 16 * 60;   // 960 mins
  const TL_SPAN = TL_END - TL_START;

  const calculateTimelinePos = (startStr, endStr) => {
    const s = parseTimeToMinutes(startStr);
    const e = parseTimeToMinutes(endStr);
    if (e <= TL_START || s >= TL_END) return null;
    const clampedStart = clamp(s, TL_START, TL_END);
    const clampedEnd = clamp(e, TL_START, TL_END);
    const leftPct = ((clampedStart - TL_START) / TL_SPAN) * 100;
    const widthPct = ((clampedEnd - clampedStart) / TL_SPAN) * 100;
    return { left: `${leftPct}%`, width: `${widthPct}%` };
  };

  const activeSectionObj = sections.find(s => s.id.toString() === selectedSection);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px', minHeight: '100%', position: 'relative' }}>
      
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">
            <Train size={32} color="var(--color-primary)" /> TIMETABLE & DISPATCH
          </h1>
          <p style={{ color: 'var(--color-text-muted)', margin: '8px 0 0 0', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <RouteIcon size={16} /> Live Section Occupancy & Maintenance Windows
          </p>
        </div>
      </div>

      {/* CONTROL BAR */}
      <div className="card" style={{ padding: '20px 24px', display: 'flex', gap: '32px', alignItems: 'center', flexWrap: 'wrap' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontWeight: 800, letterSpacing: '0.05em' }}>
            <Map size={20} color="var(--color-primary)" /> ACTIVE CORRIDOR
          </div>
          <select className="input-rail" value={selectedSection} onChange={(e) => setSelectedSection(e.target.value)} style={{ width: '300px', fontWeight: 700 }}>
            {sections.map(sec => (
              <option key={sec.id} value={sec.id}>{sec.section_code} — {sec.section_name}</option>
            ))}
          </select>
        </div>

        <div style={{ width: '1px', height: '32px', backgroundColor: 'var(--color-border)' }}></div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)', fontWeight: 800, letterSpacing: '0.05em' }}>
            <Calendar size={20} color="var(--color-primary)" /> DISPATCH DATE
          </div>
          <input type="date" className="input-rail" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} style={{ width: '200px', fontWeight: 700 }} />
        </div>
        
        {loading && (
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-primary)', fontWeight: 700, fontSize: '0.875rem' }}>
            <Activity className="animate-spin" size={18} /> SYNCING TELEMETRY...
          </div>
        )}
      </div>

      {error && (
        <div style={{ padding: '16px 24px', backgroundColor: 'var(--color-danger-bg)', border: '1px solid var(--color-danger)', color: 'var(--color-danger-dark)', display: 'flex', alignItems: 'center', gap: '12px', fontWeight: 700, borderRadius: 'var(--radius-md)' }}>
          <AlertTriangle size={24} /> {error}
        </div>
      )}

      {/* KPIs */}
      {!error && selectedSection && (
        <div className="grid-cols-4 animate-slide-up">
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-navy)' }}>
            <div className="section-heading" style={{ color: 'var(--color-navy)' }}>Total Trains</div>
            <div className="kpi-value">{windowsData ? windowsData.total_trains : '-'}</div>
          </div>
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-warning-dark)' }}>
            <div className="section-heading" style={{ color: 'var(--color-warning-dark)' }}>High Priority / SF</div>
            <div className="kpi-value" style={{ color: 'var(--color-warning-dark)' }}>{windowsData ? windowsData.high_priority_trains : '-'}</div>
          </div>
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-success-dark)' }}>
            <div className="section-heading" style={{ color: 'var(--color-success-dark)' }}>Available Free Blocks</div>
            <div className="kpi-value" style={{ color: 'var(--color-success-dark)' }}>{availableData ? availableData.available_windows : '-'}</div>
          </div>
          <div className="card hover-lift" style={{ borderLeft: '4px solid var(--color-primary)', backgroundColor: 'var(--color-bg-subtle)' }}>
            <div className="section-heading" style={{ color: 'var(--color-primary)' }}>Standard Block Window</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
              <Clock size={24} color="var(--color-primary)" /> 10:00 - 16:00
            </div>
          </div>
        </div>
      )}

      {/* OPERATIONAL TIMELINE */}
      {!error && selectedSection && windowsData && availableData && (
        <div className="card animate-slide-up" style={{ padding: '32px' }}>
          <div className="flex-between" style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
              <Focus color="var(--color-primary)" /> SECTION TRACK OCCUPANCY
            </h3>
            <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', fontWeight: 700 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-warning)', borderRadius: '2px' }}></div> SF / EXPRESS</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-primary)', borderRadius: '2px' }}></div> STANDARD</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-success-bg)', border: '1px solid var(--color-success)', borderRadius: '2px' }}></div> FREE BLOCK</span>
            </div>
          </div>
          
          <div style={{ position: 'relative', width: '100%', minWidth: '800px', backgroundColor: 'var(--color-bg-subtle)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '40px 0', overflow: 'hidden' }}>
            
            {/* Context Header */}
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, backgroundColor: 'var(--color-bg-white)', borderBottom: '1px solid var(--color-border)', padding: '12px 24px', fontSize: '0.875rem', fontWeight: 800, letterSpacing: '0.05em', color: 'var(--color-navy)', display: 'flex', justifyContent: 'space-between', zIndex: 10, boxShadow: 'var(--shadow-sm)' }}>
              <span>{activeSectionObj?.section_code} CORRIDOR</span>
              <span style={{ color: 'var(--color-text-muted)' }}>{targetDate}</span>
            </div>

            {/* Timeline Axis */}
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid var(--color-border-dark)', padding: '16px 24px 8px 24px', color: 'var(--color-navy)', fontSize: '0.875rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
              <span>10:00</span><span>11:00</span><span>12:00</span><span>13:00</span><span>14:00</span><span>15:00</span><span>16:00</span>
            </div>

            {/* Grid lines */}
            <div style={{ position: 'absolute', top: '90px', bottom: 0, left: '24px', right: '24px', display: 'flex', justifyContent: 'space-between', zIndex: 0, pointerEvents: 'none' }}>
              {[...Array(7)].map((_, i) => (
                <div key={i} style={{ width: '1px', backgroundColor: 'var(--color-border)', height: '100%' }}></div>
              ))}
            </div>

            <div style={{ position: 'relative', margin: '0 24px' }}>
              {/* TRAIN ROW */}
              <div style={{ position: 'relative', height: '100px', marginTop: '24px', borderBottom: '1px dashed var(--color-border-dark)', zIndex: 2 }}>
                <div style={{ position: 'absolute', left: 0, top: '-20px', fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.1em', color: 'var(--color-text-muted)' }}>LIVE TRAIN MOVEMENT</div>
                
                {windowsData.trains.map((train, idx) => {
                  const pos = calculateTimelinePos(train.entry_time, train.exit_time);
                  if (!pos) return null;
                  
                  return (
                    <div 
                      key={`${train.train_no}-${idx}`}
                      onClick={() => handleTrainClick(train.train_id)}
                      style={{
                        position: 'absolute', left: pos.left, width: pos.width,
                        top: `${(idx % 3) * 32}px`, height: '24px',
                        backgroundColor: train.is_high_priority ? 'var(--color-warning)' : 'var(--color-primary)',
                        borderRadius: '4px', border: '1px solid rgba(0,0,0,0.1)',
                        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        overflow: 'hidden', whiteSpace: 'nowrap', color: 'white',
                        fontSize: '0.75rem', fontWeight: 800, fontFamily: 'var(--font-mono)',
                        boxShadow: 'var(--shadow-sm)', transition: 'all 0.2s', zIndex: 10
                      }}
                      className="hover-lift"
                      title={`${train.train_no} - ${train.train_name}`}
                    >
                      {train.train_no}
                    </div>
                  );
                })}
              </div>

              {/* WINDOW ROW */}
              <div style={{ position: 'relative', height: '60px', marginTop: '24px', zIndex: 1 }}>
                <div style={{ position: 'absolute', left: 0, top: '-20px', fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.1em', color: 'var(--color-success-dark)' }}>COMPUTED FREE BLOCKS</div>
                
                {availableData.windows.map((win, idx) => {
                  const pos = calculateTimelinePos(win.start_time, win.end_time);
                  if (!pos) return null;
                  
                  return (
                    <div 
                      key={idx}
                      style={{
                        position: 'absolute', left: pos.left, width: pos.width,
                        top: '0', height: '40px',
                        backgroundColor: 'var(--color-success-bg)',
                        border: '2px solid var(--color-success)', borderRadius: '4px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'var(--color-success-dark)', fontSize: '0.875rem', fontWeight: 800,
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      {win.duration_min} MIN
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      )}

      {/* LOWER SECTION */}
      {!error && selectedSection && (
        <div className="grid-cols-2 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          
          {/* SIMULATOR */}
          <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="panel-header">
              <ShieldAlert color="var(--color-warning-dark)" size={20} /> AUTHORITATIVE SAFETY SIMULATOR
            </div>
            <div style={{ padding: '24px', flex: 1, backgroundColor: 'var(--color-bg-white)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 24px 0', lineHeight: 1.6, fontWeight: 500 }}>
                Simulate a proposed maintenance block against the live dispatch schedule to verify safety compliance.
              </p>

              <form onSubmit={handleCheckConflict} style={{ display: 'flex', flexDirection: 'column', gap: '16px', backgroundColor: 'var(--color-bg-subtle)', padding: '24px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', textTransform: 'uppercase' }}>Start (HH:MM)</label>
                    <input type="time" className="input-rail" style={{ width: '100%', marginTop: '8px', fontWeight: 700 }} value={simBlockStart} onChange={e=>setSimBlockStart(e.target.value)} required />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', textTransform: 'uppercase' }}>End (HH:MM)</label>
                    <input type="time" className="input-rail" style={{ width: '100%', marginTop: '8px', fontWeight: 700 }} value={simBlockEnd} onChange={e=>setSimBlockEnd(e.target.value)} required />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-navy)', textTransform: 'uppercase' }}>Line</label>
                    <select className="input-rail" style={{ width: '100%', marginTop: '8px', fontWeight: 700 }} value={simLine} onChange={e=>setSimLine(e.target.value)}>
                      <option value="BOTH">BOTH (BLOCK)</option>
                      <option value="UP">UP LINE</option>
                      <option value="DN">DN LINE</option>
                    </select>
                  </div>
                </div>
                <button type="submit" className="btn btn-primary" style={{ marginTop: '8px', justifyContent: 'center', padding: '16px', fontWeight: 700, fontSize: '1rem' }} disabled={simLoading}>
                  {simLoading ? <Activity className="animate-spin" size={20} /> : <ShieldCheck size={20} />}
                  EXECUTE SAFETY SIMULATION
                </button>
              </form>

              {conflictResult && (
                <div className="animate-fade-in" style={{ marginTop: '24px', padding: '24px', borderRadius: 'var(--radius-md)', border: `2px solid ${conflictResult.has_conflicts ? 'var(--color-danger)' : 'var(--color-success)'}`, backgroundColor: conflictResult.has_conflicts ? 'var(--color-danger-bg)' : 'var(--color-success-bg)' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: conflictResult.has_conflicts ? 'var(--color-danger-dark)' : 'var(--color-success-dark)', display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase' }}>
                    {conflictResult.has_conflicts ? <AlertTriangle size={24} /> : <CheckCircle2 size={24} />}
                    {conflictResult.has_conflicts ? 'CRITICAL CONFLICT DETECTED' : 'WINDOW VALIDATED SAFE'}
                  </div>
                  
                  {conflictResult.has_conflicts && (
                    <div style={{ marginTop: '16px', fontSize: '0.875rem' }}>
                      <div style={{ display: 'flex', gap: '24px', marginBottom: '16px', fontWeight: 700 }}>
                        <span style={{ color: 'var(--color-navy)' }}>Total Overlaps: <span style={{ color: 'var(--color-danger-dark)', fontSize: '1.125rem' }}>{conflictResult.total_conflicts}</span></span>
                      </div>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {conflictResult.conflicts.map((c, i) => (
                          <div key={i} style={{ backgroundColor: 'var(--color-bg-white)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', borderLeft: `4px solid ${c.is_high_priority ? 'var(--color-danger)' : 'var(--color-warning)'}` }}>
                            <div style={{ fontWeight: 800, fontSize: '1rem', marginBottom: '4px', color: 'var(--color-navy)' }}>{c.train_no} ({c.train_name})</div>
                            <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', fontWeight: 500 }}>{c.reason}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* TRAIN DISPATCH LIST */}
          <div className="panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div className="panel-header">
              <Compass color="var(--color-primary)" size={20} /> DISPATCH MANIFEST
            </div>
            
            <div style={{ overflowY: 'auto', flex: 1, backgroundColor: 'var(--color-bg-white)' }}>
              <table className="rail-table">
                <thead>
                  <tr>
                    <th style={{ paddingLeft: '32px' }}>Train Identity</th>
                    <th>Entry (In)</th>
                    <th>Exit (Out)</th>
                    <th style={{ paddingRight: '32px' }}>Direction</th>
                  </tr>
                </thead>
                <tbody>
                  {trainsList.map(t => (
                    <tr key={t.id} onClick={() => handleTrainClick(t.id)} style={{ cursor: 'pointer' }}>
                      <td style={{ paddingLeft: '32px' }}>
                        <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-navy)' }}>
                          {t.train_no}
                          {t.is_high_priority && <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-warning)' }} title="High Priority"></div>}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '4px', fontWeight: 600 }}>{t.train_name}</div>
                      </td>
                      <td style={{ fontWeight: 700, color: 'var(--color-text-main)' }}>{t.entry_time}</td>
                      <td style={{ fontWeight: 700, color: 'var(--color-text-main)' }}>{t.exit_time}</td>
                      <td style={{ paddingRight: '32px' }}><span className="badge badge-neutral" style={{ fontWeight: 700 }}>{t.direction}</span></td>
                    </tr>
                  ))}
                  {trainsList.length === 0 && (
                    <tr>
                      <td colSpan="4" style={{ padding: '40px 0', textAlign: 'center', color: 'var(--color-text-muted)', fontWeight: 600 }}>No train telemetry available.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TRAIN DETAIL DRAWER */}
      {selectedTrainId && (
        <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(4px)', zIndex: 100, display: 'flex', justifyContent: 'flex-end' }}>
          
          <div className="animate-fade-in" style={{ width: '450px', backgroundColor: 'var(--color-bg-main)', borderLeft: '1px solid var(--color-border)', height: '100%', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg-white)', boxShadow: 'var(--shadow-sm)' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-navy)' }}>
                <Train color="var(--color-primary)" /> TRAIN MANIFEST
              </h2>
              <button onClick={() => setSelectedTrainId(null)} className="hover-lift" style={{ padding: '8px', backgroundColor: 'var(--color-bg-subtle)', borderRadius: '50%' }}><X size={20} /></button>
            </div>

            <div style={{ padding: '32px', overflowY: 'auto', flex: 1 }}>
              {detailLoading ? (
                <div className="flex-center" style={{ height: '100%', color: 'var(--color-primary)' }}><Activity className="animate-spin" size={32} /></div>
              ) : trainDetail ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                  
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <span className={`badge ${trainDetail.is_high_priority ? 'badge-warning' : 'badge-primary'}`} style={{ fontSize: '0.875rem' }}>PRIORITY {trainDetail.priority}</span>
                    <span className="badge badge-neutral" style={{ fontSize: '0.875rem' }}>{trainDetail.train_type}</span>
                    <span className="badge badge-neutral" style={{ fontSize: '0.875rem' }}>{trainDetail.direction} BOUND</span>
                  </div>

                  <div>
                    <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Locomotive Identity</h3>
                    <div className="card" style={{ padding: 0 }}>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}><span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>Train No.</span><span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{trainDetail.train_no}</span></div>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}><span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>Train Name</span><span style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{trainDetail.train_name}</span></div>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>Operating Days</span><span style={{ fontWeight: 700, color: 'var(--color-navy)' }}>{trainDetail.days_of_run}</span></div>
                    </div>
                  </div>

                  <div>
                    <h3 className="section-heading" style={{ color: 'var(--color-navy)' }}>Corridor Timing</h3>
                    <div className="card" style={{ padding: 0 }}>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}><span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>Entry (KM {trainDetail.entry_km})</span><span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{trainDetail.entry_time}</span></div>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}><span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>Exit (KM {trainDetail.exit_km})</span><span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-navy)' }}>{trainDetail.exit_time}</span></div>
                      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', backgroundColor: 'var(--color-bg-subtle)' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>Avg Historical Delay</span>
                        <span style={{ fontWeight: 800, color: trainDetail.avg_delay_min > 10 ? 'var(--color-warning-dark)' : 'var(--color-success-dark)' }}>{trainDetail.avg_delay_min} MIN</span>
                      </div>
                    </div>
                  </div>

                  {trainDetail.is_special && (
                     <div style={{ backgroundColor: 'var(--color-primary-light)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-primary)', display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-primary)' }}>
                       <Info size={24} /> <span style={{ fontWeight: 800, fontSize: '0.875rem' }}>SPECIAL SERVICE DESIGNATION</span>
                     </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--color-danger)', fontWeight: 600 }}>Telemetry not found.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trains;
