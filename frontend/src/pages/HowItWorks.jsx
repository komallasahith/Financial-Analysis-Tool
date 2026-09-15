import React, { useEffect, useState } from 'react';
import TerminalWindow from '../components/TerminalWindow';
import { api } from '../utils/api';

const STEPS = [
  {
    number: '01',
    title: 'Collect prices',
    text: 'MarketPulse retrieves adjusted historical prices from Yahoo Finance and keeps each asset on its own trading calendar. Missing observations are handled without dropping every date shared by the full universe.',
  },
  {
    number: '02',
    title: 'Build features',
    text: 'The pipeline calculates daily returns, rolling annualized volatility, and normalized price series. These features make assets with very different price scales comparable.',
  },
  {
    number: '03',
    title: 'Detect shocks',
    text: 'You can use a fixed percentage threshold or volatility-normalized z-scores. A shock is recorded with its date, asset, direction, and return magnitude.',
  },
  {
    number: '04',
    title: 'Measure propagation',
    text: 'For each shock, the model checks the following trading days and measures average movement in the other core assets. Incomplete future windows are excluded from the comparison.',
  },
  {
    number: '05',
    title: 'Explore scenarios',
    text: 'The scenario lab scales observed historical relationships to a user-selected shock. Results are illustrative historical relationships, not forecasts or trading signals.',
  },
];

export default function HowItWorks() {
  const [algorithms, setAlgorithms] = useState(null);

  useEffect(() => {
    api.algorithms().then(setAlgorithms).catch(() => setAlgorithms(null));
  }, []);

  return (
    <div className="page-container">
      <TerminalWindow title="~/how-it-works">
        <div className="education-intro">
          <div>
            <span className="badge badge-blue">Research notes</span>
            <h1>How MarketPulse works</h1>
            <p>
              A plain-language guide to the data, calculations, and limits behind the dashboard.
            </p>
          </div>
          <div className="education-disclaimer">
            <strong>Educational use only</strong>
            <span>MarketPulse is not investment advice. Its outputs are illustrative and have not been validated for live trading.</span>
          </div>
        </div>

        <section className="education-section" aria-labelledby="pipeline-heading">
          <div className="education-section-heading">
            <span className="section-kicker">The pipeline</span>
            <h2 id="pipeline-heading">From market prices to readable signals</h2>
          </div>
          <div className="method-step-grid">
            {STEPS.map(step => (
              <article className="method-step" key={step.number}>
                <span className="method-step-number">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="education-section" aria-labelledby="algorithms-heading">
          <div className="education-section-heading">
            <span className="section-kicker">Methods</span>
            <h2 id="algorithms-heading">Algorithms used in the app</h2>
          </div>
          <div className="algorithm-list">
            {(algorithms?.algorithms || []).map((algorithm, index) => (
              <article className="algorithm-row" key={algorithm.name}>
                <span className="algorithm-index">{String(index + 1).padStart(2, '0')}</span>
                <div>
                  <h3>{algorithm.name}</h3>
                  <p>{algorithm.description}</p>
                </div>
              </article>
            ))}
            {!algorithms && <p className="empty-methods">Algorithm notes are loading from the API.</p>}
          </div>
          <p className="method-source">Primary data source: {algorithms?.data_source || 'Yahoo Finance'}. {algorithms?.notes || 'Prices reflect actual trading sessions and market holidays.'}</p>
        </section>

        <section className="education-section" aria-labelledby="calculations-heading">
          <div className="education-section-heading">
            <span className="section-kicker">Calculations</span>
            <h2 id="calculations-heading">What each number means</h2>
          </div>
          <div className="calculation-list">
            <div><strong>Daily return</strong><code>(close today / close yesterday) - 1</code><p>Used for movement, probability, shock detection, and propagation analysis.</p></div>
            <div><strong>Annualized volatility</strong><code>std(daily returns, 30-day window) x sqrt(252)</code><p>The rolling standard deviation is scaled to an approximate trading year.</p></div>
            <div><strong>Normalized price</strong><code>close / first close x 100</code><p>Every series starts at 100 so relative performance can be compared visually.</p></div>
            <div><strong>Z-score shock</strong><code>daily return / rolling standard deviation</code><p>The default rolling window is 60 observations with a minimum of 20; the default alert level is 3 standard deviations.</p></div>
            <div><strong>Propagation impact</strong><code>mean(target returns during the next 3 trading rows)</code><p>The shock day itself is excluded, and a partial future window is not included.</p></div>
            <div><strong>Scenario scaling</strong><code>historical impact x requested shock / median detected shock</code><p>The baseline is derived from detected shocks in the selected dataset, not a fixed 6% assumption.</p></div>
          </div>
        </section>

        <section className="education-section limitations-section" aria-labelledby="limits-heading">
          <div className="education-section-heading">
            <span className="section-kicker">Read responsibly</span>
            <h2 id="limits-heading">What the numbers do not mean</h2>
          </div>
          <div className="limits-grid">
            <div><strong>Not a prediction</strong><p>Historical propagation does not establish that the same relationship will hold next time.</p></div>
            <div><strong>Not a recommendation</strong><p>Scores and scenarios do not tell you what to buy, sell, or hold.</p></div>
            <div><strong>Not a live trading model</strong><p>There is no guarantee of execution, liquidity, completeness, or future performance.</p></div>
          </div>
        </section>
      </TerminalWindow>
    </div>
  );
}
