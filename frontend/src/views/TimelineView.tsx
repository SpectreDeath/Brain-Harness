import React, { useState } from 'react';
import { Clock, Play } from 'lucide-react';
import type { HarnessEvent } from '../types/harness';

interface TimelineViewProps {
  events: HarnessEvent[];
  onFetchWindow: () => void;
}

export const TimelineView: React.FC<TimelineViewProps> = ({ events, onFetchWindow }) => {
  const [filter, setFilter] = useState('*');
  const [scrubPct, setScrubPct] = useState(100);
  const [openPayloads, setOpenPayloads] = useState<Record<number, boolean>>({});

  const filterChips = [
    { id: '*', label: 'All Events' },
    { id: 'agent', label: '🤖 Agent' },
    { id: 'tool', label: '🔧 Tools' },
    { id: 'swarm', label: '🐝 Swarm' },
    { id: 'plugin', label: '🧩 Plugin' },
    { id: 'system', label: '⚙️ System' },
    { id: 'error', label: '🚨 Errors' },
  ];

  const totalCount = events.length;
  const visibleCount = Math.max(1, Math.round((scrubPct / 100) * totalCount));
  const slicedEvents = events.slice(0, visibleCount);

  const filteredEvents = slicedEvents.filter((ev) => {
    if (filter === '*') return true;
    const etype = (ev.event_type || '').toLowerCase();
    return etype.includes(filter);
  });

  const togglePayload = (idx: number) => {
    setOpenPayloads((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <Clock size={18} color="var(--accent-cyan)" />
            <span>Spatiotemporal Event Timeline & Replay Sourcing</span>
          </div>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            <button className="btn btn-outline btn-xs" onClick={onFetchWindow}>
              Fetch Window
            </button>
            <button
              className="btn btn-purple btn-xs"
              onClick={() => {
                setScrubPct(0);
                let p = 0;
                const timer = setInterval(() => {
                  p += 5;
                  setScrubPct(p);
                  if (p >= 100) clearInterval(timer);
                }, 50);
              }}
            >
              <Play size={12} />
              <span>Replay All</span>
            </button>
          </div>
        </div>

        {/* Timeline Scrubber */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          background: 'rgba(0, 0, 0, 0.35)',
          padding: '0.75rem 1.1rem',
          borderRadius: '10px',
          border: '1px solid var(--border-color)',
        }}>
          <span className="text-code" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Events: {visibleCount} / {totalCount}
          </span>
          <input
            type="range"
            min="1"
            max="100"
            value={scrubPct}
            onChange={(e) => setScrubPct(parseInt(e.target.value, 10))}
            style={{ flex: 1, accentColor: 'var(--accent-cyan)', cursor: 'pointer' }}
          />
          <span className="text-code" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
            {scrubPct}% {scrubPct === 100 ? '(Live)' : ''}
          </span>
        </div>

        {/* Filter Chips */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {filterChips.map((chip) => (
            <button
              key={chip.id}
              onClick={() => setFilter(chip.id)}
              style={{
                background: filter === chip.id ? 'rgba(56, 189, 248, 0.18)' : 'rgba(255, 255, 255, 0.04)',
                border: '1px solid',
                borderColor: filter === chip.id ? 'rgba(56, 189, 248, 0.4)' : 'var(--border-color)',
                color: filter === chip.id ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                borderRadius: '20px',
                padding: '0.3rem 0.75rem',
                fontSize: '0.78rem',
                fontWeight: filter === chip.id ? 600 : 500,
                cursor: 'pointer',
              }}
            >
              {chip.label}
            </button>
          ))}
        </div>

        {/* Event List Box */}
        <div className="terminal-box" style={{ height: '480px' }}>
          {filteredEvents.length === 0 ? (
            <div className="log-line">
              <span className="log-ts">&gt;</span> No events found matching filter.
            </div>
          ) : (
            filteredEvents.map((ev, idx) => {
              const time = ev.timestamp ? ev.timestamp.substring(11, 19) : '';
              const isOpen = !!openPayloads[idx];
              return (
                <div key={ev.id || idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                  <div className="log-line">
                    <span className="log-ts">[{time}]</span>
                    <span className="log-badge system">{ev.event_type}</span>
                    <span className="log-src">{ev.source}</span>
                    <button
                      className="btn btn-outline btn-xs"
                      style={{ padding: '0.15rem 0.45rem', fontSize: '0.7rem' }}
                      onClick={() => togglePayload(idx)}
                    >
                      {isOpen ? 'Hide Payload' : 'View Payload'}
                    </button>
                  </div>
                  {isOpen && (
                    <div style={{
                      background: '#03060f',
                      padding: '0.65rem 0.85rem',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      fontSize: '0.76rem',
                      color: 'var(--accent-cyan)',
                      overflowX: 'auto',
                    }}>
                      <pre>{JSON.stringify(ev.payload || {}, null, 2)}</pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
