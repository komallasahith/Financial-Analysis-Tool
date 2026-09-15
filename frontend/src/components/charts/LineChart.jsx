import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Filler, Tooltip, Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { ASSET_COLORS } from '../../utils/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

export default function LineChart({ asset, dates = [], prices = [], normalized = false }) {
  const values = normalized
    ? prices.map((_, i) => prices[i]) // caller decides which array
    : prices;

  const color = ASSET_COLORS[asset] || '#00d4aa';

  const data = {
    labels: dates,
    datasets: [{
      label: normalized ? `${asset} (Normalized, base=100)` : `${asset} Price`,
      data: values,
      borderColor: color,
      borderWidth: 2,
      fill: false,
      tension: 0.15,
      pointRadius: 0,
      pointHoverRadius: 5,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
          backgroundColor: '#fffefa',
        borderColor: color,
        borderWidth: 1,
        titleColor: '#f0f4ff',
        bodyColor: '#8b92a5',
        padding: 12,
        callbacks: {
          label: (ctx) => ` ${ctx.parsed.y.toLocaleString()}`
        }
      },
    },
    scales: {
      x: {
        ticks: { color: '#525a6e', maxTicksLimit: 8, maxRotation: 0, font: { size: 11 } },
        grid: { color: '#e8e4da' },
      },
      y: {
        ticks: { color: '#525a6e', font: { size: 11 } },
        grid: { color: '#e8e4da' },
      },
    },
  };

  return (
    <div style={{ height: '340px', position: 'relative' }}>
      <Line data={data} options={options} />
    </div>
  );
}
