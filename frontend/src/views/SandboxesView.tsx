import React from 'react';
import { RefreshCw, Shield } from 'lucide-react';
import type { HarnessSandbox } from '../types/harness';

interface SandboxesViewProps {
  sandboxes: HarnessSandbox[];
  onRefresh: () => void;
}

export const SandboxesView: React.FC<SandboxesViewProps> = ({ sandboxes, onRefresh }) => {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <Shield size={18} color="var(--accent-rose)" />
            <span>Sandbox Executor & Isolation Monitor</span>
          </div>
          <button className="btn btn-outline btn-xs" onClick={onRefresh}>
            <RefreshCw size={12} />
            <span>Refresh</span>
          </button>
        </div>

        <div style={{ maxHeight: '520px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                <th style={{ padding: '0.6rem 0.5rem' }}>Plugin</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Executor Mode</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Running State</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Process PID</th>
                <th style={{ padding: '0.6rem 0.5rem' }}>Trust Level</th>
              </tr>
            </thead>
            <tbody>
              {sandboxes.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No sandboxes active
                  </td>
                </tr>
              ) : (
                sandboxes.map((s) => (
                  <tr key={s.plugin} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td className="text-code" style={{ padding: '0.65rem 0.5rem', fontWeight: 600 }}>
                      {s.plugin}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill ${s.executor}`}>{s.executor}</span>
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill ${s.is_running ? 'enabled' : 'disabled'}`}>
                        {s.is_running ? 'Running' : 'Stopped'}
                      </span>
                    </td>
                    <td className="text-code" style={{ padding: '0.65rem 0.5rem' }}>
                      {s.pid || '-'}
                    </td>
                    <td style={{ padding: '0.65rem 0.5rem' }}>
                      <span className={`pill ${s.trusted ? 'enabled' : 'disabled'}`}>
                        {s.trusted ? 'Trusted' : 'Untrusted (Subprocess Sandboxed)'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
