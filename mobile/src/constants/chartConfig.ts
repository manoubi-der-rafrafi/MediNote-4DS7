// WEB-ONLY: This component uses React DOM. It cannot be used in React Native.
// It is part of the separate web delegate SPA (src/App.tsx entry point).
import { ChartOptions } from 'chart.js';

export const C = {
  brand: '#2E7D4F',
  brand2: '#13452B',
  soft: '#86BC9B',
  pos: '#4A7C59',
  neg: '#B94A48',
  warn: '#B8860B',
  grey: '#B5B4AF',
} as const;

export const chartOpts: ChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 500,
    easing: 'easeOutQuart',
  },
  plugins: {
    legend: {
      labels: {
        font: { size: 10 },
        boxWidth: 8,
        usePointStyle: true,
        color: '#6b6b68',
      },
    },
    tooltip: {
      backgroundColor: '#1a1a1a',
      padding: 10,
      cornerRadius: 8,
      titleFont: { size: 11 },
      bodyFont: { size: 10 },
    },
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(0,0,0,0.04)',
        drawBorder: false,
      },
      ticks: {
        font: { size: 10 },
        color: '#6b6b68',
      },
    },
    y: {
      grid: {
        color: 'rgba(0,0,0,0.04)',
        drawBorder: false,
      },
      ticks: {
        font: { size: 10 },
        color: '#6b6b68',
      },
    },
  },
};

export const doughnutOpts: ChartOptions = {
  ...chartOpts,
  scales: {},
};
