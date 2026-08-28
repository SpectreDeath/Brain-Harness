import React from 'react';
import type { ToastMessage } from '../types/harness';

interface ToastContainerProps {
  toasts: ToastMessage[];
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts }) => {
  return (
    <div style={{
      position: 'fixed',
      top: '1.5rem',
      right: '1.5rem',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      gap: '0.65rem',
      pointerEvents: 'none',
    }}>
      {toasts.map((toast) => {
        const borderColors = {
          success: 'var(--accent-emerald)',
          error: 'var(--accent-rose)',
          info: 'var(--accent-cyan)',
          warning: 'var(--accent-amber)',
        };
        const icons = {
          success: '✓',
          error: '✗',
          info: 'ℹ',
          warning: '⚠',
        };

        return (
          <div
            key={toast.id}
            style={{
              pointerEvents: 'auto',
              background: '#0f172a',
              border: '1px solid var(--border-color)',
              borderLeft: `4px solid ${borderColors[toast.type]}`,
              borderRadius: '10px',
              padding: '0.85rem 1.1rem',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.6)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              fontSize: '0.86rem',
              color: '#fff',
              maxWidth: '380px',
            }}
          >
            <span style={{ fontWeight: 'bold' }}>{icons[toast.type]}</span>
            <span>{toast.text}</span>
          </div>
        );
      })}
    </div>
  );
};
