import React, { useState } from 'react';
import { Upload, X } from 'lucide-react';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestUrl: (source: string, ref: string) => Promise<void>;
  onUploadZip: (file: File) => Promise<void>;
}

export const IngestModal: React.FC<IngestModalProps> = ({
  isOpen,
  onClose,
  onIngestUrl,
  onUploadZip,
}) => {
  const [tab, setTab] = useState<'url' | 'zip'>('url');
  const [source, setSource] = useState('');
  const [ref, setRef] = useState('main');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  if (!isOpen) return null;

  const handleSubmitUrl = async () => {
    if (!source.trim() || isBusy) return;
    setIsBusy(true);
    try {
      await onIngestUrl(source, ref);
      onClose();
    } finally {
      setIsBusy(false);
    }
  };

  const handleSubmitZip = async () => {
    if (!selectedFile || isBusy) return;
    setIsBusy(true);
    try {
      await onUploadZip(selectedFile);
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
          maxWidth: '560px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>Universal Plugin Ingestion</h2>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {/* Tab switch */}
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
          <button
            onClick={() => setTab('url')}
            style={{
              background: tab === 'url' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: tab === 'url' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: '6px',
              padding: '0.4rem 0.85rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            GitHub / Remote URL
          </button>
          <button
            onClick={() => setTab('zip')}
            style={{
              background: tab === 'zip' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: tab === 'zip' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: '6px',
              padding: '0.4rem 0.85rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            Upload ZIP Archive
          </button>
        </div>

        {tab === 'url' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                Source (GitHub repo, PyPI or URL)
              </label>
              <input
                type="text"
                placeholder="e.g. owner/repo or https://github.com/owner/repo"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="agent-input"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
                Git Branch / Ref
              </label>
              <input
                type="text"
                value={ref}
                onChange={(e) => setRef(e.target.value)}
                className="agent-input"
              />
            </div>
            <button className="btn" onClick={handleSubmitUrl} disabled={isBusy}>
              <Upload size={14} />
              <span>{isBusy ? 'Ingesting...' : 'Ingest & Sandboxed Activate'}</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div
              style={{
                border: '2px dashed var(--border-color)',
                borderRadius: '10px',
                padding: '2rem',
                textAlign: 'center',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
              onClick={() => document.getElementById('zipFileInput')?.click()}
            >
              <input
                id="zipFileInput"
                type="file"
                accept=".zip"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files && setSelectedFile(e.target.files[0])}
              />
              <Upload size={28} style={{ margin: '0 auto 0.5rem', opacity: 0.7 }} />
              <div>{selectedFile ? `Selected: ${selectedFile.name}` : 'Click or drop a plugin .zip archive here'}</div>
            </div>
            <button className="btn" onClick={handleSubmitZip} disabled={!selectedFile || isBusy}>
              <Upload size={14} />
              <span>{isBusy ? 'Uploading...' : 'Upload & Mount Plugin'}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
