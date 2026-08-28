import React, { useState } from 'react';
import { marked } from 'marked';
import { BookOpen, Code, X } from 'lucide-react';

interface GuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  pluginName: string;
  guideText?: string;
  cardText?: string;
}

export const GuideModal: React.FC<GuideModalProps> = ({
  isOpen,
  onClose,
  pluginName,
  guideText,
  cardText,
}) => {
  const [tab, setTab] = useState<'doc' | 'card'>('doc');

  if (!isOpen) return null;

  const htmlContent = guideText ? marked.parse(guideText) : '<p>No guide documentation available.</p>';

  return (
    <div
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(3, 6, 15, 0.82)',
        backdropFilter: 'blur(10px)',
        zIndex: 300,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#0c1324',
          border: '1px solid var(--border-light)',
          borderRadius: '16px',
          padding: '1.75rem',
          width: '100%',
          maxWidth: '780px',
          maxHeight: '85vh',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>
            📖 Plugin Documentation: <span className="text-code-cyan">{pluginName}</span>
          </h2>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {/* Tab switch */}
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
          <button
            onClick={() => setTab('doc')}
            style={{
              background: tab === 'doc' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: tab === 'doc' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: '6px',
              padding: '0.4rem 0.85rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <BookOpen size={14} />
            <span>Quick Start Guide</span>
          </button>
          <button
            onClick={() => setTab('card')}
            style={{
              background: tab === 'card' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: tab === 'card' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: '6px',
              padding: '0.4rem 0.85rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Code size={14} />
            <span>Summary Card Schema</span>
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', maxHeight: '55vh', paddingRight: '0.5rem' }}>
          {tab === 'doc' ? (
            <div
              style={{ fontSize: '0.88rem', lineHeight: 1.6, color: '#cbd5e1' }}
              dangerouslySetInnerHTML={{ __html: htmlContent }}
            />
          ) : (
            <pre style={{
              background: '#040711',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              fontFamily: "'Fira Code', monospace",
              fontSize: '0.82rem',
              color: 'var(--accent-cyan)',
              overflowX: 'auto',
            }}>
              {cardText || 'No manifest summary card available.'}
            </pre>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
          <button className="btn btn-outline" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
