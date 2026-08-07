import React from 'react';

export default function ModeToggle({ mode, setMode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>DATA:</span>
      <div className="mode-toggle">
        <button
          className={`mode-btn ${mode === 'historical' ? 'active-hist' : ''}`}
          onClick={() => setMode('historical')}
        >
          Historical
        </button>
        <button
          className={`mode-btn ${mode === 'live' ? 'active-live' : ''}`}
          onClick={() => setMode('live')}
        >
          <span className="live-dot" /> Live
        </button>
      </div>
      {mode === 'live' && (
        <span style={{ fontSize: '0.75rem', color: 'var(--red)', fontWeight: 600 }}>
          Fetching fresh from market
        </span>
      )}
      {mode === 'historical' && (
        <span style={{ fontSize: '0.75rem', color: '#3b82f6', fontWeight: 600 }}>
          Using cached data (max 24h)
        </span>
      )}
    </div>
  );
}
