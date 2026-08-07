import React from 'react';
import {
  Chart as ChartJS, LinearScale, PointElement, Tooltip, Legend
} from 'chart.js';
import { Scatter } from 'react-chartjs-2';
import { ASSET_COLORS } from '../../utils/api';

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

export default function ScatterChart({ asset, points = [] }) {
  const color = ASSET_COLORS[asset] || '#00d4aa';

  const data = {
    datasets: [{
      label: `${asset} — Volatility vs Daily Return`,
      data: points,
      backgroundColor: `${color}60`,
      borderColor: color,
      borderWidth: 1,
      pointRadius: 4,
      pointHoverRadius: 7,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(13,18,36,0.95)',
        titleColor: '#f0f4ff',
        bodyColor: '#8b92a5',
        borderColor: color,
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: ctx => `  Vol: ${ctx.parsed.x.toFixed(2)}%  Ret: ${ctx.parsed.y >= 0 ? '+' : ''}${ctx.parsed.y.toFixed(2)}%`,
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: '20-Day Rolling Volatility (%)',
          color: '#525a6e',
          font: { size: 12 },
        },
        ticks: { color: '#525a6e', font: { size: 11 }, callback: v => `${v}%` },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        title: {
          display: true,
          text: 'Daily Return (%)',
          color: '#525a6e',
          font: { size: 12 },
        },
        ticks: { color: '#525a6e', font: { size: 11 }, callback: v => `${v}%` },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
    },
  };

  return (
    <div style={{ height: '340px', position: 'relative' }}>
      <Scatter data={data} options={options} />
    </div>
  );
}
