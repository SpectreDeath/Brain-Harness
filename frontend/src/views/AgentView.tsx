import React, { useState } from 'react';
import { Cpu, Download, Play, RefreshCw } from 'lucide-react';
import type { AgentSession } from '../types/harness';

interface AgentViewProps {
  sessions: AgentSession[];
  onRunTask: (task: string, maxSteps: number) => Promise<any>;
  onExportSession: (sessionId: string) => void;
  onRefreshSessions: () => void;
}

export const AgentView: React.FC<AgentViewProps> = ({
  sessions,
  onRunTask,
  onExportSession,
  onRefreshSessions,
}) => {
  const [taskPrompt, setTaskPrompt] = useState('Calculate sum of 40 and 2 using python surface');
  const [maxSteps, setMaxSteps] = useState(10);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    '> Agent loop ready. Standby for autonomous missions.',
  ]);

  const handleLaunch = async () => {
    if (!taskPrompt.trim() || isRunning) return;
    setIsRunning(true);
    setLogs((prev) => [...prev, `> 🚀 Mission Launched: ${taskPrompt}`]);

    try {
      const res = await onRunTask(taskPrompt, maxSteps);
      const isSuccess = res.task_status === 'completed' || res.status === 'ok';
      setLogs((prev) => [
        ...prev,
        `> ${isSuccess ? '✓' : '✗'} Outcome (${res.task_status || 'done'}): ${res.final_answer || res.error || 'Finished'}`,
      ]);
    } catch (err) {
      setLogs((prev) => [...prev, `> ✗ Error: ${err}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const presets = [
    { label: 'Math Computation', prompt: 'Calculate sum of 40 and 2 using python surface' },
    { label: 'System Inspection', prompt: 'Inspect registered services and active tools.registry' },
    { label: 'Reflect Architecture', prompt: 'Reflect on memory graph and topological skill dependencies' },
  ];

  return (
    <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.25rem' }}>
      {/* Agent Launcher & Console */}
      <div className="glass-card" style={{ gridColumn: 'span 7', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
          <Cpu size={18} color="var(--accent-purple)" />
          <span>Autonomous ReAct Agent Mission Control</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <textarea
            value={taskPrompt}
            onChange={(e) => setTaskPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                handleLaunch();
              }
            }}
            placeholder="Enter autonomous task description (Shift+Enter to run)..."
            className="agent-input"
            rows={3}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  className="btn btn-outline btn-xs"
                  onClick={() => setTaskPrompt(p.prompt)}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Steps:</span>
              <input
                type="number"
                min="1"
                max="30"
                value={maxSteps}
                onChange={(e) => setMaxSteps(parseInt(e.target.value, 10))}
                className="agent-input"
                style={{ width: '60px', padding: '0.3rem 0.5rem' }}
              />
              <button
                className="btn btn-sm"
                onClick={handleLaunch}
                disabled={isRunning}
              >
                <Play size={14} />
                <span>{isRunning ? 'Running...' : 'Launch Mission'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Console Box */}
        <div className="terminal-box" style={{ height: '380px' }}>
          {logs.map((log, idx) => (
            <div key={idx} className="log-line">
              <span style={{ color: log.includes('✓') ? 'var(--accent-emerald)' : log.includes('✗') ? 'var(--accent-rose)' : 'inherit' }}>
                {log}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Session History Explorer */}
      <div className="glass-card" style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>Session History & Artifacts</span>
          <button className="btn btn-outline btn-xs" onClick={onRefreshSessions}>
            <RefreshCw size={12} />
            <span>Refresh</span>
          </button>
        </div>

        <div style={{ maxHeight: '480px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem' }}>Session ID</th>
                <th style={{ padding: '0.5rem' }}>Status</th>
                <th style={{ padding: '0.5rem' }}>Steps</th>
                <th style={{ padding: '0.5rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)' }}>
                    No recorded sessions
                  </td>
                </tr>
              ) : (
                sessions.map((s, idx) => {
                  const sid = s.id || s.session_id || `session-${idx}`;
                  return (
                    <tr key={sid} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td className="text-code" style={{ padding: '0.6rem 0.5rem', fontSize: '0.78rem' }}>
                        {sid.substring(0, 10)}...
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        <span className={`pill ${s.status === 'completed' ? 'enabled' : 'disabled'}`}>
                          {s.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        {s.steps_count || s.steps?.length || 0}
                      </td>
                      <td style={{ padding: '0.6rem 0.5rem' }}>
                        <button
                          className="btn btn-outline btn-xs"
                          onClick={() => onExportSession(sid)}
                        >
                          <Download size={12} />
                          <span>JSON</span>
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
