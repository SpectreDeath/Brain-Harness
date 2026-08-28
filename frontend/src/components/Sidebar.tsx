import React from 'react';
import {
  Activity,
  Box,
  Brain,
  Clock,
  Cpu,
  Layers,
  Network,
  Shield,
  Zap,
} from 'lucide-react';

export type ViewType = 'overview' | 'timeline' | 'graph' | 'agent' | 'swarm' | 'skills' | 'plugins' | 'sandboxes';

interface SidebarProps {
  activeView: ViewType;
  onSelectView: (view: ViewType) => void;
  pluginsCount: number;
  onOpenCmdPalette: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onSelectView,
  pluginsCount,
  onOpenCmdPalette,
}) => {
  const navItems: { id: ViewType; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'overview', label: 'Overview', icon: <Activity size={18} /> },
    { id: 'timeline', label: 'Timeline & Replay', icon: <Clock size={18} /> },
    { id: 'graph', label: 'Service Graph', icon: <Network size={18} /> },
    { id: 'agent', label: 'Agent Missions', icon: <Cpu size={18} /> },
    { id: 'swarm', label: 'Multi-Agent Swarm', icon: <Layers size={18} />, badge: 'Live' },
    { id: 'skills', label: 'Skill Graph & Router', icon: <Brain size={18} /> },
    { id: 'plugins', label: 'Plugins & Tools', icon: <Box size={18} />, badge: String(pluginsCount) },
    { id: 'sandboxes', label: 'Sandboxes', icon: <Shield size={18} /> },
  ];

  return (
    <aside style={{
      width: 'var(--sidebar-width)',
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      top: 0,
      bottom: 0,
      left: 0,
      zIndex: 60,
      backdropFilter: 'blur(20px)',
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '1.25rem 1.4rem',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.85rem',
      }}>
        <div style={{
          background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
          color: '#fff',
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px var(--glow-cyan)',
          flexShrink: 0,
        }}>
          <Zap size={20} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{
            fontSize: '1.05rem',
            fontWeight: 700,
            letterSpacing: '-0.01em',
            background: 'linear-gradient(90deg, #fff, #cbd5e1)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            BRAIN HARNESS
          </span>
          <span style={{
            fontSize: '0.72rem',
            color: 'var(--accent-cyan)',
            fontWeight: 600,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}>
            React Control Room
          </span>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{
        padding: '1rem 0.75rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.35rem',
        flex: 1,
        overflowY: 'auto',
      }}>
        <div style={{
          fontSize: '0.68rem',
          fontWeight: 700,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          padding: '0.6rem 0.75rem 0.3rem',
        }}>
          Control Deck
        </div>

        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectView(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                padding: '0.6rem 0.85rem',
                background: isActive
                  ? 'linear-gradient(90deg, rgba(56, 189, 248, 0.15), rgba(168, 85, 247, 0.08))'
                  : 'transparent',
                border: '1px solid',
                borderColor: isActive ? 'rgba(56, 189, 248, 0.3)' : 'transparent',
                borderRadius: '8px',
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                fontSize: '0.88rem',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                boxShadow: isActive ? '0 0 14px var(--glow-cyan)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span style={{ color: isActive ? 'var(--accent-cyan)' : 'inherit' }}>{item.icon}</span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.45rem',
                  borderRadius: '10px',
                  background: isActive ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.08)',
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div style={{
        padding: '1rem',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.65rem',
      }}>
        <div style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>Kernel State:</span>
          <span className="text-code-cyan">Connected</span>
        </div>
        <button
          className="btn btn-outline btn-xs"
          style={{ width: '100%' }}
          onClick={onOpenCmdPalette}
        >
          <span>Command Palette (⌘K)</span>
        </button>
      </div>
    </aside>
  );
};
