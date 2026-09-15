import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-logo" onClick={() => setIsOpen(false)}>
        <img src="/marketpulse-logo.svg" alt="" className="navbar-logo-icon" />
        <span><strong>Market</strong>Pulse</span>
      </NavLink>
      
      <div className="hamburger" onClick={() => setIsOpen(!isOpen)}>
        <div className={`bar ${isOpen ? 'open' : ''}`}></div>
        <div className={`bar ${isOpen ? 'open' : ''}`}></div>
        <div className={`bar ${isOpen ? 'open' : ''}`}></div>
      </div>

      <ul className={`navbar-links ${isOpen ? 'mobile-menu-open' : ''}`}>
        <li><NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''} onClick={() => setIsOpen(false)}>Overview</NavLink></li>
        <li><NavLink to="/analysis" className={({isActive}) => isActive ? 'active' : ''} onClick={() => setIsOpen(false)}>Cross-asset</NavLink></li>
        <li><NavLink to="/simulator" className={({isActive}) => isActive ? 'active' : ''} onClick={() => setIsOpen(false)}>Scenarios</NavLink></li>
        <li><NavLink to="/trade" className={({isActive}) => isActive ? 'active' : ''} onClick={() => setIsOpen(false)}>Trade lab</NavLink></li>
        <li><NavLink to="/how-it-works" className={({isActive}) => isActive ? 'active' : ''} onClick={() => setIsOpen(false)}>How it works</NavLink></li>
      </ul>
      
      <div className="navbar-meta desktop-only"><span className="market-status-dot" /> Markets open</div>
    </nav>
  );
}
