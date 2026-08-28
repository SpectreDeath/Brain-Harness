import React, { useEffect, useState } from 'react';
import {
  Activity,
  Box,
  Brain,
  Clock,
  Cpu,
  Layers,
  Network,
  Shield,
  Sparkles,
  Upload,
} from 'lucide-react';
import type { ViewType } from './Sidebar';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectView: (view: ViewType) => void;
  onOpenCreator: () => void;
  onOpenIngest: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectView,
  onOpenCreator,
  onOpenIngest,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    { label: 'Go to Overview', icon: <Activity size={16} />, action: () => onSelectView('overview') },
    { label: 'Go to Agent Missions', icon: <Cpu size={16} />, action: () => onSelectView('agent') },
    { label: 'Go to Multi-Agent Swarm', icon: <Layers size={16} />, action: () => onSelectView('swarm') },
    { label: 'Go to Skill Knowledge Graph', icon: <Brain size={16} />, action: () => onSelectView('skills') },
    { label: 'Go to Plugins & Tools', icon: <Box size={16} />, action: () => onSelectView('plugins') },
    { label: 'Go to Timeline & Replay', icon: <Clock size={16} />, action: () => onSelectView('timeline') },
    { label: 'Go to Service Graph', icon: <Network size={16} />, action: () => onSelectView('graph') },
    { label: 'Go to Sandboxes', icon: <Shield size={16} />, action: () => onSelectView('sandboxes') },
    { label: 'Scaffold New Plugin', icon: <Sparkles size={16} />, action: onOpenCreator },
    { label: 'Ingest GitHub Plugin', icon: <Upload size={16} />, action: onOpenIngest },
  ];

  const filtered = actions.filter((a) => a.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(3, 6, 15, 0.82)',
        backdropFilter: 'blur(10px)',
        zIndex: 300,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#0c1324',
          border: '1px solid var(--border-light)',
          borderRadius: '16px',
          padding: '1rem',
          width: '100%',
          maxWidth: '560px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <input
          autoFocus
          type="text"
          placeholder="Type a command or jump to view..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="agent-input"
          style={{ fontSize: '1rem', padding: '0.8rem 1rem' }}
        />

        <div style={{ maxHeight: '300px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {filtered.map((item, idx) => (
            <div
              key={idx}
              onClick={() => {
                item.action();
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.65rem 0.85rem',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.88rem',
                color: 'var(--text-secondary)',
                transition: 'background 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)';
                e.currentTarget.style.color = '#fff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              <span style={{ color: 'var(--accent-cyan)' }}>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
          {filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)', fontSize: '0.84rem' }}>
              No commands matching "{query}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
