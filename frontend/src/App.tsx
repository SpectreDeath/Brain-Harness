import { useEffect, useState } from 'react';
import { CommandPalette } from './components/CommandPalette';
import { Header } from './components/Header';
import { Sidebar, type ViewType } from './components/Sidebar';
import { ToastContainer } from './components/ToastContainer';
import { CreatorModal } from './modals/CreatorModal';
import { GuideModal } from './modals/GuideModal';
import { IngestModal } from './modals/IngestModal';
import { api } from './services/api';
import type {
  AgentSession,
  HarnessEvent,
  HarnessSandbox,
  HarnessStatus,
  HarnessTool,
  SwarmRun,
  ToastMessage,
} from './types/harness';
import { AgentView } from './views/AgentView';
import { GraphView } from './views/GraphView';
import { OverviewView } from './views/OverviewView';
import { PluginsView } from './views/PluginsView';
import { SandboxesView } from './views/SandboxesView';
import { SkillsView } from './views/SkillsView';
import { SwarmView } from './views/SwarmView';
import { TimelineView } from './views/TimelineView';

export function App() {
  const [activeView, setActiveView] = useState<ViewType>('overview');
  const [wsConnected, setWsConnected] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const [status, setStatus] = useState<HarnessStatus | null>(null);
  const [metrics, setMetrics] = useState<Record<string, any> | null>(null);
  const [tools, setTools] = useState<HarnessTool[]>([]);
  const [sandboxes, setSandboxes] = useState<HarnessSandbox[]>([]);
  const [events, setEvents] = useState<HarnessEvent[]>([]);
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [swarmRuns, setSwarmRuns] = useState<SwarmRun[]>([]);
  const [mermaidCode, setMermaidCode] = useState('');

  // Modals
  const [isCmdOpen, setIsCmdOpen] = useState(false);
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isCreatorOpen, setIsCreatorOpen] = useState(false);
  const [guideData, setGuideData] = useState<{ isOpen: boolean; name: string; guide?: string; card?: string }>({
    isOpen: false,
    name: '',
  });

  const showToast = (text: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // Data Loading
  const loadAll = async () => {
    try {
      const [st, mt, tl, sb, gr] = await Promise.all([
        api.getStatus().catch(() => null),
        api.getMetrics().catch(() => null),
        api.getTools().catch(() => ({ tools: [] })),
        api.getSandboxes().catch(() => ({ sandboxes: [], total: 0 })),
        api.getGraph().catch(() => ({ mermaid: '' })),
      ]);

      if (st) setStatus(st);
      if (mt) setMetrics(mt);
      if (tl) setTools(tl.tools || []);
      if (sb) setSandboxes(sb.sandboxes || []);
      if (gr) setMermaidCode(gr.mermaid || '');
    } catch (err) {
      console.error('Error loading data', err);
    }
  };

  const loadSessions = async () => {
    try {
      const res = await api.getSessions();
      setSessions(res.sessions || []);
    } catch (err) {}
  };

  const loadSwarmRuns = async () => {
    try {
      const res = await api.getSwarmRuns();
      setSwarmRuns(res.runs || []);
    } catch (err) {}
  };

  const loadTimeline = async () => {
    try {
      const res = await api.getTimeline();
      setEvents(res.events || []);
    } catch (err) {}
  };

  // WebSocket Live Broadcast
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/events`;
    let ws: WebSocket;

    const connect = () => {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'event' && msg.data) {
            setEvents((prev) => [...prev, msg.data]);
          }
        } catch (err) {}
      };
    };

    connect();
    loadAll();
    loadSessions();
    loadSwarmRuns();
    loadTimeline();

    const interval = setInterval(() => {
      if (activeView === 'overview') loadAll();
    }, 8000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, []);

  // Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCmdOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <div className="ambient-glow" />
      <div className="ambient-glow-2" />

      {/* Toast Notification Center */}
      <ToastContainer toasts={toasts} />

      {/* Sidebar Navigation */}
      <Sidebar
        activeView={activeView}
        onSelectView={setActiveView}
        pluginsCount={status?.plugins_count ?? 0}
        onOpenCmdPalette={() => setIsCmdOpen(true)}
      />

      {/* Main View Area */}
      <div style={{
        marginLeft: 'var(--sidebar-width)',
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        zIndex: 10,
        width: 'calc(100% - var(--sidebar-width))',
      }}>
        <Header
          activeView={activeView}
          wsConnected={wsConnected}
          onOpenCreator={() => setIsCreatorOpen(true)}
          onOpenIngest={() => setIsIngestOpen(true)}
          onOpenCmdPalette={() => setIsCmdOpen(true)}
        />

        <main style={{ flex: 1, padding: '1.75rem 2rem 3rem', maxWidth: '1700px', width: '100%', margin: '0 auto' }}>
          {activeView === 'overview' && (
            <OverviewView
              status={status}
              metrics={metrics}
              sandboxesCount={sandboxes.filter((s) => s.is_running).length}
              events={events}
              onRefresh={loadAll}
              onClearStream={() => setEvents([])}
            />
          )}

          {activeView === 'timeline' && (
            <TimelineView
              events={events}
              onFetchWindow={loadTimeline}
            />
          )}

          {activeView === 'graph' && (
            <GraphView
              mermaidCode={mermaidCode}
              onRefresh={loadAll}
            />
          )}

          {activeView === 'agent' && (
            <AgentView
              sessions={sessions}
              onRunTask={async (task, maxSteps) => {
                const res = await api.runAgentTask(task, maxSteps);
                loadSessions();
                showToast('Agent mission finished', 'success');
                return res;
              }}
              onExportSession={async (sid) => {
                const res = await api.exportSession(sid);
                const blob = new Blob([res.content || JSON.stringify(res, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `session_${sid}.json`;
                a.click();
                showToast('Session exported', 'success');
              }}
              onRefreshSessions={loadSessions}
            />
          )}

          {activeView === 'swarm' && (
            <SwarmView
              runs={swarmRuns}
              onLaunchSwarm={async (obj, tok, con) => {
                const res = await api.runSwarm(obj, tok, con);
                showToast('Swarm consensus run finished', 'success');
                loadSwarmRuns();
                return res;
              }}
              onInspectTree={async (rid) => {
                const res = await api.getSwarmRunTree(rid);
                alert(JSON.stringify(res.tree || res, null, 2));
              }}
              onRefreshRuns={loadSwarmRuns}
            />
          )}

          {activeView === 'skills' && (
            <SkillsView
              onRouteIntent={(intent) => api.routeSkills(intent)}
              onFindChain={(start, target) => api.findSkillChain(start, target)}
              onRefreshGraph={loadAll}
            />
          )}

          {activeView === 'plugins' && (
            <PluginsView
              plugins={status?.plugins || {}}
              tools={tools}
              onTogglePlugin={async (name, action) => {
                await api.togglePlugin(name, action);
                showToast(`Plugin '${name}' ${action}d`, 'info');
                loadAll();
              }}
              onToggleTool={async (toolName, enabled) => {
                await api.toggleTool(toolName, enabled);
                showToast(`Tool '${toolName}' turned ${enabled ? 'ON' : 'OFF'}`, 'info');
                loadAll();
              }}
              onEnableAll={async () => {
                await api.enableAllPlugins();
                showToast('All plugins enabled', 'success');
                loadAll();
              }}
              onDisableAll={async () => {
                await api.disableAllPlugins();
                showToast('Non-core plugins disabled', 'warning');
                loadAll();
              }}
              onOpenGuide={async (name) => {
                try {
                  const res = await api.getPluginGuide(name);
                  setGuideData({ isOpen: true, name, guide: res.guide, card: res.card });
                } catch (e) {
                  showToast(`Failed loading guide: ${e}`, 'error');
                }
              }}
              onRefresh={loadAll}
            />
          )}

          {activeView === 'sandboxes' && (
            <SandboxesView
              sandboxes={sandboxes}
              onRefresh={loadAll}
            />
          )}
        </main>
      </div>

      {/* Global Modals */}
      <CommandPalette
        isOpen={isCmdOpen}
        onClose={() => setIsCmdOpen(false)}
        onSelectView={setActiveView}
        onOpenCreator={() => {
          setIsCmdOpen(false);
          setIsCreatorOpen(true);
        }}
        onOpenIngest={() => {
          setIsCmdOpen(false);
          setIsIngestOpen(true);
        }}
      />

      <IngestModal
        isOpen={isIngestOpen}
        onClose={() => setIsIngestOpen(false)}
        onIngestUrl={async (source, ref) => {
          const res = await api.ingestPlugin(source, ref);
          if (res.status === 'ok') {
            showToast(`Plugin '${res.plugin.name}' ingested successfully`, 'success');
            loadAll();
          } else {
            showToast(`Ingestion failed: ${res.error}`, 'error');
          }
        }}
        onUploadZip={async (file) => {
          const res = await api.uploadPluginZip(file);
          if (res.status === 'ok') {
            showToast(`Plugin '${res.plugin.name}' installed successfully`, 'success');
            loadAll();
          } else {
            showToast(`Upload failed: ${res.error}`, 'error');
          }
        }}
      />

      <CreatorModal
        isOpen={isCreatorOpen}
        onClose={() => setIsCreatorOpen(false)}
        onScaffold={async (params) => {
          const res = await api.scaffoldPlugin(params);
          if (res.status === 'ok') {
            showToast(`Plugin '${res.plugin.name}' scaffolded and mounted!`, 'success');
            loadAll();
          } else {
            showToast(`Scaffold failed: ${res.error}`, 'error');
          }
        }}
      />

      <GuideModal
        isOpen={guideData.isOpen}
        onClose={() => setGuideData({ isOpen: false, name: '' })}
        pluginName={guideData.name}
        guideText={guideData.guide}
        cardText={guideData.card}
      />
    </div>
  );
}

export default App;
