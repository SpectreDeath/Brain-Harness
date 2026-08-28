export interface HarnessStatus {
  status: string;
  plugins: Record<string, string>;
  plugins_count: number;
  services: Record<string, string>;
  services_count: number;
  tools: string[];
  tools_count: number;
}

export interface HarnessTool {
  name: string;
  provider: string;
  description: string;
  enabled: boolean;
  parameters?: Record<string, any>;
}

export interface HarnessPluginGuide {
  status: string;
  name: string;
  guide?: string;
  card?: string;
  manifest?: Record<string, any>;
}

export interface HarnessSandbox {
  plugin: string;
  executor: string;
  is_running: boolean;
  pid: number | null;
  trusted: boolean;
}

export interface HarnessEvent {
  id: string;
  timestamp: string;
  event_type: string;
  source: string;
  payload: Record<string, any>;
}

export interface AgentSession {
  id?: string;
  session_id?: string;
  status: string;
  steps_count?: number;
  steps?: any[];
  task?: string;
  final_answer?: string;
  created_at?: string;
}

export interface SwarmRun {
  run_id?: string;
  id?: string;
  objective: string;
  status: string;
  consensus_score?: number;
  total_tokens?: number;
  rounds?: number;
  final_answer?: string;
}

export interface SkillMatch {
  skill_name: string;
  category: string;
  confidence: number;
  matched_triggers?: string[];
}

export interface SkillRouteResult {
  intent: string;
  matches: SkillMatch[];
  recommended_chain: string[];
}

export interface SkillTopology {
  skill: {
    name: string;
    version: string;
    category: string;
    invocation: string;
    target: string;
    description: string;
  };
  prerequisites: string[];
  downstream_handoffs: string[];
  mitigated_anti_patterns: string[];
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  text: string;
}
