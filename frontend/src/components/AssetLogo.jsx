import React from 'react';

const ASSET_LOGOS = {
  NIFTY:      { color: '#3b82f6', variant: 'trend' },
  SP500:      { color: '#6366f1', variant: 'trend' },
  Nasdaq:     { color: '#8b5cf6', variant: 'trend' },
  Gold:       { color: '#f5c518', variant: 'bar' },
  Silver:     { color: '#94a3b8', variant: 'coin' },
  Platinum:   { color: '#c4d7eb', variant: 'diamond' },
  BrentOil:   { color: '#f97316', variant: 'flame' },
  WTICrude:   { color: '#fb923c', variant: 'flame' },
  NaturalGas: { color: '#fbbf24', variant: 'flame' },
  Bitcoin:    { color: '#f59e0b', variant: 'digital' },
  Ethereum:   { color: '#a855f7', variant: 'digital' },
  Copper:     { color: '#f87171', variant: 'coil' },
  Apple:      { color: '#22c55e', variant: 'leaf' },
  Microsoft:  { color: '#3b82f6', variant: 'grid' },
  Amazon:     { color: '#f97316', variant: 'arrow' },
  Tesla:      { color: '#ef4444', variant: 'arrow' },
  Nvidia:     { color: '#10b981', variant: 'arrow' },
  Meta:       { color: '#7c3aed', variant: 'digital' },
};

function makeShape(variant, color) {
  switch (variant) {
    case 'trend':
      return (
        <>
          <path d="M14 32L20 24L28 30L34 18L40 26" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="14" cy="32" r="3.2" fill={color} />
          <circle cx="40" cy="26" r="3.2" fill={color} />
        </>
      );
    case 'bar':
      return (
        <>
          <rect x="13" y="20" width="6" height="14" rx="2" fill={color} />
          <rect x="21" y="16" width="6" height="18" rx="2" fill={color} />
          <rect x="29" y="12" width="6" height="22" rx="2" fill={color} />
        </>
      );
    case 'coin':
      return (
        <>
          <circle cx="24" cy="24" r="12" fill={color} />
          <path d="M18 24H30" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
        </>
      );
    case 'diamond':
      return (
        <path d="M24 14L34 24L24 34L14 24Z" fill={color} fillOpacity="0.95" stroke="#fff" strokeWidth="1.5" />
      );
    case 'flame':
      return (
        <path d="M24 12c-6 7-6 13-4 18 2 6 10 8 12 0 2-7 2-11-4-18z" fill={color} />
      );
    case 'digital':
      return (
        <>
          <rect x="16" y="16" width="6" height="6" rx="2" fill={color} />
          <rect x="26" y="16" width="6" height="6" rx="2" fill={color} />
          <rect x="16" y="26" width="6" height="6" rx="2" fill={color} />
          <rect x="26" y="26" width="6" height="6" rx="2" fill={color} />
        </>
      );
    case 'coil':
      return (
        <path d="M18 18c4-4 12-4 16 0s4 10 0 14c-4 4-12 4-16 0" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" />
      );
    case 'leaf':
      return (
        <path d="M22 14c-6 0-10 6-10 10s4 10 10 10 10-6 10-10-4-10-10-10z" fill={color} />
      );
    case 'grid':
      return (
        <>
          <rect x="12" y="12" width="8" height="8" rx="2" fill={color} />
          <rect x="28" y="12" width="8" height="8" rx="2" fill={color} />
          <rect x="12" y="28" width="8" height="8" rx="2" fill={color} />
          <rect x="28" y="28" width="8" height="8" rx="2" fill={color} />
        </>
      );
    case 'arrow':
      return (
        <>
          <path d="M14 30L22 18L28 26L34 16" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M14 26h8l6-8 6 12" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" />
        </>
      );
    default:
      return (
        <circle cx="24" cy="24" r="10" fill={color} />
      );
  }
}

export default function AssetLogo({ asset }) {
  const config = ASSET_LOGOS[asset] || { color: '#64748b', variant: 'trend' };
  const { color, variant } = config;

  return (
    <svg viewBox="0 0 48 48" width="40" height="40" role="img" aria-label={`${asset} logo`}>
      <rect x="4" y="4" width="40" height="40" rx="14" fill={color} fillOpacity="0.16" />
      {makeShape(variant, color)}
    </svg>
  );
}
