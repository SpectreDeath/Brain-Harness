import React, { useState } from 'react';
import { GitBranch, Layers, Play, RefreshCw } from 'lucide-react';
import type { SwarmRun } from '../types/harness';

interface SwarmViewProps {
  runs: SwarmRun[];
  onLaunchSwarm: (objective: string, tokens: number, consensus: number) => Promise<any>;
  onInspectTree: (runId: string) => void;
  onRefreshRuns: () => void;
}

export const SwarmView: React.FC<SwarmViewProps> = ({
  runs,
  onLaunchSwarm,
  onInspectTree,
  onRefreshRuns,
}) => {
  const [objective, setObjective] = useState(
    'Architect a fault-tolerant distributed plugin cache layer'
  );
  const [tokens, setTokens] = useState(50000);
  const [consensus, setConsensus] = useState(66);
  const [isRunning, setIsRunning] = useState(false);

  const handleLaunch = async () => {
    if (!objective.trim() || isRunning) return;
    setIsRunning(true);
    try {
      await onLaunchSwarm(objective, tokens, consensus / 100.0);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.25rem' }}>
      {/* Swarm Launcher */}
      <div className="glass-card" style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
          <Layers size={18} color="var(--accent-indigo)" />
          <span>Multi-Agent Swarm Mission Launcher</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Deliberation Objective / Problem
            </label>
            <textarea
              rows={4}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="agent-input"
              placeholder="Specify the objective for multi-agent debate..."
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                Consensus Threshold ({consensus}%)
              </label>
              <input
                type="range"
                min="50"
                max="100"
                value={consensus}
                onChange={(e) => setConsensus(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: 'var(--accent-purple)', cursor: 'pointer' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                Token Budget
              </label>
              <input
                type="number"
                step="5000"
                value={tokens}
                onChange={(e) => setTokens(parseInt(e.target.value, 10))}
                className="agent-input"
              />
            </div>
          </div>

          <button
            className="btn btn-purple"
            style={{ width: '100%', padding: '0.65rem' }}
            onClick={handleLaunch}
            disabled={isRunning}
          >
            <Play size={14} />
            <span>{isRunning ? 'Debating & Converging...' : 'Launch Multi-Agent Swarm'}</span>
          </button>
        </div>
      </div>

      {/* Swarm Runs History & Visual Execution Trees */}
      <div className="glass-card" style={{ gridColumn: 'span 7', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>Swarm Execution History & Consensus Runs</span>
          <button className="btn btn-outline btn-xs" onClick={onRefreshRuns}>
            <RefreshCw size={12} />
            <span>Refresh</span>
          </button>
        </div>

        <div style={{ maxHeight: '480px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Run ID</th>
                <th style={{ padding: '0.5rem' }}>Status</th>
                <th style={{ padding: '0.5rem' }}>Consensus</th>
                <th style={{ padding: '0.5rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)' }}>
                    No recorded swarm runs yet.
                  </td>
                </tr>
              ) : (
                runs.map((r, idx) => {
                  const rid = r.run_id || r.id || `swarm-${idx}`;
                  return (
                    <tr key={rid} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td className="text-code" style={{ padding: '0.6rem 0.5rem', fontSize: '0.78rem' }}>
                        {rid.substring(0, 12)}
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        <span className="pill enabled">{r.status || 'completed'}</span>
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        {Math.round((r.consensus_score || 0.85) * 100)}%
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        <button
                          className="btn btn-outline btn-xs"
                          onClick={() => onInspectTree(rid)}
                        >
                          <GitBranch size={12} />
                          <span>Inspect Tree</span>
                        </button>
                      </td>
                    </tr>
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
