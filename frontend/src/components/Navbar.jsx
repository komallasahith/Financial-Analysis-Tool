import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-logo">
        <img src="/marketpulse-logo.svg" alt="MarketPulse logo" className="navbar-logo-icon" />
        <span>MarketPulse</span>
      </NavLink>

      <ul className="navbar-links">
        <li><NavLink to="/"          className={({isActive}) => isActive ? 'active' : ''}>Dashboard</NavLink></li>
        <li><NavLink to="/analysis"  className={({isActive}) => isActive ? 'active' : ''}>Analysis</NavLink></li>
        <li><NavLink to="/simulator" className={({isActive}) => isActive ? 'active' : ''}>Simulator</NavLink></li>
        <li><NavLink to="/trade"     className={({isActive}) => isActive ? 'active' : ''}>Demo Trade</NavLink></li>
      </ul>
    </nav>
  );
}
