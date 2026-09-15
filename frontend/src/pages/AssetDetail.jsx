import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, PERIODS, ASSET_COLORS, formatPrice, formatPct, toLocalDate } from '../utils/api';
import ModeToggle from '../components/ModeToggle';
import InvestmentSuggestion from '../components/InvestmentSuggestion';
import AssetLogo from '../components/AssetLogo';
import TerminalWindow from '../components/TerminalWindow';
import LineChart from '../components/charts/LineChart';
import BarChart from '../components/charts/BarChart';
import AreaChart from '../components/charts/AreaChart';
import CandlestickChart from '../components/charts/CandlestickChart';
import ScatterChart from '../components/charts/ScatterChart';
import RadarChart from '../components/charts/RadarChart';

const CHART_TYPES = [
  { id: 'line',        label: 'Line',        desc: 'Price history over time' },
  { id: 'bar',         label: 'Bar',         desc: 'Monthly returns' },
  { id: 'area',        label: 'Area',        desc: 'Cumulative performance' },
  { id: 'candlestick', label: 'Candles',    desc: 'OHLC detail' },
  { id: 'scatter',     label: 'Scatter',     desc: 'Volatility vs Return' },
  { id: 'radar',       label: 'Radar',      desc: 'Multi-metric comparison' },
];

