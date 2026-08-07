import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { ASSET_COLORS } from '../../utils/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

export default function AreaChart({ asset, dates = [], normalized = [] }) {
  const color = ASSET_COLORS[asset] || '#00d4aa';

  const data = {
    labels: dates,
    datasets: [{
      label: `${asset} (Base=100)`,
      data: normalized,
      borderColor: color,
      backgroundColor: (ctx) => {
        const chart = ctx.chart;
        const { ctx: canvasCtx, chartArea } = chart;
        if (!chartArea) return `${color}10`;
        const gradient = canvasCtx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        gradient.addColorStop(0, `${color}55`);
        gradient.addColorStop(1, `${color}05`);
        return gradient;
      },
      fill: 'origin',
      borderWidth: 2.5,
      tension: 0.4,
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
        backgroundColor: 'rgba(13,18,36,0.95)',
        borderColor: color,
        borderWidth: 1,
        titleColor: '#f0f4ff',
        bodyColor: '#8b92a5',
        padding: 12,
        callbacks: {
          label: ctx => ` ${ctx.parsed.y.toFixed(2)} (base 100)`,
        }
      },
    },
    scales: {
      x: {
        ticks: { color: '#525a6e', maxTicksLimit: 8, font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        ticks: { color: '#525a6e', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
    },
  };

  return (
    <div style={{ height: '340px', position: 'relative' }}>
      <Line data={data} options={options} />
    </div>
  );
}
