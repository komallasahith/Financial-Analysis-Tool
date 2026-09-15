import React, { useState, useEffect } from 'react';
import { api, toLocalDate } from '../utils/api';
import ModeToggle from '../components/ModeToggle';
import TerminalWindow from '../components/TerminalWindow';
import RadarChart from '../components/charts/RadarChart';
import BarChart from '../components/charts/BarChart';

function HeatmapCell({ value }) {
  const abs = Math.abs(value);
  const intensity = Math.min(abs / 0.3, 1);  // normalise to 0-1
  const bg = value > 0
    ? `rgba(8,153,129,${0.05 + intensity * 0.6})`
    : value < 0
    ? `rgba(242,54,69,${0.05 + intensity * 0.6})`
    : 'rgba(255,255,255,0.04)';
  const fg = value > 0 ? 'var(--green)' : value < 0 ? 'var(--red)' : 'var(--text-muted)';

  return (
    <div className="heatmap-cell" style={{ background: bg, color: fg }}>
      {value !== 0 ? `${value > 0 ? '+' : ''}${value.toFixed(2)}%` : '—'}
    </div>
  );
}

export default function Analysis({ mode, setMode }) {
  const today = toLocalDate();
  const PERIOD_LABELS = {
    '3mo': 'Last 3 months',
    '6mo': 'Last 6 months',
    '1y':  'Last year',
    '2y':  'Last 2 years',
  };

  const getPeriodStart = (periodKey) => {
    const date = new Date();
    if (periodKey === '3mo') date.setMonth(date.getMonth() - 3);
    if (periodKey === '6mo') date.setMonth(date.getMonth() - 6);
    if (periodKey === '1y') date.setFullYear(date.getFullYear() - 1);
    if (periodKey === '2y') date.setFullYear(date.getFullYear() - 2);
    return toLocalDate(date);
  };

  const [period, setPeriod] = useState('1y');
  const [startDate, setStartDate] = useState(getPeriodStart('1y'));
  const [endDate, setEndDate] = useState(today);
  const [customRange, setCustomRange] = useState(false);
  const periodLabel = customRange ? 'Custom range' : PERIOD_LABELS[period] || 'Selected period';
  const rangeSummary = `${startDate} — ${endDate}`;

  const [propagation, setPropagation] = useState(null);
  const [shocks, setShocks] = useState(null);
  const [radar, setRadar] = useState(null);
  const [algorithms, setAlgorithms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.propagation(period, 0.06, mode, startDate, endDate),
      api.shocks(period, 0.06, mode, startDate, endDate),
      api.radar('', period, mode, startDate, endDate),
      api.algorithms(),
    ]).then(([prop, sh, rad, alg]) => {
      setPropagation(prop);
      setShocks(sh);
      setRadar(rad);
      setAlgorithms(alg.algorithms || []);
      setLoading(false);
    }).catch((e) => {
      setError(e?.message || 'Failed to run cross-asset analysis.');
      setLoading(false);
    });
  }, [mode, period, startDate, endDate]);

  useEffect(() => {
    if (!customRange) {
      setStartDate(getPeriodStart(period));
      setEndDate(today);
    }
  }, [period, customRange, today]);

  // Asset shock frequency for bar chart
  const shockAssets = React.useMemo(() => ['NIFTY', 'Gold', 'Silver', 'BrentOil'], []);
  const shockCounts = React.useMemo(() => shockAssets.map(a =>
    (shocks?.shocks || []).filter(s => s.Asset === a).length
  ), [shocks, shockAssets]);

  const assets = React.useMemo(() => propagation?.assets || [], [propagation]);
  const matrix = React.useMemo(() => propagation?.heatmap_matrix || {}, [propagation]);

  return (
    <div className="page-container">
      <TerminalWindow title="~/system-analysis">
        <div className="telemetry-header-row" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <span className="badge badge-blue" style={{ fontWeight: 800 }}>Cross-asset view</span>
            <span style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold' }}>Relationships and shocks</span>
            <ModeToggle mode={mode} setMode={setMode} />
          </div>

          <div style={{ display: 'flex', gap: '4px' }}>
            {['3mo','6mo','1y','2y'].map(p => (
              <button
                key={p}
                className={`chart-tab ${period === p ? 'active' : ''}`}
                onClick={() => { setPeriod(p); setCustomRange(false); }}
                style={{ padding: '4px 8px', fontSize: '0.72rem' }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 24 }}>
          <div className="section-card">
            <div className="range-chip" style={{ marginBottom: 8 }}>{periodLabel}</div>
            <h3 style={{ fontSize: '1rem', marginBottom: 6 }}>{rangeSummary}</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
              Pulls actual market data for the selected window and aligns it to real trading sessions.
            </p>
          </div>
          <div className="section-card">
            <div className="range-chip" style={{ marginBottom: 8 }}>Data source</div>
            <h3 style={{ fontSize: '1rem', marginBottom: 6 }}>Yahoo Finance</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
              Price series are sourced with automatic range handling for the chosen dates.
            </p>
          </div>
          <div className="section-card">
            <div className="range-chip" style={{ marginBottom: 8 }}>How it works</div>
            <h3 style={{ fontSize: '1rem', marginBottom: 6 }}>Signal-driven analytics</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
              Shocks are detected, propagation is measured, and comparison model ranks volatility, return, and win probability.
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
            <span className="spinner-ring" style={{ display: 'inline-block', marginBottom: 12 }} />
            <div>Preparing cross-asset analysis...</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {error && (
              <div className="error-box">
                Unable to load analysis: {error}
              </div>
            )}

            {/* Propagation Heatmap */}
            <div>
              <div className="content-section-title">
                Shock propagation map
              </div>
              <div className="panel-card" style={{ padding: 20 }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                  Average impact on target asset (columns) after a shock in source asset (rows).
                  Green = positive delta, Red = negative delta.
                </p>
                {assets.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 6 }}>
                      <thead>
                        <tr>
                          <th style={{ padding: '8px', textAlign: 'left', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            Source / Target
                          </th>
                          {assets.map(a => (
                            <th key={a} style={{ padding: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: 'bold' }}>{a}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {assets.map(src => (
                          <tr key={src}>
                            <td style={{ padding: '8px', fontWeight: 'bold', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{src}</td>
                            {assets.map(tgt => (
                              <td key={tgt} style={{ padding: 2 }}>
                                {src === tgt
                                  ? <div className="heatmap-cell" style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-muted)', textAlign: 'center', padding: '10px 8px', borderRadius: '3px', fontSize: '0.75rem' }}>self</div>
                                  : <HeatmapCell value={matrix[src]?.[tgt] ?? 0} />
                                }
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', padding: 20 }}>No propagation data available for the chosen range.</div>
                )}
              </div>
            </div>

            {/* Shock Frequency */}
            <div>
              <div className="content-section-title">
                Shock frequency by asset ({shocks?.total_shocks || 0} detected)
              </div>
              <div className="panel-card" style={{ padding: 20 }}>
                <BarChart
                  months={shockAssets}
                  returns={shockCounts}
                  asset="Shocks"
                />
              </div>
            </div>

            {/* Radar - All assets comparison */}
            <div>
              <div className="content-section-title">
                Multi-asset comparison
              </div>
              <div className="panel-card" style={{ padding: 20 }}>
                <RadarChart assets={(radar?.assets || []).slice(0, 6)} />
              </div>
            </div>

            {/* Algorithm details */}
            <div>
              <div className="content-section-title">
                Methods used
              </div>
              <div className="algo-grid">
                {algorithms.map(algo => (
                  <div key={algo.name} className="algo-card">
                    <div style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-primary)', marginBottom: 6 }}>{algo.name}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', lineHeight: 1.5 }}>{algo.description}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Shocks Table */}
            {shocks?.shocks?.length > 0 && (
              <div>
                <div className="content-section-title">
                  Recent shock events
                </div>
                <div className="panel-card" style={{ overflowX: 'auto' }}>
                  <table className="telemetry-table" style={{ marginTop: 0 }}>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Asset</th>
                        <th>Return %</th>
                        <th>Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shocks.shocks.slice(0, 15).map((s, i) => (
                        <tr key={i}>
                          <td style={{ color: 'var(--text-secondary)' }}>{String(s.Date).slice(0,10)}</td>
                          <td style={{ fontWeight: 'bold' }}>{s.Asset}</td>
                          <td style={{ color: s.Return > 0 ? 'var(--green)' : 'var(--red)', fontWeight: 'bold' }}>
                            {s.Return > 0 ? '+' : ''}{(s.Return * 100).toFixed(2)}%
                          </td>
                          <td>
                            <span className={s.Shock_Type === 'Positive' ? 'badge badge-green' : 'badge badge-red'}>
                              {s.Shock_Type === 'Positive' ? '▲' : '▼'} {s.Shock_Type}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {shocks.shocks.length > 15 && (
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 12, fontSize: '0.75rem' }}>
                      Showing 15 of {shocks.shocks.length} shock events
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </TerminalWindow>
    </div>
  );
}
