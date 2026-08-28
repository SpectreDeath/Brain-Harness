import React, { useEffect, useRef } from 'react';
import { Network, RefreshCw } from 'lucide-react';

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

  useEffect(() => {
    if (window.mermaid && containerRef.current) {
      containerRef.current.innerHTML = `<div class="mermaid">${mermaidCode || 'graph TD\n  Harness[Harness Core]'}</div>`;
      try {
        window.mermaid.run({ nodes: containerRef.current.querySelectorAll('.mermaid') });
      } catch (err) {
        console.error('Mermaid render error', err);
      }
    }
  }, [mermaidCode]);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <Network size={18} color="var(--accent-purple)" />
            <span>Micro-Kernel Component & Dependency Graph</span>
          </div>
          <button className="btn btn-outline btn-xs" onClick={onRefresh}>
            <RefreshCw size={12} />
            <span>Re-render</span>
          </button>
        </div>

        <div
          ref={containerRef}
          style={{
            background: '#040711',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '1.5rem',
            minHeight: '480px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'auto',
          }}
        >
          <div className="text-muted-sm">Loading graph...</div>
        </div>
      </div>
    </div>
  );
};
