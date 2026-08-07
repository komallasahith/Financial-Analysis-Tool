import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const COLORS = [
  '#f5c518','#00d4aa','#3b82f6','#a855f7','#f97316',
  '#f87171','#6366f1','#fbbf24','#fb923c','#94a3b8','#8b5cf6','#e2e8f0',
];

export default function RadarChart({ assets = [] }) {
  if (!assets.length) return null;

  // Normalize each metric 0–100
  const normalize = (arr) => {
    const min = Math.min(...arr), max = Math.max(...arr);
    if (max === min) return arr.map(() => 50);
    return arr.map(v => ((v - min) / (max - min)) * 100);
  };

  const annReturns  = normalize(assets.map(a => a.annualized_return  ?? 0));
  const totReturns  = normalize(assets.map(a => a.total_return       ?? 0));
  const probs       = normalize(assets.map(a => a.probability_positive ?? 50));
  // inverse volatility so lower vol = higher score
  const invVol      = normalize(assets.map(a => -(a.volatility ?? 0)));

  const labels = ['Ann. Return', 'Total Return', 'Low Volatility', '% Positive Days'];

  const datasets = assets.slice(0, 6).map((a, i) => ({
    label: a.asset,
    data: [annReturns[i], totReturns[i], invVol[i], probs[i]],
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: `${COLORS[i % COLORS.length]}20`,
    borderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 6,
  }));

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#8b92a5', font: { size: 12 }, padding: 16, boxWidth: 12 },
      },
      tooltip: {
        backgroundColor: 'rgba(13,18,36,0.95)',
        titleColor: '#f0f4ff',
        bodyColor: '#8b92a5',
        padding: 12,
      },
    },
    scales: {
      r: {
        angleLines: { color: 'rgba(255,255,255,0.07)' },
        grid: { color: 'rgba(255,255,255,0.07)' },
        pointLabels: { color: '#8b92a5', font: { size: 12 } },
        ticks: { display: false, backdropColor: 'transparent' },
        suggestedMin: 0,
        suggestedMax: 100,
      },
    },
  };

  return (
    <div style={{ height: '380px', position: 'relative' }}>
      <Radar data={{ labels, datasets }} options={options} />
    </div>
  );
}
