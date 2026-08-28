import React from 'react';
import { Command, Sparkles, Upload } from 'lucide-react';
import type { ViewType } from './Sidebar';

interface HeaderProps {
  activeView: ViewType;
  wsConnected: boolean;
  onOpenCreator: () => void;
  onOpenIngest: () => void;
  onOpenCmdPalette: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeView,
  wsConnected,
  onOpenCreator,
  onOpenIngest,
  onOpenCmdPalette,
}) => {
  const titles: Record<ViewType, { title: string; subtitle: string }> = {
    overview: { title: '📊 System Overview & Health', subtitle: 'Real-time telemetry and micro-kernel state' },
    timeline: { title: '⏱️ Spatiotemporal Event Timeline', subtitle: 'Replayable event sourcing log across all plugins' },
    graph: { title: '🕸️ Micro-Kernel Service Graph', subtitle: 'Declarative IoC dependency hierarchy' },
    agent: { title: '🤖 Autonomous Agent Missions', subtitle: 'Multi-step autonomous ReAct execution and session transcripts' },
    swarm: { title: '🐝 Multi-Agent Swarm Mission Control', subtitle: 'Distributed agent deliberation, debate, and consensus' },
    skills: { title: '🧠 Skill Knowledge Graph & Router', subtitle: 'Topological agent capability graph and intent routing' },
    plugins: { title: '🧩 Plugin Ecosystem & Tools', subtitle: 'Dynamic registration and tool enablement matrix' },
    sandboxes: { title: '🛡️ Sandboxes & Process Isolation', subtitle: 'Subprocess and venv execution security monitor' },
  };

  const current = titles[activeView] || { title: activeView, subtitle: '' };

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      background: 'var(--bg-header)',
      borderBottom: '1px solid var(--border-color)',
      padding: '0.85rem 2rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <div>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.01em', color: '#fff' }}>
          {current.title}
        </h1>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          {current.subtitle}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          onClick={onOpenCmdPalette}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            padding: '0.35rem 0.65rem',
            fontSize: '0.75rem',
            fontFamily: "'Fira Code', monospace",
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            cursor: 'pointer',
          }}
        >
          <Command size={14} />
          <span>⌘K Quick Actions</span>
        </button>

        <button className="btn btn-outline btn-sm" onClick={onOpenCreator}>
          <Sparkles size={14} />
          <span>Scaffold Plugin</span>
        </button>

        <button className="btn btn-sm" onClick={onOpenIngest}>
          <Upload size={14} />
          <span>Ingest Plugin</span>
        </button>

        {/* Live WS Pulse Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          background: 'rgba(0, 0, 0, 0.35)',
          padding: '0.35rem 0.75rem',
          borderRadius: '20px',
          border: '1px solid var(--border-color)',
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: wsConnected ? 'var(--accent-emerald)' : 'var(--accent-rose)',
            boxShadow: wsConnected ? '0 0 8px var(--accent-emerald)' : '0 0 8px var(--accent-rose)',
            transition: 'all 0.3s ease',
          }} />
          <span>{wsConnected ? 'Live Connected' : 'Connecting...'}</span>
        </div>
      </div>
    </header>
  );
};
