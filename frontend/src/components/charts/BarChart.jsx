import React from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function BarChart({ months = [], returns = [], asset }) {
  const colors = returns.map(v => v >= 0 ? 'rgba(0,212,170,0.75)' : 'rgba(255,77,77,0.75)');
  const borders = returns.map(v => v >= 0 ? '#00d4aa' : '#ff4d4d');

  const data = {
    labels: months,
    datasets: [{
      label: 'Monthly Return (%)',
      data: returns,
      backgroundColor: colors,
      borderColor: borders,
      borderWidth: 1,
      borderRadius: 5,
      borderSkipped: false,
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
        titleColor: '#f0f4ff',
        bodyColor: '#8b92a5',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: ctx => {
            const v = ctx.parsed.y;
            return ` ${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
          },
          borderColor: ctx => ctx.parsed.y >= 0 ? '#00d4aa' : '#ff4d4d',
        }
      },
    },
    scales: {
      x: {
        ticks: { color: '#525a6e', maxRotation: 45, font: { size: 11 } },
        grid: { display: false },
      },
      y: {
        ticks: { color: '#525a6e', font: { size: 11 }, callback: v => `${v}%` },
        grid: { color: 'rgba(255,255,255,0.04)' },
        border: { dash: [4, 4] },
      },
    },
  };

  return (
    <div style={{ height: '340px', position: 'relative' }}>
      <Bar data={data} options={options} />
    </div>
  );
}
