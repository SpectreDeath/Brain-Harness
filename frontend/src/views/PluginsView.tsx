import React, { useState } from 'react';
import { BookOpen, Box, ChevronDown, ChevronRight, RefreshCw, Power } from 'lucide-react';
import type { HarnessTool } from '../types/harness';

interface PluginsViewProps {
  plugins: Record<string, string>;
  tools: HarnessTool[];
  onTogglePlugin: (name: string, action: 'enable' | 'disable') => Promise<void>;
  onToggleTool: (toolName: string, enabled: boolean) => Promise<void>;
  onEnableAll: () => Promise<void>;
  onDisableAll: () => Promise<void>;
  onOpenGuide: (name: string) => void;
  onRefresh: () => void;
}

export const PluginsView: React.FC<PluginsViewProps> = ({
  plugins,
  tools,
  onTogglePlugin,
  onToggleTool,
  onEnableAll,
  onDisableAll,
  onOpenGuide,
  onRefresh,
}) => {
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = (name: string) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const pluginEntries = Object.entries(plugins);
  const filtered = pluginEntries.filter(([name]) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    const matchName = name.toLowerCase().includes(q);
    const matchTools = tools.some(
      (t) => (t.provider === name || t.name.startsWith(`${name}.`)) && t.name.toLowerCase().includes(q)
    );
    return matchName || matchTools;
  });

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <Box size={18} color="var(--accent-cyan)" />
            <span>Plugin Ecosystem & Granular Tool Registry</span>
          </div>

          <div style={{ display: 'flex', gap: '0.4rem' }}>
            <button className="btn btn-outline btn-success btn-xs" onClick={onEnableAll}>
              Enable All
            </button>
            <button className="btn btn-outline btn-danger btn-xs" onClick={onDisableAll}>
              Disable All
            </button>
            <button className="btn btn-outline btn-xs" onClick={onRefresh}>
              <RefreshCw size={12} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <input
          type="text"
          placeholder="Search plugins or tool capabilities (e.g. llm, storage, react)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="agent-input"
        />

        <div style={{ maxHeight: '520px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                <th style={{ width: '28px', padding: '0.6rem 0.5rem' }}></th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Plugin Name</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Mounted Tools</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>State</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No plugins found
                  </td>
                </tr>
              ) : (
                filtered.map(([name, state]) => {
                  const pTools = tools.filter(
                    (t) => t.provider === name || (t.name.startsWith(`${name}.`) && !t.provider)
                  );
                  const isExpanded = !!expanded[name];
                  const isEnabled = state === 'enabled';
                  const activeToolsCount = pTools.filter((t) => t.enabled).length;

                  return (
                    <React.Fragment key={name}>
                      <tr
                        style={{ borderBottom: '1px solid var(--border-color)', cursor: 'pointer' }}
                        onClick={() => toggleExpand(name)}
                      >
                        <td style={{ padding: '0.6rem 0.5rem', color: 'var(--text-muted)' }}>
                          {pTools.length > 0 && (isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />)}
                        </td>
                        <td className="text-code" style={{ padding: '0.6rem 0.5rem', fontWeight: 600 }}>
                          {name}
                        </td>
                        <td style={{ padding: '0.6rem 0.5rem' }}>
                          {pTools.length > 0 ? (
                            <span style={{
                              background: 'rgba(56, 189, 248, 0.15)',
                              color: 'var(--accent-cyan)',
                              border: '1px solid rgba(56, 189, 248, 0.3)',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '10px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}>
                              {activeToolsCount} / {pTools.length}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>0</span>
                          )}
                        </td>
                        <td style={{ padding: '0.6rem 0.5rem' }}>
                          <span className={`pill ${state}`}>{state}</span>
                        </td>
                        <td style={{ padding: '0.6rem 0.5rem' }} onClick={(e) => e.stopPropagation()}>
                          <div style={{ display: 'flex', gap: '0.4rem' }}>
                            <button
                              className="btn btn-outline btn-xs"
                              onClick={() => onOpenGuide(name)}
                            >
                              <BookOpen size={12} />
                              <span>Guide</span>
                            </button>
                            <button
                              className={`btn btn-outline btn-xs ${isEnabled ? 'btn-danger' : 'btn-success'}`}
                              onClick={() => onTogglePlugin(name, isEnabled ? 'disable' : 'enable')}
                            >
                              <Power size={12} />
                              <span>{isEnabled ? 'Disable' : 'Enable'}</span>
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Tool Drawers */}
                      {isExpanded && pTools.length > 0 && (
                        <tr>
                          <td colSpan={5} style={{ padding: 0, background: 'rgba(0, 0, 0, 0.3)' }}>
                            <div style={{
                              padding: '0.75rem 1.25rem',
                              borderLeft: '3px solid var(--accent-cyan)',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.5rem',
                            }}>
                              <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                                Granular Tool Control ({pTools.length})
                              </div>
                              {pTools.map((t) => {
                                const short = t.name.startsWith(`${name}.`) ? t.name.substring(name.length + 1) : t.name;
                                return (
                                  <div
                                    key={t.name}
                                    style={{
                                      display: 'flex',
                                      justifyContent: 'space-between',
                                      alignItems: 'center',
                                      padding: '0.45rem 0.75rem',
                                      background: 'rgba(255, 255, 255, 0.025)',
                                      borderRadius: '8px',
                                      border: '1px solid rgba(255, 255, 255, 0.04)',
                                    }}
                                  >
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                      <span className="text-code-cyan" style={{ fontSize: '0.84rem' }}>{short}</span>
                                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                        {t.description || '(no description)'}
                                      </span>
                                    </div>
                                    <button
                                      className={`btn btn-xs ${t.enabled ? 'btn-success' : 'btn-outline btn-danger'}`}
                                      onClick={() => onToggleTool(t.name, !t.enabled)}
                                    >
                                      {t.enabled ? 'ON' : 'OFF'}
                                    </button>
                                  </div>
                                );
                              })}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