export default function AssetDetail({ mode, setMode }) {
  const { name } = useParams();
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
  const [chartType, setChartType] = useState('line');

  const [priceData,   setPriceData]   = useState(null);
  const [barData,     setBarData]     = useState(null);
  const [ohlcData,    setOhlcData]    = useState(null);
  const [scatterData, setScatterData] = useState(null);
  const [radarData,   setRadarData]   = useState(null);
  const [probData,    setProbData]    = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);

  const color = ASSET_COLORS[name] || '#00d4aa';

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.assetDetail(name, period, mode, startDate, endDate)
      .then((data) => {
        setPriceData(data.price_history);
        setBarData(data.monthly_returns);
        setOhlcData(data.ohlc);
        setScatterData(data.scatter);
        setRadarData(data.radar);
        setProbData(data.probability);
        setLoading(false);
      })
      .catch((e) => {
        setError(e?.message || 'Failed to load asset analytics.');
        setLoading(false);
      });
  }, [name, mode, period, startDate, endDate]);

  useEffect(() => {
    if (!customRange) {
      setStartDate(getPeriodStart(period));
      setEndDate(today);
    }
  }, [period, customRange, today]);

  const renderChart = () => {
    if (loading) return <div className="loading-spinner"><div className="spinner-ring" /><span>Loading chart data…</span></div>;

    switch (chartType) {
      case 'line':
        return <LineChart asset={name} dates={priceData?.dates || []} prices={priceData?.prices || []} />;
      case 'bar':
        return <BarChart asset={name} months={barData?.months || []} returns={barData?.returns || []} />;
      case 'area':
        return <AreaChart asset={name} dates={priceData?.dates || []} normalized={priceData?.normalized || []} />;
      case 'candlestick':
        return <CandlestickChart asset={name} candles={ohlcData?.candles || []} />;
      case 'scatter':
        return <ScatterChart asset={name} points={scatterData?.points || []} />;
      case 'radar':
        return <RadarChart assets={radarData?.assets || []} />;
      default:
        return null;
    }
  };

  return (
    <div className="page-container">
      <button className="btn btn-ghost" style={{ marginBottom: 16 }} onClick={() => navigate('/')}>
        ← Back to Dashboard
      </button>

      <TerminalWindow title={`~/asset-detail // name: ${name.toLowerCase()}`}>
        {/* Hero */}
        <div className="detail-hero fade-up">
          <div className="detail-icon-big" style={{ background: `${color}18`, borderColor: color, border: '1px solid' }}>
            <AssetLogo asset={name} />
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: 8 }}>
              {name}
            </h2>
            <div className="detail-meta">
              {priceData && (
                <>
                  <span className="detail-price-big" style={{ color }}>
                    {priceData.currency === 'INR' ? '₹' : '$'}{formatPrice(priceData.current_price)}
                  </span>
                  <span
                    className="badge"
                    style={{
                      background: priceData.total_return_pct >= 0 ? 'var(--green-dim)' : 'var(--red-dim)',
                      color: priceData.total_return_pct >= 0 ? 'var(--green)' : 'var(--red)',
                      fontSize: '0.82rem', padding: '4px 10px',
                    }}
                  >
                    {formatPct(priceData.total_return_pct)} total ({period})
                  </span>
                </>
              )}
            </div>
            <div className="detail-meta" style={{ marginTop: 8, fontSize: '0.78rem' }}>
              <span>Period: <b>{customRange ? 'Custom' : period}</b></span>
              <span>•</span>
              <span>Mode: <b>{mode}</b></span>
              {priceData?.last_updated && <span>• Updated: {priceData.last_updated}</span>}
            </div>
          </div>
        </div>

        {/* Controls row */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', marginBottom: 20, marginTop: 16 }}>
          <ModeToggle mode={mode} setMode={setMode} />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {PERIODS.map(p => (
              <button key={p} className={`chart-tab ${period === p ? 'active' : ''}`} onClick={() => { setPeriod(p); setCustomRange(false); }}>
                {p}
              </button>
            ))}
          </div>
          <div className="date-range-group" style={{ marginLeft: 'auto' }}>
            <label>
              From
              <input type="date" value={startDate} max={endDate} onChange={e => { setStartDate(e.target.value); setCustomRange(true); }} />
            </label>
            <label>
              To
              <input type="date" value={endDate} min={startDate} max={today} onChange={e => { setEndDate(e.target.value); setCustomRange(true); }} />
            </label>
          </div>
        </div>

        {/* Chart type selector */}
        <div className="chart-tabs" style={{ marginBottom: 8 }}>
          {CHART_TYPES.map(ct => (
            <button
              key={ct.id}
              className={`chart-tab ${chartType === ct.id ? 'active' : ''}`}
              onClick={() => setChartType(ct.id)}
              title={ct.desc}
            >
              {ct.label}
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="chart-wrapper">
          {renderChart()}
        </div>

        {error && (
          <div className="error-box" style={{ marginTop: 16, marginBottom: 24 }}>
            Unable to load asset data: {error}
          </div>
        )}

        {/* Stats row */}
        {priceData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20, marginTop: 24 }}>
            <div className="content-section-title">
              Asset statistics
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))', gap: 12 }}>
            {[
              { label: 'Start Price',    value: `${priceData.currency === 'INR' ? '₹' : '$'}${formatPrice(priceData.start_price)}` },
              { label: 'Current Price',  value: `${priceData.currency === 'INR' ? '₹' : '$'}${formatPrice(priceData.current_price)}`, highlight: true },
              { label: 'Total Return',   value: formatPct(priceData.total_return_pct) },
              { label: 'Win Days %',     value: probData ? `${probData.probability_positive_pct}%` : '—' },
              { label: 'Annualized Vol', value: probData ? `${probData.annualized_volatility_pct}%` : '—' },
              { label: '30-day Trend',   value: probData ? formatPct(probData.trend_30d_pct) : '—' },
            ].map(s => (
              <div key={s.label} className="panel-card" style={{ padding: '14px' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' }}>
                  {s.label}
                </div>
                <div style={{
                  fontSize: '1.2rem', fontWeight: 700,
                  color: s.highlight ? color : 'var(--text-primary)',
                }}>
                  {s.value}
                </div>
              </div>
            ))}
            </div>
          </div>
        )}

        {/* Investment Suggestion */}
        {probData && <InvestmentSuggestion data={probData} />}

        {/* Win/Loss days bar */}
        {probData && (
          <div className="panel-card" style={{ padding: 20, marginTop: 20 }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12 }}>
              Win vs loss days (last {probData.window_days} days)
            </h3>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8 }}>
              <div style={{ flex: probData.win_days, height: 10, borderRadius: '4px 0 0 4px', background: 'var(--green)' }} />
              <div style={{ flex: probData.loss_days, height: 10, borderRadius: '0 4px 4px 0', background: 'var(--red)' }} />
            </div>
            <div style={{ display: 'flex', gap: 20, fontSize: '0.78rem' }}>
              <span style={{ color: 'var(--green)', fontWeight: 600 }}>
                {probData.win_days} winning days
              </span>
              <span style={{ color: 'var(--red)', fontWeight: 600 }}>
                {probData.loss_days} losing days
              </span>
            </div>
          </div>
        )}
      </TerminalWindow>
    </div>
  );
}
