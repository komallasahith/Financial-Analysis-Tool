import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-logo">
        <img src="/marketpulse-logo.svg" alt="" className="navbar-logo-icon" />
        <span><strong>Market</strong>Pulse</span>
      </NavLink>

      <ul className="navbar-links">
        <li><NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''}>Overview</NavLink></li>
        <li><NavLink to="/analysis" className={({isActive}) => isActive ? 'active' : ''}>Cross-asset</NavLink></li>
        <li><NavLink to="/simulator" className={({isActive}) => isActive ? 'active' : ''}>Scenarios</NavLink></li>
        <li><NavLink to="/trade" className={({isActive}) => isActive ? 'active' : ''}>Trade lab</NavLink></li>
        <li><NavLink to="/how-it-works" className={({isActive}) => isActive ? 'active' : ''}>How it works</NavLink></li>
      </ul>
      <div className="navbar-meta"><span className="market-status-dot" /> Markets open</div>
    </nav>
  );
}
