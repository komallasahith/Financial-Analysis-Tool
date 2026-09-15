import React, { useState } from 'react';
import ModeToggle from '../components/ModeToggle';
import TerminalWindow from '../components/TerminalWindow';
import { api, formatPrice, formatPct, toLocalDate } from '../utils/api';

const STOCK_ASSETS = [
  { name: 'Apple',    ticker: 'AAPL', desc: 'Consumer tech leader' },
  { name: 'Microsoft',ticker: 'MSFT', desc: 'Cloud and productivity' },
  { name: 'Amazon',   ticker: 'AMZN', desc: 'E-commerce and cloud' },
  { name: 'Tesla',    ticker: 'TSLA', desc: 'EV and energy innovator' },
  { name: 'Nvidia',   ticker: 'NVDA', desc: 'AI chip powerhouse' },
  { name: 'Meta',     ticker: 'META', desc: 'Social media and metaverse' },
];

export default function TradeDemo({ mode, setMode }) {
  const today = toLocalDate();
  const defaultBuyDate = toLocalDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000));

  const [asset, setAsset] = useState('Apple');
  const [investment, setInvestment] = useState(1000);
  const [buyDate, setBuyDate] = useState(defaultBuyDate);
  const [result, setResult] = useState(null);
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const assetTicker = STOCK_ASSETS.find(a => a.name === asset)?.ticker || asset;

  const runDemo = async () => {
    if (!investment || Number(investment) <= 0) {
      setError('Enter a positive investment amount.');
      return;
    }
    if (!buyDate) {
      setError('Select a buy date before running the demo.');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    setQuote(null);

    try {
      const history = await api.priceHistory(asset, '1y', mode, buyDate, today);
      if (history.error) {
        throw new Error(history.error);
      }
      const verified = await api.verify(asset);
      if (!verified || verified.error) {
        setQuote(null);
      } else {
        setQuote(verified);
      }

      const startPrice = history.start_price;
      const currentPrice = history.current_price;
      const shares = investment / startPrice;
      const currentValue = shares * currentPrice;
      const profitLoss = currentValue - investment;
      const profitPct = investment ? (profitLoss / investment) * 100 : 0;

      setResult({
        asset,
        ticker: assetTicker,
        requestedBuyDate: buyDate,
        buyDate: history.dates?.[0] || buyDate,
        startPrice,
        currentPrice,
        shares,
        currentValue,
        profitLoss,
        profitPct,
      });
    } catch (e) {
      setError('Demo failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const gain = result?.profitLoss >= 0;

  return (
    <div className="page-container">
      <TerminalWindow title="~/demo-trading">
        <div className="telemetry-header-row" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span className="badge badge-green" style={{ fontWeight: 800 }}>Trade lab</span>
            <span style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold' }}>Historical position check</span>
            <ModeToggle mode={mode} setMode={setMode} />
          </div>
        </div>

        <div className="trade-page">
          {/* Order entry router right-side column */}
          <div className="trade-card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold', borderBottom: '1px solid var(--border-ui)', paddingBottom: 8 }}>
              Position setup
            </div>

            <div className="form-group">
              <label className="form-label">Asset</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                {STOCK_ASSETS.map(stock => (
                  <button
                    key={stock.name}
                    type="button"
                    className={`btn ${asset === stock.name ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setAsset(stock.name)}
                    style={{ fontSize: '0.75rem', padding: '6px' }}
                  >
                    [{stock.ticker}] {stock.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Entry date</label>
              <input
                className="form-input"
                type="date"
                max={today}
                value={buyDate}
                onChange={e => setBuyDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Capital allocation (USD)</label>
              <input
                className="form-input"
                type="number"
                min="10"
                step="10"
                value={investment}
                onChange={e => setInvestment(Number(e.target.value))}
              />
            </div>

            <button 
              className="btn btn-primary" 
              onClick={runDemo} 
              disabled={loading}
              style={{ width: '100%', padding: '12px' }}
            >
              {loading ? 'Running...' : 'Run position check'}
            </button>

            {error && <div className="error-box" style={{ fontSize: '0.8rem' }}>{error}</div>}

            {result && (
              <div style={{ marginTop: 12, padding: 12, border: '1px solid var(--border-ui)', background: 'var(--bg-card)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Net position result</div>
                <div style={{ fontSize: '1.65rem', fontWeight: 'bold', color: gain ? 'var(--green)' : 'var(--red)', marginTop: 4 }}>
                  {gain ? '+' : ''}${formatPrice(result.profitLoss)}
                </div>
                <div style={{ fontSize: '0.9rem', color: gain ? 'var(--green)' : 'var(--red)', fontWeight: 'bold' }}>
                  {formatPct(result.profitPct)}
                </div>
              </div>
            )}
          </div>

          {/* Results column on the left */}
          <div className="trade-card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ color: 'var(--terminal-green)', fontSize: '0.85rem', fontWeight: 'bold', borderBottom: '1px solid var(--border-ui)', paddingBottom: 8 }}>
              Position report
            </div>

            {!result && !loading && (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Choose an asset and run the position check for {assetTicker}.
              </div>
            )}

            {loading && (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
                <span className="spinner-ring" style={{ display: 'inline-block', marginBottom: 12 }} />
                <div>Loading historical prices...</div>
              </div>
            )}

            {result && (
              <div>
                <table className="telemetry-table" style={{ marginTop: 0 }}>
                  <thead>
                    <tr>
                      <th>Parameter</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Ticker</td>
                      <td style={{ fontWeight: 'bold' }}>[{result.ticker}]</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Requested_Date</td>
                      <td>{result.requestedBuyDate}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Actual_Date</td>
                      <td>{result.buyDate}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Entry_Price</td>
                      <td style={{ fontFamily: 'Fira Code' }}>${formatPrice(result.startPrice)}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Current_Price</td>
                      <td style={{ fontFamily: 'Fira Code' }}>${formatPrice(result.currentPrice)}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Shares_Allocated</td>
                      <td>{result.shares.toFixed(4)}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--text-secondary)' }}>Current_Valuation</td>
                      <td style={{ fontFamily: 'Fira Code', fontWeight: 'bold' }}>${formatPrice(result.currentValue)}</td>
                    </tr>
                  </tbody>
                </table>

                {quote && (
                  <div style={{ marginTop: 24, padding: 12, background: 'var(--bg-card)', border: '1px solid var(--border-ui)', fontSize: '0.78rem' }}>
                    <div style={{ color: 'var(--text-secondary)', fontWeight: 'bold', marginBottom: 8 }}>Latest quote</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>LIVE_PRICE:</span>{' '}
                        <span style={{ fontWeight: 'bold' }}>${formatPrice(quote.current_price)}</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>PREV_CLOSE:</span>{' '}
                        <span style={{ fontWeight: 'bold' }}>${formatPrice(quote.previous_close)}</span>
                      </div>
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: 8 }}>
                      QUOTE_LAST_UPDATED: {quote.last_updated}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </TerminalWindow>
    </div>
  );
}
