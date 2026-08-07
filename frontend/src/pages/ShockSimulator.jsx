import React, { useState } from 'react';
import { api } from '../utils/api';
import ModeToggle from '../components/ModeToggle';
import TerminalWindow from '../components/TerminalWindow';
import BarChart from '../components/charts/BarChart';

const CORE_ASSETS = ['NIFTY', 'Gold', 'Silver', 'BrentOil'];

export default function ShockSimulator({ mode, setMode }) {
  const today = new Date().toISOString().slice(0, 10);
  const oneYearAgo = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

  const [asset,       setAsset]       = useState('BrentOil');
  const [shockPct,    setShockPct]    = useState('');
  const [investAmount,setInvestAmount]= useState(1000);
  const [startDate,   setStartDate]   = useState(oneYearAgo);
  const [endDate,     setEndDate]     = useState(today);
  const [result,      setResult]      = useState(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);

  const simulate = async () => {
    if (!shockPct || isNaN(shockPct)) { setError('Enter a valid shock %'); return; }
    if (!investAmount || isNaN(investAmount) || Number(investAmount) <= 0) { setError('Enter a positive investment amount'); return; }
    if (!startDate || !endDate) { setError('Choose a valid date range'); return; }
    setError(null);
    setLoading(true);
    try {
      const data = await api.simulate(asset, parseFloat(shockPct), mode, startDate, endDate);
      setResult({ ...data, investAmount: Number(investAmount) });
    } catch (e) {
      setError('Simulation failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const impacts  = result?.impacts || [];
  const months   = impacts.map(i => i.target);
  const returns  = impacts.map(i => i.impact_pct);
  const investment = result?.investAmount || 0;
  const sourcePosition = result ? investment * (1 + result.shock_pct / 100) : 0;
  const maxImpact = impacts.reduce((m, i) => Math.max(m, Math.abs(i.impact_pct)), 0);

  return (
    <div className="page-container">
      <TerminalWindow title="~/shock-propagation-simulator">
        <div className="telemetry-header-row" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span className="badge badge-gold" style={{ fontWeight: 800 }}>SIM_OPS_NODE</span>
            <span style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold' }}>SHOCK_PROPAGATION_SIMULATOR</span>
            <ModeToggle mode={mode} setMode={setMode} />
          </div>
        </div>

        <div className="panel-card" style={{ padding: 24, marginBottom: 24 }}>
          <div style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold', borderBottom: '1px solid var(--border-ui)', paddingBottom: 8, marginBottom: 16 }}>
            :: CONFIGURE_SHOCK_SCENARIO
          </div>
          <div className="sim-form">
            <div className="form-group">
              <label className="form-label">Source Asset</label>
              <select className="form-select" value={asset} onChange={e => setAsset(e.target.value)}>
                {CORE_ASSETS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Shock Magnitude (%)</label>
              <input
                className="form-input"
                type="number"
                step="0.5"
                placeholder="e.g. +10 or -7.5"
                value={shockPct}
                onChange={e => setShockPct(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && simulate()}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Investment Amount (USD)</label>
              <input
                className="form-input"
                type="number"
                step="10"
                min="0"
                value={investAmount}
                onChange={e => setInvestAmount(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && simulate()}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input
                className="form-input"
                type="date"
                value={startDate}
                max={endDate}
                onChange={e => setStartDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">End Date</label>
              <input
                className="form-input"
                type="date"
                value={endDate}
                min={startDate}
                max={today}
                onChange={e => setEndDate(e.target.value)}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={simulate}
              disabled={loading}
              style={{ height: 'fit-content', alignSelf: 'flex-end' }}
            >
              {loading ? '[ RUNNING... ]' : '[ SIMULATE ]'}
            </button>
          </div>

          {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}

          <div style={{ marginTop: 16, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Note: output is based on historical shock propagation and does not guarantee future performance.
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className="fade-up" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold', borderBottom: '1px solid var(--border-ui)', paddingBottom: 8 }}>
              :: SIMULATION_OUTPUT_METRICS
            </div>

            <div className="panel-card" style={{ padding: 20 }}>
              <div style={{ display: 'grid', gap: 18, gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>INVESTED_CAPITAL</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>${investment.toLocaleString()}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>PROJECTED_SOURCE_VALUE</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--blue)' }}>
                    ${sourcePosition.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>SHOCK_APPLIED</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: result.shock_pct >= 0 ? 'var(--green)' : 'var(--red)' }}>
                    {result.source_asset} {result.shock_pct > 0 ? '+' : ''}{result.shock_pct}%
                  </div>
                </div>
              </div>
            </div>

            <div className="panel-card" style={{ padding: 20 }}>
              <BarChart
                months={months}
                returns={returns}
                asset={asset}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))', gap: 14 }}>
              {impacts.map(imp => {
                const isPos = imp.impact_pct >= 0;
                const strength = maxImpact ? Math.abs(imp.impact_pct) / maxImpact : 0;
                return (
                  <div key={imp.target} className="panel-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: 4 }}>
                      {imp.target}
                    </div>
                    <div style={{
                      fontSize: '1.5rem', fontWeight: 'bold',
                      color: isPos ? 'var(--green)' : 'var(--red)',
                      marginBottom: 8,
                    }}>
                      {isPos ? '+' : ''}{imp.impact_pct.toFixed(3)}%
                    </div>
                    <div className="prob-bar-bg" style={{ marginBottom: 8 }}>
                      <div className="prob-bar-fill" style={{
                        width: `${strength * 100}%`,
                        background: isPos ? 'var(--green)' : 'var(--red)',
                      }} />
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      EST. CHANGE: ${(investment * (imp.impact_pct / 100)).toFixed(2)}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="panel-card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 'bold', marginBottom: 8, fontSize: '0.85rem' }}>
                :: WHAT_THIS_SCENARIO_MEANS
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', lineHeight: 1.6 }}>
                If <strong>{result.source_asset}</strong> drops or rises by
                {' '}<strong>{Math.abs(result.shock_pct)}%</strong>, our model predicts the following
                average moves in other markets:
              </p>
              <ul style={{ marginTop: 8, paddingLeft: 20, lineHeight: 1.8, color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                {impacts.map(imp => (
                  <li key={imp.target}>
                    <strong style={{ color: imp.impact_pct >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      {imp.target}
                    </strong>
                    {' '}{imp.impact_pct >= 0 ? 'may rise' : 'may fall'} by approximately
                    {' '}<strong>{Math.abs(imp.impact_pct).toFixed(2)}%</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </TerminalWindow>
    </div>
  );
}
