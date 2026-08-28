import React, { useState } from 'react';
import { Brain, Compass, RefreshCw } from 'lucide-react';
import type { SkillRouteResult } from '../types/harness';

interface SkillsViewProps {
  onRouteIntent: (intent: string) => Promise<SkillRouteResult>;
  onFindChain: (start: string, target: string) => Promise<any>;
  onRefreshGraph: () => void;
}

export const SkillsView: React.FC<SkillsViewProps> = ({
  onRouteIntent,
  onFindChain,
  onRefreshGraph,
}) => {
  const [intentInput, setIntentInput] = useState('author and audit agent instruction files');
  const [routeResult, setRouteResult] = useState<SkillRouteResult | null>(null);
  const [isRouting, setIsRouting] = useState(false);

  const [chainStart, setChainStart] = useState('');
  const [chainTarget, setChainTarget] = useState('');
  const [chainPath, setChainPath] = useState<string[] | null>(null);

  const handleRoute = async () => {
    if (!intentInput.trim()) return;
    setIsRouting(true);
    try {
      const res = await onRouteIntent(intentInput);
      setRouteResult(res);
    } finally {
      setIsRouting(false);
    }
  };

  const handleFindChain = async () => {
    if (!chainStart.trim() || !chainTarget.trim()) return;
    try {
      const res = await onFindChain(chainStart, chainTarget);
      setChainPath(res.chain || [chainStart, chainTarget]);
    } catch (e) {
      setChainPath([chainStart, chainTarget]);
    }
  };

  const nodes = [
    { id: 'agent-instruction-architect', category: 'meta', x: 180, y: 140 },
    { id: 'deepen-architecture', category: 'arch', x: 330, y: 200 },
    { id: 'questio-reflection', category: 'meta', x: 200, y: 290 },
    { id: 'crafting-skills', category: 'meta', x: 460, y: 130 },
    { id: 'tdd', category: 'testing', x: 400, y: 310 },
    { id: 'diagnosing-bugs', category: 'testing', x: 550, y: 240 },
    { id: 'codebase-design', category: 'arch', x: 320, y: 70 },
  ];

  return (
    <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.25rem' }}>
      {/* Visual Topological Skill Network */}
      <div className="glass-card" style={{ gridColumn: 'span 7', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <Brain size={18} color="var(--accent-cyan)" />
            <span>Skill Knowledge Graph Topology</span>
          </div>
          <button className="btn btn-outline btn-xs" onClick={onRefreshGraph}>
            <RefreshCw size={12} />
            <span>Refresh</span>
          </button>
        </div>

        <div style={{
          width: '100%',
          height: '460px',
          background: '#040711',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <svg width="100%" height="100%" viewBox="0 0 700 400">
            <line x1="180" y1="140" x2="330" y2="200" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />
            <line x1="330" y1="200" x2="200" y2="290" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />
            <line x1="330" y1="200" x2="460" y2="130" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />
            <line x1="330" y1="200" x2="400" y2="310" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />
            <line x1="460" y1="130" x2="550" y2="240" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />
            <line x1="320" y1="70" x2="180" y2="140" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />

            {nodes.map((n) => (
              <g key={n.id} style={{ cursor: 'pointer' }}>
                <circle cx={n.x} cy={n.y} r="20" fill="#0f172a" stroke="var(--accent-cyan)" strokeWidth="2" />
                <text x={n.x} y={n.y + 4} textAnchor="middle" fill="#fff" fontSize="9" fontFamily="Inter" fontWeight="600">
                  {n.id.substring(0, 4).toUpperCase()}
                </text>
                <text x={n.x} y={n.y + 32} textAnchor="middle" fill="var(--text-secondary)" fontSize="10" fontFamily="'Fira Code', monospace">
                  {n.id}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </div>

      {/* Natural Language Skill Router & Chain Pathfinder */}
      <div className="glass-card" style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
          <Compass size={18} color="var(--accent-purple)" />
          <span>Natural Language Skill Router</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Task Intent
            </label>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <input
                type="text"
                value={intentInput}
                onChange={(e) => setIntentInput(e.target.value)}
                className="agent-input"
                placeholder="Describe your intent..."
              />
              <button className="btn btn-sm" onClick={handleRoute} disabled={isRouting}>
                {isRouting ? '...' : 'Route'}
              </button>
            </div>
          </div>

          {/* Route Results */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
            {routeResult?.matches?.map((m, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '0.6rem 0.85rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="text-code-cyan" style={{ fontSize: '0.86rem' }}>{m.skill_name}</span>
                  <span className="pill enabled">{Math.round(m.confidence * 100)}% Match</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Triggers: {(m.matched_triggers || []).join(', ') || 'intent match'}
                </div>
              </div>
            ))}
          </div>

          {routeResult?.recommended_chain && routeResult.recommended_chain.length > 0 && (
            <div style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', fontWeight: 600 }}>
              🔗 Recommended Execution Chain: {routeResult.recommended_chain.join(' → ')}
            </div>
          )}

          {/* Chain Pathfinder */}
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Skill Chain Pathfinder
            </label>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <input
                type="text"
                placeholder="Start (e.g. deep-module)"
                value={chainStart}
                onChange={(e) => setChainStart(e.target.value)}
                className="agent-input"
              />
              <input
                type="text"
                placeholder="Target (e.g. tdd)"
                value={chainTarget}
                onChange={(e) => setChainTarget(e.target.value)}
                className="agent-input"
              />
              <button className="btn btn-outline btn-sm" onClick={handleFindChain}>
                Find Path
              </button>
            </div>

            {chainPath && (
              <div style={{ marginTop: '0.5rem' }}>
                <span className="pill enabled" style={{ width: '100%', justifyContent: 'center' }}>
                  Path: {chainPath.join(' → ')}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
