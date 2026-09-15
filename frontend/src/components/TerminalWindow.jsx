import React from 'react';

export default function TerminalWindow({ title, children }) {
  return (
    <div className="terminal-window">
      <div className="terminal-header">
        <div className="terminal-title">{title?.replace('~/', '')}</div>
        <div className="terminal-header-note">MarketPulse research desk</div>
      </div>
      <div className="terminal-body">
        {children}
      </div>
    </div>
  );
}
