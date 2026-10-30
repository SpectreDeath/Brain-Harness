import React, { useEffect, useRef, useState, useTransition } from 'react';
import {
  Network,
  RefreshCw,
  Sparkles,
  Layers,
  ShieldAlert,
  ChevronRight,
  Zap,
  BookOpen,
  AlertTriangle,
  Search,
  ExternalLink,
} from 'lucide-react';
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

type ViewMode = 'kernel' | 'skills' | 'knowledge';

export const GraphView: React.FC<GraphViewProps> = ({ mermaidCode, onRefresh }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('skills');
  const [skillMermaid, setSkillMermaid] = useState<string>('');
  const [clusters, setClusters] = useState<any[]>([]);
  const [selectedCluster, setSelectedCluster] = useState<any | null>(null);

  // Knowledge graph state
  const [knowledgeMermaid, setKnowledgeMermaid] = useState<string>('');
  const [knowledgeGraph, setKnowledgeGraph] = useState<any | null>(null);
  const [knowledgeSummary, setKnowledgeSummary] = useState<any | null>(null);
  const [selectedKnowledgeNode, setSelectedKnowledgeNode] = useState<any | null>(null);
  const [contradictions, setContradictions] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');

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

  const loadKnowledgeGraph = async () => {
    setLoading(true);
    try {
      const [graphRes, conflictsRes] = await Promise.all([
        api.getKnowledgeGraph({
          includeDerived: true,
          domain: selectedDomain === 'all' ? undefined : selectedDomain,
        }).catch(() => ({ graph: { nodes: [], edges: [] }, summary: null, mermaid: '' })),
        api.getKnowledgeContradictions().catch(() => ({ contradictions: [] })),
      ]);
      setKnowledgeMermaid(graphRes.mermaid || '');
      setKnowledgeGraph(graphRes.graph || { nodes: [], edges: [] });
      setKnowledgeSummary(graphRes.summary || null);
      setContradictions(conflictsRes.contradictions || []);
      const nodes = graphRes.graph?.nodes || [];
      if (nodes.length > 0 && !selectedKnowledgeNode) {
        setSelectedKnowledgeNode(nodes[0]);
      }
    } catch (err) {
      console.error('Failed to load knowledge graph', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'skills') {
      loadSkillClusters();
    } else if (viewMode === 'knowledge') {
      loadKnowledgeGraph();
    }
  }, [viewMode, selectedDomain]);

  const activeCode =
    viewMode === 'kernel'
      ? mermaidCode
      : viewMode === 'skills'
      ? skillMermaid
      : knowledgeMermaid;

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
    } else if (viewMode === 'skills') {
      loadSkillClusters();
    } else {
      loadKnowledgeGraph();
    }
  };

  const handleResolveContradiction = async (kiA: string, kiB: string, action: string) => {
    try {
      await api.resolveKnowledgeContradiction({ kiA, kiB, action });
      await loadKnowledgeGraph();
    } catch (err) {
      console.error('Failed to resolve contradiction', err);
    }
  };

  const filteredKnowledgeNodes = (knowledgeGraph?.nodes || []).filter((n: any) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      n.id.toLowerCase().includes(q) ||
      (n.label && n.label.toLowerCase().includes(q)) ||
      (n.category && n.category.toLowerCase().includes(q)) ||
      (n.tags && n.tags.some((t: string) => t.toLowerCase().includes(q)))
    );
  });

  const incidentEdges = (knowledgeGraph?.edges || []).filter(
    (e: any) =>
      selectedKnowledgeNode &&
      (e.source === selectedKnowledgeNode.id || e.target === selectedKnowledgeNode.id)
  );

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
              {viewMode === 'skills' ? (
                <Sparkles size={18} color="var(--accent-purple, #a855f7)" />
              ) : viewMode === 'knowledge' ? (
                <BookOpen size={18} color="#10b981" />
              ) : (
                <Network size={18} color="var(--accent-blue, #3b82f6)" />
              )}
              <span>
                {viewMode === 'skills'
                  ? 'Dynamic Skill Clusters & Emergent Capabilities (Leiden/Louvain)'
                  : viewMode === 'knowledge'
                  ? 'Knowledge Vault & Inter-Domain Graph'
                  : 'Micro-Kernel Component & Dependency Graph'}
              </span>
            </div>
            {viewMode === 'skills' && (
              <span className="badge badge-info" style={{ fontSize: '11px', padding: '0.2rem 0.5rem' }}>
                {clusters.length} Clusters Detected
              </span>
            )}
            {viewMode === 'knowledge' && knowledgeSummary && (
              <span className="badge" style={{ fontSize: '11px', padding: '0.2rem 0.5rem', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                {knowledgeSummary.total_nodes} Entities • {knowledgeSummary.total_edges} Edges
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
              <button
                className={`btn btn-xs ${viewMode === 'knowledge' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ borderRadius: '6px' }}
                onClick={() => startTransition(() => setViewMode('knowledge'))}
              >
                <BookOpen size={13} style={{ marginRight: '4px' }} />
                <span>Knowledge Graph</span>
              </button>
            </div>

            {viewMode === 'knowledge' && (
              <a
                href="/api/knowledge/graph/html"
                target="_blank"
                rel="noreferrer"
                className="btn btn-outline btn-xs"
                title="Open standalone interactive HTML canvas brief in new tab"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              >
                <ExternalLink size={12} />
                <span>Canvas Brief</span>
              </a>
            )}

            <button className="btn btn-outline btn-xs" onClick={handleRefresh} disabled={loading}>
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'Refreshing...' : 'Re-render'}</span>
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'kernel' ? '1fr' : '1fr 360px', gap: '1rem', minHeight: '520px' }}>
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
            <div className="text-muted-sm">{loading ? 'Rendering graph...' : 'Loading graph...'}</div>
          </div>

          {/* Skill Cluster Drawer */}
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

          {/* Knowledge Vault Inspector Drawer */}
          {viewMode === 'knowledge' && (
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
                  Knowledge Inspector
                </span>
                <span className="text-muted-sm" style={{ fontSize: '11px' }}>
                  {filteredKnowledgeNodes.length} Visible
                </span>
              </div>

              {/* Contradiction Alert Box */}
              {contradictions.length > 0 && (
                <div
                  style={{
                    background: 'rgba(234, 179, 8, 0.1)',
                    border: '1px solid rgba(234, 179, 8, 0.3)',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#facc15', fontSize: '12px', fontWeight: 600 }}>
                    <AlertTriangle size={14} />
                    <span>Contradiction Queue ({contradictions.length})</span>
                  </div>
                  {contradictions.slice(0, 3).map((c, idx) => (
                    <div key={idx} style={{ fontSize: '11px', color: '#d1d5db', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '0.4rem' }}>
                      <div><b>{c.ki_a}</b> vs <b>{c.ki_b}</b></div>
                      <div style={{ color: '#9ca3af', fontSize: '10px' }}>{c.reason}</div>
                      <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                        <button
                          className="btn btn-xs btn-outline"
                          style={{ fontSize: '9px', padding: '1px 5px' }}
                          onClick={() => handleResolveContradiction(c.ki_a, c.ki_b, 'supersede')}
                        >
                          Supersede
                        </button>
                        <button
                          className="btn btn-xs btn-outline"
                          style={{ fontSize: '9px', padding: '1px 5px' }}
                          onClick={() => handleResolveContradiction(c.ki_a, c.ki_b, 'contradict')}
                        >
                          Conflict
                        </button>
                        <button
                          className="btn btn-xs btn-ghost"
                          style={{ fontSize: '9px', padding: '1px 5px' }}
                          onClick={() => handleResolveContradiction(c.ki_a, c.ki_b, 'dismiss')}
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Filters */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '6px', padding: '0.2rem 0.5rem', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <Search size={12} color="#6b7280" style={{ marginRight: '6px' }} />
                  <input
                    type="text"
                    placeholder="Search entities or tags..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '11px', width: '100%', outline: 'none' }}
                  />
                </div>

                <select
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    padding: '0.25rem 0.5rem',
                    color: '#d1d5db',
                    fontSize: '11px',
                    outline: 'none',
                  }}
                >
                  <option value="all">All Domains ({knowledgeSummary?.total_nodes || 0})</option>
                  <option value="agent_orchestration">agent_orchestration</option>
                  <option value="context_engineering">context_engineering</option>
                  <option value="developer_experience">developer_experience</option>
                  <option value="data_engineering">data_engineering</option>
                  <option value="security_and_forensics">security_and_forensics</option>
                  <option value="memory_and_epistemics">memory_and_epistemics</option>
                  <option value="infrastructure_and_runtime">infrastructure_and_runtime</option>
                  <option value="scientific_computing">scientific_computing</option>
                </select>
              </div>

              {/* Selected Node Details Card */}
              {selectedKnowledgeNode && (
                <div
                  style={{
                    background: 'rgba(16, 24, 40, 0.9)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.4rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#34d399' }}>
                      {selectedKnowledgeNode.label}
                    </span>
                    <span style={{ fontSize: '9px', background: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7', padding: '1px 5px', borderRadius: '4px' }}>
                      {selectedKnowledgeNode.node_kind || 'ki'}
                    </span>
                  </div>
                  <div style={{ fontSize: '10px', color: '#9ca3af', wordBreak: 'break-all' }}>
                    ID: <code>{selectedKnowledgeNode.id}</code>
                  </div>
                  <div style={{ fontSize: '10px', color: '#cbd5e1' }}>
                    Domain: <b style={{ color: '#93c5fd' }}>{selectedKnowledgeNode.domain || selectedKnowledgeNode.category}</b>
                  </div>
                  {selectedKnowledgeNode.tags && selectedKnowledgeNode.tags.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px', marginTop: '2px' }}>
                      {selectedKnowledgeNode.tags.map((t: string) => (
                        <span key={t} style={{ fontSize: '9px', background: 'rgba(255, 255, 255, 0.08)', color: '#d1d5db', padding: '1px 4px', borderRadius: '3px' }}>
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Incident Edges */}
                  <div style={{ marginTop: '0.4rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '0.4rem' }}>
                    <div style={{ fontSize: '10px', fontWeight: 600, color: '#94a3b8', marginBottom: '3px' }}>
                      Connected Edges ({incidentEdges.length})
                    </div>
                    {incidentEdges.length === 0 ? (
                      <div style={{ fontSize: '10px', color: '#6b7280' }}>No connected edges</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', maxHeight: '110px', overflowY: 'auto' }}>
                        {incidentEdges.map((e: any, idx: number) => {
                          const isTarget = e.target === selectedKnowledgeNode.id;
                          const other = isTarget ? e.source : e.target;
                          const dir = isTarget ? '←' : '→';
                          return (
                            <div key={idx} style={{ fontSize: '10px', color: '#9ca3af', display: 'flex', justifyContent: 'space-between' }}>
                              <span>{dir} [{e.type}]</span>
                              <span style={{ color: '#e2e8f0', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {other}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Scrollable Node List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto', maxHeight: '180px' }}>
                {filteredKnowledgeNodes.slice(0, 30).map((n: any) => {
                  const isSelected = selectedKnowledgeNode?.id === n.id;
                  return (
                    <div
                      key={n.id}
                      onClick={() => setSelectedKnowledgeNode(n)}
                      style={{
                        padding: '0.4rem 0.6rem',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '11px',
                        background: isSelected ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                        border: isSelected ? '1px solid #10b981' : '1px solid transparent',
                        color: isSelected ? '#34d399' : '#cbd5e1',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {n.label}
                      </span>
                      <span style={{ fontSize: '9px', color: '#6b7280' }}>
                        {n.domain || n.category}
                      </span>
                    </div>
                  );
                })}
                {filteredKnowledgeNodes.length > 30 && (
                  <div style={{ fontSize: '10px', color: '#6b7280', textAlign: 'center', padding: '4px' }}>
                    + {filteredKnowledgeNodes.length - 30} more (use search filter)
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
