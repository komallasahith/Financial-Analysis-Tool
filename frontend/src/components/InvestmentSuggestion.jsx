import React from 'react';

export default function InvestmentSuggestion({ data }) {
  if (!data) return null;
  const { suggestion } = data;
  if (!suggestion) return null;

  const { risk_level, trend, action, score, text, probability_positive } = suggestion;

  const riskClass = risk_level?.toLowerCase() || 'medium';

  const scoreColor =
    score >= 65 ? 'var(--teal)' :
    score >= 40 ? 'var(--gold)' :
    'var(--red)';

  return (
    <div className={`suggestion-card ${riskClass}`}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
        <div style={{ width: 24, height: 24, borderRadius: 6, background: 'rgba(12, 65, 103, 0.1)' }} />
        <h3 style={{ fontFamily: 'Outfit', fontSize: '1rem', fontWeight: 700 }}>
          Investment Insight
        </h3>
        <span
          className="badge"
          style={{
            background: riskClass === 'low' ? 'rgba(0,212,170,0.15)' :
                        riskClass === 'medium' ? 'rgba(245,197,24,0.15)' :
                        'rgba(255,77,77,0.15)',
            color: riskClass === 'low' ? 'var(--teal)' :
                   riskClass === 'medium' ? 'var(--gold)' : 'var(--red)',
          }}
        >
          {risk_level} Risk
        </span>
      </div>

      {/* Score + metrics row */}
      <div className="suggestion-score">
        <div className="score-ring" style={{ color: scoreColor }}>
          {score}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Opportunity Score (0–100)
          </div>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>TREND</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{trend}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>POSITIVE DAYS</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: scoreColor }}>{probability_positive}%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Probability bar */}
      <div className="prob-meter">
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>Probability of Positive Return</span>
          <span>{probability_positive}%</span>
        </div>
        <div className="prob-bar-bg">
          <div
            className="prob-bar-fill"
            style={{
              width: `${probability_positive}%`,
              background: scoreColor,
            }}
          />
        </div>
      </div>

      {/* Suggestion text */}
      <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
        {text}
      </p>

      {/* Action call-out */}
      <div style={{
        padding: '10px 16px',
        borderRadius: '8px',
        background: 'rgba(12, 65, 103, 0.08)',
        fontWeight: 600,
        fontSize: '0.85rem',
        color: 'var(--text-primary)',
      }}>
        {action}
      </div>
    </div>
  );
}
