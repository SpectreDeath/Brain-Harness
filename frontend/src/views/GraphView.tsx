import React, { useEffect, useRef, useState, useTransition } from 'react';
import { Network, RefreshCw, Sparkles, Layers, ShieldAlert, ChevronRight, Zap } from 'lucide-react';
import { api } from '../services/api';

interface GraphViewProps {
  mermaidCode: string;
  onRefresh: () => void;
}

declare global {
  interface Window {
    mermaid?: any;
  }
}

export const GraphView: React.FC<GraphViewProps> = ({ mermaidCode, onRefresh }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewMode, setViewMode] = useState<'kernel' | 'skills'>('skills');
  const [skillMermaid, setSkillMermaid] = useState<string>('');
  const [clusters, setClusters] = useState<any[]>([]);
  const [selectedCluster, setSelectedCluster] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [, startTransition] = useTransition();

  const loadSkillClusters = async () => {
    setLoading(true);
    try {
      const [mermaidRes, clustersRes] = await Promise.all([
        api.getSkillClusterMermaid().catch(() => ({ mermaid: '' })),
        api.getSkillClusters().catch(() => ({ clusters: [], bridges: [] })),
      ]);
      setSkillMermaid(mermaidRes.mermaid || '');
      const fetchedClusters = clustersRes.clusters || [];
      setClusters(fetchedClusters);
      if (fetchedClusters.length > 0 && !selectedCluster) {
        setSelectedCluster(fetchedClusters[0]);
      }
    } catch (err) {
      console.error('Failed to load skill clusters', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'skills') {
      loadSkillClusters();
    }
  }, [viewMode]);

  const activeCode = viewMode === 'kernel' ? mermaidCode : skillMermaid;

  useEffect(() => {
    if (window.mermaid && containerRef.current) {
      const codeToRender = activeCode || 'graph TD\n  Harness[Harness Core]';
      containerRef.current.innerHTML = `<div class="mermaid">${codeToRender}</div>`;
      try {
        window.mermaid.run({ nodes: containerRef.current.querySelectorAll('.mermaid') });
      } catch (err) {
        console.error('Mermaid render error', err);
      }
    }
  }, [activeCode]);

  const handleRefresh = () => {
    if (viewMode === 'kernel') {
      onRefresh();
    } else {
      loadSkillClusters();
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
              {viewMode === 'skills' ? (
                <Sparkles size={18} color="var(--accent-purple, #a855f7)" />
              ) : (
                <Network size={18} color="var(--accent-blue, #3b82f6)" />
              )}
              <span>
                {viewMode === 'skills'
                  ? 'Dynamic Skill Clusters & Emergent Capabilities (Leiden/Louvain)'
                  : 'Micro-Kernel Component & Dependency Graph'}
              </span>
            </div>
            {viewMode === 'skills' && (
              <span className="badge badge-info" style={{ fontSize: '11px', padding: '0.2rem 0.5rem' }}>
                {clusters.length} Clusters Detected
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* View Mode Segmented Controls */}
            <div
              style={{
                display: 'inline-flex',
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '3px',
                borderRadius: '8px',
                border: '1px solid var(--border-color, #30363d)',
              }}
            >
              <button
                className={`btn btn-xs ${viewMode === 'skills' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ borderRadius: '6px' }}
                onClick={() => startTransition(() => setViewMode('skills'))}
              >
                <Layers size={13} style={{ marginRight: '4px' }} />
                <span>Skill Clusters</span>
              </button>
              <button
                className={`btn btn-xs ${viewMode === 'kernel' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ borderRadius: '6px' }}
                onClick={() => startTransition(() => setViewMode('kernel'))}
              >
                <Network size={13} style={{ marginRight: '4px' }} />
                <span>Kernel Architecture</span>
              </button>
            </div>

            <button className="btn btn-outline btn-xs" onClick={handleRefresh} disabled={loading}>
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'Refreshing...' : 'Re-render'}</span>
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'skills' ? '1fr 340px' : '1fr', gap: '1rem', minHeight: '520px' }}>
          {/* Main Visual Canvas */}
          <div
            ref={containerRef}
            style={{
              background: '#040711',
              border: '1px solid var(--border-color, #30363d)',
              borderRadius: '12px',
              padding: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'auto',
              minHeight: '480px',
            }}
          >
            <div className="text-muted-sm">{loading ? 'Computing cluster layout...' : 'Loading graph...'}</div>
          </div>

          {/* Emergent Capabilities & Cluster Inspector Drawer */}
          {viewMode === 'skills' && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                maxHeight: '620px',
                overflowY: 'auto',
                background: 'rgba(10, 15, 29, 0.65)',
                border: '1px solid var(--border-color, #30363d)',
                borderRadius: '12px',
                padding: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color, #30363d)', paddingBottom: '0.5rem' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-color, #e6edf3)' }}>
                  Cluster Inspector
                </span>
                <span className="text-muted-sm" style={{ fontSize: '11px' }}>
                  {clusters.length} Domains
                </span>
              </div>

              {/* Cluster Pills */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {clusters.map((c) => {
                  const isSelected = selectedCluster?.cluster_id === c.cluster_id;
                  return (
                    <div
                      key={c.cluster_id}
                      onClick={() => setSelectedCluster(c)}
                      style={{
                        padding: '0.6rem 0.75rem',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                        border: isSelected ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: isSelected ? '#60a5fa' : '#f0f6fc' }}>
                          {c.name}
                        </span>
                        <span style={{ fontSize: '10px', color: '#94a3b8', background: 'rgba(255, 255, 255, 0.06)', padding: '2px 6px', borderRadius: '4px' }}>
                          {c.cohesion_score !== undefined ? `${Math.round(c.cohesion_score * 100)}% Cohesion` : ''}
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#8b949e', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Zap size={11} color="#f59e0b" />
                        <span>Hub: <b>{c.central_hub_skill}</b></span>
                        <span>•</span>
                        <span>{c.skills?.length || 0} skills</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Emergent Capability Detail Card */}
              {selectedCluster && (
                <div
                  style={{
                    marginTop: '0.5rem',
                    padding: '0.85rem',
                    background: 'rgba(16, 24, 40, 0.85)',
                    border: '1px solid #1e3a8a',
                    borderRadius: '8px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#93c5fd', fontSize: '12px', fontWeight: 600 }}>
                    <Sparkles size={13} color="#60a5fa" />
                    <span>Emergent Capabilities ({selectedCluster.emergent_capabilities?.length || 0})</span>
                  </div>

                  {selectedCluster.emergent_capabilities && selectedCluster.emergent_capabilities.length > 0 ? (
                    selectedCluster.emergent_capabilities.map((cap: any) => (
                      <div key={cap.id} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)', paddingTop: '0.4rem' }}>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: '#f0f6fc' }}>{cap.title}</div>
                        <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0, lineHeight: 1.4 }}>{cap.description}</p>
                        
                        {cap.recommended_pipeline && cap.recommended_pipeline.length > 0 && (
                          <div style={{ marginTop: '0.2rem' }}>
                            <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#64748b', fontWeight: 600, marginBottom: '2px' }}>
                              Recommended Pipeline
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
                              {cap.recommended_pipeline.map((step: string, idx: number) => (
                                <React.Fragment key={step}>
                                  <span style={{ fontSize: '10px', background: 'rgba(30, 58, 138, 0.5)', color: '#bfdbfe', padding: '1px 5px', borderRadius: '4px' }}>
                                    {step}
                                  </span>
                                  {idx < cap.recommended_pipeline.length - 1 && <ChevronRight size={10} color="#64748b" />}
                                </React.Fragment>
                              ))}
                            </div>
                          </div>
                        )}

                        {cap.guarded_anti_patterns && cap.guarded_anti_patterns.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '0.2rem', color: '#f87171', fontSize: '10px' }}>
                            <ShieldAlert size={11} />
                            <span>Guards: {cap.guarded_anti_patterns.slice(0, 2).join(', ')}</span>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-muted-sm" style={{ fontSize: '11px' }}>
                      No emergent macro-actions synthesized for this cluster.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
