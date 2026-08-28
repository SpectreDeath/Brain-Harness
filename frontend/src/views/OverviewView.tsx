import React from 'react';
import { Activity, Box, Cpu, HardDrive, RefreshCw, Shield, Trash2, Zap } from 'lucide-react';
import type { HarnessEvent, HarnessStatus } from '../types/harness';

interface OverviewViewProps {
  status: HarnessStatus | null;
  metrics: Record<string, any> | null;
  sandboxesCount: number;
  events: HarnessEvent[];
  onRefresh: () => void;
  onClearStream: () => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  status,
  metrics,
  sandboxesCount,
  events,
  onRefresh,
  onClearStream,
}) => {
  const pluginsCount = status?.plugins_count ?? 0;
  const servicesCount = status?.services_count ?? 0;
  const toolsCount = status?.tools_count ?? 0;
  const eventsCount = events.length;
  const tokensConsumed = metrics?.total_tokens ?? 0;

  const kpis = [
    { label: 'Active Plugins', val: pluginsCount, sub: 'Loaded & Enabled', icon: <Box size={18} color="var(--accent-cyan)" /> },
    { label: 'IoC Services', val: servicesCount, sub: 'Typed Service Keys', icon: <HardDrive size={18} color="var(--accent-purple)" /> },
    { label: 'Mounted Tools', val: toolsCount, sub: 'Callable Entrypoints', icon: <Zap size={18} color="var(--accent-emerald)" /> },
    { label: 'Captured Events', val: eventsCount, sub: 'Event Sourcing Stream', icon: <Activity size={18} color="var(--accent-cyan)" /> },
    { label: 'Tokens Consumed', val: tokensConsumed.toLocaleString(), sub: 'LLM Optimizer Budget', icon: <Cpu size={18} color="var(--accent-amber)" /> },
    { label: 'Active Sandboxes', val: sandboxesCount, sub: 'Subprocess & Venv', icon: <Shield size={18} color="var(--accent-rose)" /> },
  ];

  const services = status?.services || {};

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top KPI Metrics Row */}
      <div className="glass-card" style={{ padding: '1.25rem' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
        }}>
          {kpis.map((kpi, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '1rem 0.9rem',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '0.2rem',
                transition: 'transform 0.15s, border-color 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'none';
                e.currentTarget.style.borderColor = 'var(--border-color)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                {kpi.icon}
                <span className="text-code" style={{ fontSize: '1.65rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {kpi.val}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
                {kpi.label}
              </div>
              <div style={{ fontSize: '0.68rem', color: 'var(--accent-emerald)' }}>
                {kpi.sub}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grid: Service Context & Live Stream */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.25rem' }}>
        {/* Service Context */}
        <div className="glass-card" style={{ gridColumn: 'span 6', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
              <HardDrive size={18} color="var(--accent-purple)" />
              <span>Kernel Service Context</span>
            </div>
            <button className="btn btn-outline btn-xs" onClick={onRefresh}>
              <RefreshCw size={12} />
              <span>Refresh</span>
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '360px', overflowY: 'auto' }}>
            {Object.keys(services).length === 0 ? (
              <div className="text-muted-sm">Loading service registry...</div>
            ) : (
              Object.entries(services).map(([sKey, provider]) => (
                <div
                  key={sKey}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.5rem 0.75rem',
                    background: 'rgba(0, 0, 0, 0.3)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div>
                    <span className="text-code-cyan">{sKey}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                      ({provider || 'core'})
                    </span>
                  </div>
                  <span className="pill enabled">Active</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live Activity Stream */}
        <div className="glass-card" style={{ gridColumn: 'span 6', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
              <Activity size={18} color="var(--accent-cyan)" />
              <span>Live Telemetry Stream</span>
            </div>
            <button className="btn btn-outline btn-xs" onClick={onClearStream}>
              <Trash2 size={12} />
              <span>Clear</span>
            </button>
          </div>

          <div className="terminal-box" style={{ height: '360px' }}>
            {events.length === 0 ? (
              <div className="log-line">
                <span className="log-ts">&gt;</span> Listening for harness telemetry...
              </div>
            ) : (
              events.slice(-40).map((ev, i) => {
                const time = ev.timestamp ? ev.timestamp.substring(11, 19) : '';
                return (
                  <div key={ev.id || i} className="log-line">
                    <span className="log-ts">[{time}]</span>
                    <span className="log-badge system">{ev.event_type}</span>
                    <span className="log-src">{ev.source}</span>
                    <span className="log-content">{JSON.stringify(ev.payload || {})}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
