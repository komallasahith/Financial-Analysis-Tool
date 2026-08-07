import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import './index.css';
import './App.css';
import Navbar from './components/Navbar';
import WelcomeModal from './components/WelcomeModal';
import Dashboard from './pages/Dashboard';
import AssetDetail from './pages/AssetDetail';
import Analysis from './pages/Analysis';
import ShockSimulator from './pages/ShockSimulator';
import TradeDemo from './pages/TradeDemo';

function AppRouter() {
  const navigate = useNavigate();
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const [mode, setMode] = useState('historical');

  useEffect(() => {
    const storedIntent = window.localStorage.getItem('marketpulse-intent');
    if (!storedIntent) {
      setWelcomeOpen(true);
    }
  }, []);

  const handleChoose = (option) => {
    window.localStorage.setItem('marketpulse-intent', option.key);
    setWelcomeOpen(false);
    navigate(option.path);
  };

  return (
    <>
      <div className="app-bg" />
      <Navbar mode={mode} setMode={setMode} />
      <WelcomeModal open={welcomeOpen} onChoose={handleChoose} />
      <Routes>
        <Route path="/" element={<Dashboard mode={mode} setMode={setMode} />} />
        <Route path="/asset/:name" element={<AssetDetail mode={mode} setMode={setMode} />} />
        <Route path="/analysis" element={<Analysis mode={mode} setMode={setMode} />} />
        <Route path="/simulator" element={<ShockSimulator mode={mode} setMode={setMode} />} />
        <Route path="/trade" element={<TradeDemo mode={mode} setMode={setMode} />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  );
}