// Central API config
const BASE = (process.env.REACT_APP_API_BASE || 'http://127.0.0.1:5000/api').replace(/\/$/, '');

export const toLocalDate = (date = new Date()) => {
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 10);
};

const get = (path) => fetch(`${BASE}${path}`).then(r => {
  if (!r.ok) throw new Error(`API error: ${r.status} ${r.statusText}`);
  return r.json();
});
const post = (path, body) =>
  fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => {
    if (!r.ok) throw new Error(`API error: ${r.status} ${r.statusText}`);
    return r.json();
  });

const buildQuery = (params) =>
  Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join('&');

const getWithParams = (path, params) => get(`${path}?${buildQuery(params)}`);

export const api = {
  categories:     () => get('/categories'),
  summary:        (period = '1y', mode = 'historical', start, end) => getWithParams('/summary', { period, mode, start, end }),
  priceHistory:   (asset, period = '1y', mode = 'historical', start, end) => getWithParams('/price-history', { asset, period, mode, start, end }),
  ohlc:           (asset, period = '1y', mode = 'historical', start, end) => getWithParams('/ohlc', { asset, period, mode, start, end }),
  monthlyReturns: (asset, period = '2y', mode = 'historical', start, end) => getWithParams('/monthly-returns', { asset, period, mode, start, end }),
  scatter:        (asset, period = '1y', mode = 'historical', start, end) => getWithParams('/scatter', { asset, period, mode, start, end }),
  radar:          (assets, period = '1y', mode = 'historical', start, end) => getWithParams('/radar', { assets, period, mode, start, end }),
  probability:    (asset, period = '1y', mode = 'historical', window = 60, start, end) => getWithParams('/probability', { asset, period, mode, window, start, end }),
  shocks:         (period = '1y', threshold = 0.06, mode = 'historical', start, end, detection_mode = 'fixed_pct') => getWithParams('/shocks', { period, threshold, mode, start, end, detection_mode }),
  propagation:    (period = '1y', threshold = 0.06, mode = 'historical', start, end, detection_mode = 'fixed_pct') => getWithParams('/propagation', { period, threshold, mode, start, end, detection_mode }),
  simulate:       (asset, shock_pct, mode = 'historical', start, end, threshold = 0.06, detection_mode = 'fixed_pct') => post('/simulate', { asset, shock_pct, mode, start, end, threshold, detection_mode }),
  verify:         (asset) => getWithParams('/verify', { asset }),
  algorithms:     () => get('/algorithms'),
  dataQuality:    (period = '1y', mode = 'historical', start, end) => getWithParams('/data-quality', { period, mode, start, end }),
};

export const PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y'];

export const ASSET_COLORS = {
  NIFTY:      '#3b82f6',
  SP500:      '#6366f1',
  Nasdaq:     '#8b5cf6',
  Gold:       '#f5c518',
  Silver:     '#94a3b8',
  Platinum:   '#e2e8f0',
  BrentOil:   '#f97316',
  WTICrude:   '#fb923c',
  NaturalGas: '#fbbf24',
  Bitcoin:    '#f59e0b',
  Ethereum:   '#a855f7',
  Copper:     '#f87171',
  Alphabet:   '#4285f4',
  Broadcom:   '#d97706',
  AMD:        '#dc2626',
  Netflix:    '#b91c1c',
  JPMorgan:   '#1d4ed8',
  Berkshire:  '#475569',
  Reliance:   '#0f766e',
  HDFCBank:   '#1e40af',
};

export const formatPrice = (p, decimals = 2) => {
  if (p == null) return '—';
  if (p >= 1000) return p.toLocaleString('en-US', { maximumFractionDigits: 2 });
  return Number(p).toFixed(decimals);
};

export const formatPct = (v) => {
  if (v == null) return '—';
  const sign = v >= 0 ? '+' : '';
  return `${sign}${Number(v).toFixed(2)}%`;
};

export const exportToCSV = (filename, headers, rows) => {
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => {
      if (cell == null) return '';
      if (typeof cell === 'string') return `"${cell.replace(/"/g, '""')}"`;
      return String(cell);
    }).join(','))
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
