import type {
  AgentSession,
  HarnessEvent,
  HarnessSandbox,
  HarnessStatus,
  HarnessTool,
  SkillRouteResult,
  SwarmRun,
} from '../types/harness';

const API_BASE = '/api';

export const api = {
  async getStatus(): Promise<HarnessStatus> {
    const res = await fetch(`${API_BASE}/status`);
    return res.json();
  },

  async getMetrics(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/metrics`);
    return res.json();
  },

  async getPlugins(): Promise<{ plugins: Record<string, string> }> {
    const res = await fetch(`${API_BASE}/plugins`);
    return res.json();
  },

  async getTools(): Promise<{ tools: HarnessTool[] }> {
    const res = await fetch(`${API_BASE}/tools`);
    return res.json();
  },

  async togglePlugin(name: string, action: 'enable' | 'disable'): Promise<{ status: string; state?: string }> {
    const res = await fetch(`${API_BASE}/plugins/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, action }),
    });
    return res.json();
  },

  async toggleTool(name: string, enabled: boolean): Promise<{ status: string; enabled?: boolean }> {
    const res = await fetch(`${API_BASE}/tools/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, enabled }),
    });
    return res.json();
  },

  async enableAllPlugins(): Promise<any> {
    const res = await fetch(`${API_BASE}/plugins/enable-all`, { method: 'POST' });
    return res.json();
  },

  async disableAllPlugins(): Promise<any> {
    const res = await fetch(`${API_BASE}/plugins/disable-all`, { method: 'POST' });
    return res.json();
  },

  async getPluginGuide(name: string): Promise<any> {
    const res = await fetch(`${API_BASE}/plugins/${encodeURIComponent(name)}/guide`);
    return res.json();
  },

  async ingestPlugin(source: string, ref: string = 'main'): Promise<any> {
    const res = await fetch(`${API_BASE}/plugins/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, ref }),
    });
    return res.json();
  },

  async uploadPluginZip(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/plugins/upload`, {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },

  async scaffoldPlugin(params: {
    name: string;
    language: string;
    preset: string;
    isolation: string;
    tools: string[];
    description: string;
  }): Promise<any> {
    const res = await fetch(`${API_BASE}/creator/scaffold`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...params, auto_enable: true }),
    });
    return res.json();
  },

  async getSandboxes(): Promise<{ sandboxes: HarnessSandbox[]; total: number }> {
    const res = await fetch(`${API_BASE}/sandboxes`);
    return res.json();
  },

  async getTimeline(limit: number = 200): Promise<{ events: HarnessEvent[]; total: number; summary: any }> {
    const res = await fetch(`${API_BASE}/timeline?limit=${limit}`);
    return res.json();
  },

  async getGraph(): Promise<{ mermaid: string }> {
    const res = await fetch(`${API_BASE}/graph`);
    return res.json();
  },

  async runAgentTask(task: string, maxSteps: number = 10): Promise<any> {
    const res = await fetch(`${API_BASE}/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, max_steps: maxSteps }),
    });
    return res.json();
  },

  async getSessions(): Promise<{ sessions: AgentSession[]; total: number }> {
    const res = await fetch(`${API_BASE}/sessions`);
    return res.json();
  },

  async exportSession(sessionId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}/export?format=json`);
    return res.json();
  },

  async getSwarmRuns(): Promise<{ runs: SwarmRun[]; total: number }> {
    const res = await fetch(`${API_BASE}/swarm/runs`);
    return res.json();
  },

  async runSwarm(objective: string, maxTokens: number = 50000, consensusThreshold: number = 0.66): Promise<any> {
    const res = await fetch(`${API_BASE}/swarm/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        objective,
        max_tokens: maxTokens,
        consensus_threshold: consensusThreshold,
      }),
    });
    return res.json();
  },

  async getSwarmRunTree(runId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/swarm/runs/${encodeURIComponent(runId)}/tree`);
    return res.json();
  },

  async getSkills(): Promise<any> {
    const res = await fetch(`${API_BASE}/skills`);
    return res.json();
  },

  async routeSkills(intent: string, topK: number = 3): Promise<SkillRouteResult> {
    const res = await fetch(`${API_BASE}/skills/route?intent=${encodeURIComponent(intent)}&top_k=${topK}`);
    return res.json();
  },

  async findSkillChain(start: string, target: string): Promise<any> {
    const res = await fetch(`${API_BASE}/skills/chain?start=${encodeURIComponent(start)}&target=${encodeURIComponent(target)}`);
    return res.json();
  },

  async getSkillTopology(skillName: string): Promise<any> {
    const res = await fetch(`${API_BASE}/skills/${encodeURIComponent(skillName)}/topology`);
    return res.json();
  },
};
