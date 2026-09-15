import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, PERIODS, exportToCSV, toLocalDate } from '../utils/api';
import ModeToggle from '../components/ModeToggle';
import TerminalWindow from '../components/TerminalWindow';

const TICKER_MAP = {
  NIFTY:      '[^NSEI]',
  SP500:      '[^GSPC]',
  Nasdaq:     '[^IXIC]',
  Gold:       '[GC=F]',
  Silver:     '[SI=F]',
  Platinum:   '[PL=F]',
  BrentOil:   '[BZ=F]',
  WTICrude:   '[CL=F]',
  NaturalGas: '[NG=F]',
  Bitcoin:    '[BTC-USD]',
  Ethereum:   '[ETH-USD]',
  Copper:     '[HG=F]',
  Apple:      '[AAPL]',
  Microsoft:  '[MSFT]',
  Amazon:     '[AMZN]',
  Tesla:      '[TSLA]',
  Nvidia:     '[NVDA]',
  Meta:       '[META]',
  Alphabet:   '[GOOGL]',
  Broadcom:   '[AVGO]',
  AMD:        '[AMD]',
  Netflix:    '[NFLX]',
  JPMorgan:   '[JPM]',
  Berkshire:  '[BRK-B]',
  Reliance:   '[RELIANCE.NS]',
  HDFCBank:   '[HDFCBANK.NS]',
};

export default function Dashboard({ mode, setMode }) {
  const navigate = useNavigate();
  const today = toLocalDate();
  const oneYearAgo = toLocalDate(new Date(Date.now() - 365 * 24 * 60 * 60 * 1000));

  const getPeriodStart = (periodKey) => {
    const date = new Date();
    if (periodKey === '1d') date.setDate(date.getDate() - 1);
    if (periodKey === '5d') date.setDate(date.getDate() - 5);
    if (periodKey === '1mo') date.setMonth(date.getMonth() - 1);
    if (periodKey === '3mo') date.setMonth(date.getMonth() - 3);
    if (periodKey === '6mo') date.setMonth(date.getMonth() - 6);
    if (periodKey === '1y') date.setFullYear(date.getFullYear() - 1);
    if (periodKey === '2y') date.setFullYear(date.getFullYear() - 2);
    if (periodKey === '5y') date.setFullYear(date.getFullYear() - 5);
    if (periodKey === '10y') date.setFullYear(date.getFullYear() - 10);
    return toLocalDate(date);
  };

  const [period, setPeriod] = useState('1y');
  const [startDate, setStartDate] = useState(oneYearAgo);
  const [endDate, setEndDate] = useState(today);
  const [customRange, setCustomRange] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.summary(period, mode, startDate, endDate)
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { 
        setError(e.message || 'Failed to load market data.');
        setLoading(false);
      });
  }, [mode, period, startDate, endDate]);

  useEffect(() => {
    if (!customRange) {
      setStartDate(getPeriodStart(period));
      setEndDate(today);
    }
  }, [period, customRange, today]);

  const handleExportCSV = () => {
    if (!data?.assets?.length) {
      alert('No data to export.');
      return;
    }
    const headers = ['Asset', 'Category', 'Price', 'Change %', 'Week Change %', 'Volatility %'];
    const rows = data.assets.map(a => [
      a.name,
      a.category,
      a.price,
      a.change_pct.toFixed(2),
      a.week_change_pct.toFixed(2),
      a.volatility_pct.toFixed(2),
    ]);
    exportToCSV(`marketpulse-dashboard-${toLocalDate()}.csv`, headers, rows);
  };

  const getSystemLogic = (change) => {
    if (change > 0.2) return <span className="badge badge-green">BULL_TREND</span>;
    if (change < -0.2) return <span className="badge badge-red">BEAR_TREND</span>;
    return <span className="badge badge-blue">STABLE</span>;
  };

  return (
    <div className="page-container">
      <TerminalWindow title="~/dashboard">
        <div className="telemetry-header-row">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <span className="badge badge-green" style={{ fontWeight: 800 }}>Market overview</span>
            <span style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold' }}>Daily market moves</span>
            <ModeToggle mode={mode} setMode={setMode} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: '4px' }}>
              {PERIODS.map(p => (
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

            <button className="btn btn-primary" onClick={handleExportCSV} style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
              Export data
            </button>
          </div>
        </div>

        {error && (
          <div className="error-box" style={{ margin: '16px' }}>
            Unable to load market data: {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
            <span className="spinner-ring" style={{ display: 'inline-block', marginBottom: 12 }} />
            <div>Loading market data...</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="telemetry-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Asset Identity</th>
                  <th>Class</th>
                  <th>Latest quote</th>
                  <th>Net Delta</th>
                  <th>Ann. Volatility</th>
                  <th>System Logic</th>
                  <th>Command</th>
                </tr>
              </thead>
              <tbody>
                {(data?.assets || []).map(asset => {
                  const ticker = TICKER_MAP[asset.name] || `[${asset.name}]`;
                  const priceStr = asset.price ? `${asset.currency === 'INR' ? '₹' : '$'}${asset.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A';
                  const changeSign = asset.change_pct >= 0 ? '+' : '';
                  const changeColor = asset.change_pct >= 0 ? 'var(--green)' : 'var(--red)';
                  
                  return (
                    <tr key={asset.name}>
                      <td style={{ color: 'var(--text-secondary)' }}>{ticker}</td>
                      <td style={{ fontWeight: 'bold' }}>{asset.name}</td>
                      <td>{asset.category}</td>
                      <td style={{ fontFamily: 'Fira Code, monospace', fontWeight: 600 }}>{priceStr}</td>
                      <td style={{ color: changeColor, fontWeight: 'bold' }}>
                        {changeSign}{asset.change_pct.toFixed(2)}%
                      </td>
                      <td>
                        <span style={{ marginRight: 8 }}>{asset.volatility_pct.toFixed(2)}%</span>
                        <div className="progress-bar-container">
                          <div 
                            className="progress-bar-fill" 
                            style={{ 
                              width: `${Math.min(asset.volatility_pct, 100)}%`,
                              background: asset.volatility_pct > 30 ? 'var(--red)' : asset.volatility_pct > 15 ? 'var(--gold)' : 'var(--green)'
                            }} 
                          />
                        </div>
                      </td>
                      <td>{getSystemLogic(asset.change_pct)}</td>
                      <td>
                        <button 
                          className="btn btn-ghost" 
                          onClick={() => navigate(`/asset/${asset.name}`)}
                        >
                          Analyze
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {data?.assets?.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginTop: 24, padding: 16, background: 'var(--bg-card)', border: '1px solid var(--border-ui)' }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>TOTAL_SYSTEM_NODES</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--teal)' }}>{data.assets.length}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>BULLISH_NODES</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--green)' }}>
                {data.assets.filter(a => a.change_pct > 0.2).length}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>BEARISH_NODES</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--red)' }}>
                {data.assets.filter(a => a.change_pct < -0.2).length}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>AVERAGE_VOLATILITY</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--gold)' }}>
                {(data.assets.reduce((s, a) => s + (a.volatility_pct || 0), 0) / data.assets.length).toFixed(2)}%
              </div>
            </div>
          </div>
        )}
      </TerminalWindow>
    </div>
  );
}
