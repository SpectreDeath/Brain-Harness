import React, { useState } from 'react';
import { Sparkles, X } from 'lucide-react';

interface CreatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScaffold: (params: {
    name: string;
    language: string;
    preset: string;
    isolation: string;
    tools: string[];
    description: string;
  }) => Promise<void>;
}

export const CreatorModal: React.FC<CreatorModalProps> = ({
  isOpen,
  onClose,
  onScaffold,
}) => {
  const [name, setName] = useState('');
  const [language, setLanguage] = useState('python');
  const [preset, setPreset] = useState('general');
  const [isolation, setIsolation] = useState('subprocess');
  const [tools, setTools] = useState('execute');
  const [description, setDescription] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (!name.trim() || isBusy) return;
    setIsBusy(true);
    try {
      const toolsList = tools.split(',').map((t) => t.trim()).filter(Boolean);
      await onScaffold({
        name,
        language,
        preset,
        isolation,
        tools: toolsList.length ? toolsList : ['execute'],
        description,
      });
      onClose();
    } finally {
      setIsBusy(false);
    }
  };

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
          maxWidth: '720px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>✨ Plugin Creator & Scaffolder</h2>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Plugin Name *
            </label>
            <input
              type="text"
              placeholder="e.g. data_cleaner"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="agent-input"
            />
          </div>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Implementation Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="agent-input"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Archetype Preset
            </label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="agent-input"
            >
              <option value="general">General Plugin</option>
              <option value="tool">LLM Skill / Tool</option>
              <option value="api_wrapper">API Wrapper (httpx)</option>
              <option value="service">Service Provider</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              Sandbox Isolation Mode
            </label>
            <select
              value={isolation}
              onChange={(e) => setIsolation(e.target.value)}
              className="agent-input"
            >
              <option value="subprocess">Subprocess (Default)</option>
              <option value="venv">Isolated Venv</option>
              <option value="in_process">In-Process (Trusted)</option>
              <option value="docker">Docker Container</option>
            </select>
          </div>
        </div>

        <div>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
            Tools / Entrypoints (comma-separated)
          </label>
          <input
            type="text"
            placeholder="e.g. clean_csv,validate_json"
            value={tools}
            onChange={(e) => setTools(e.target.value)}
            className="agent-input"
          />
        </div>

        <div>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
            Description
          </label>
          <input
            type="text"
            placeholder="Provides data processing capabilities"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="agent-input"
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
          <button className="btn btn-outline" onClick={onClose}>
            Cancel
          </button>
          <button className="btn" onClick={handleSubmit} disabled={isBusy || !name.trim()}>
            <Sparkles size={14} />
            <span>{isBusy ? 'Scaffolding...' : 'Scaffold & Auto-Mount'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
