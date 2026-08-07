import React from 'react';

export default function TerminalWindow({ title, children }) {
  return (
    <div className="terminal-window">
      <div className="terminal-header">
        <div className="terminal-dots">
          <span className="dot dot-red"></span>
          <span className="dot dot-yellow"></span>
          <span className="dot dot-green"></span>
        </div>
        <div className="terminal-title">{title}</div>
        <div className="terminal-spacer"></div>
      </div>
      <div className="terminal-body">
        {children}
      </div>
    </div>
  );
}
