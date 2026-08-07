import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ASSET_COLORS, formatPrice, formatPct } from '../utils/api';
import AssetLogo from './AssetLogo';

// Tiny inline sparkline using SVG
function Sparkline({ data = [] }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const W = 100, H = 36;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = H - ((v - min) / range) * H;
    return `${x},${y}`;
  }).join(' ');

  const rising = data[data.length - 1] >= data[0];
  const colour = rising ? '#00d4aa' : '#ff4d4d';

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="40" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={colour} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export default function AssetCard({ asset }) {
  const navigate = useNavigate();
  const accentColor = ASSET_COLORS[asset.name] || '#00d4aa';
  const isPos = asset.change_pct >= 0;

  return (
    <div
      className="panel-card asset-card fade-up"
      style={{ '--accent-color': accentColor }}
      onClick={() => navigate(`/asset/${asset.name}`)}
    >
      <div className="asset-card-header">
        <div>
          <div className="asset-icon-wrap" style={{ background: `${accentColor}18` }}>
            <AssetLogo asset={asset.name} />
          </div>
        </div>
        <span
          className="badge"
          style={{
            background: isPos ? 'rgba(0,212,170,0.12)' : 'rgba(255,77,77,0.12)',
            color: isPos ? '#00d4aa' : '#ff4d4d',
          }}
        >
          {formatPct(asset.change_pct)}
        </span>
      </div>

      <div className="asset-name">{asset.name}</div>
      <div className="asset-ticker">{asset.ticker}</div>

      <div className="asset-price" style={{ color: accentColor }}>
        {formatPrice(asset.price)}
      </div>

      <div className={`asset-change ${isPos ? 'change-pos' : 'change-neg'}`}>
        {isPos ? '▲' : '▼'} {Math.abs(asset.week_change_pct).toFixed(2)}% this week
      </div>

      <div className="sparkline-wrap">
        <Sparkline data={asset.sparkline} />
      </div>

      <div className="asset-vol">Vol: {asset.volatility_pct}% ann.</div>
    </div>
  );
}
