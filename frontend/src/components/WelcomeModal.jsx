import React from 'react';

const OPTIONS = [
  { key: 'dashboard', title: 'View market data', description: 'Explore asset performance, current prices and charts.', path: '/' },
  { key: 'analysis', title: 'Analyze trends', description: 'Review correlation, shock propagation and model details.', path: '/analysis' },
  { key: 'simulator', title: 'Simulate an investment', description: 'Build a trade scenario and compare expected impact across markets.', path: '/simulator' },
  { key: 'trade', title: 'Demo trading', description: 'Run a live stock trade test and see profit or loss using current market prices.', path: '/trade' },
  { key: 'education', title: 'Learn the method', description: 'Read how prices, shocks, propagation, and limitations are calculated.', path: '/how-it-works' },
];

export default function WelcomeModal({ open, onChoose }) {
  if (!open) return null;

  return (
    <div className="welcome-overlay">
      <div className="welcome-card">
        <div className="welcome-header">
          <h2>Welcome to MarketPulse</h2>
          <p>Tell us your goal so we can guide you to the right experience.</p>
        </div>

        <div className="welcome-options">
          {OPTIONS.map(option => (
            <button
              key={option.key}
              className="welcome-option"
              onClick={() => onChoose(option)}
            >
              <div>
                <div className="welcome-option-title">{option.title}</div>
                <div className="welcome-option-desc">{option.description}</div>
              </div>
              <span className="welcome-option-action">Continue</span>
            </button>
          ))}
        </div>

        <div className="welcome-footer">
          <p>
            Data is sourced from Yahoo Finance and historical calculations are for informational use only.
            Always verify with your own research before making investment decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
