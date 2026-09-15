import React from 'react';
import ReactApexChart from 'react-apexcharts';

export default function CandlestickChart({ asset, candles = [] }) {
  // color kept for future use, passed via theme palette

  const series = [{ data: candles }];

  const options = {
    chart: {
      type: 'candlestick',
      background: 'transparent',
      toolbar: { show: false },
      animations: { enabled: true, speed: 400 },
    },
    title: { text: '' },
    xaxis: {
      type: 'datetime',
      labels: { style: { colors: '#525a6e', fontSize: '11px' } },
      axisBorder: { color: 'rgba(0,0,0,0.1)' },
      axisTicks: { color: 'rgba(0,0,0,0.1)' },
    },
    yaxis: {
      tooltip: { enabled: true },
      labels: {
        style: { colors: '#525a6e', fontSize: '11px' },
        formatter: v => v?.toLocaleString() || v,
      },
    },
    grid: {
      borderColor: 'rgba(0,0,0,0.05)',
      strokeDashArray: 4,
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward:   '#00d4aa',
          downward: '#ff4d4d',
        },
        wick: { useFillColor: true },
      },
    },
    tooltip: {
      theme: 'light',
      style: { fontSize: '12px' },
    },
  };

  return (
    <div style={{ height: '360px' }}>
      <ReactApexChart
        type="candlestick"
        series={series}
        options={options}
        height={360}
      />
    </div>
  );
}
