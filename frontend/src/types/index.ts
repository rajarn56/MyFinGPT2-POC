/**
 * Type definitions for MyFinGPT-POC-V2 Frontend
 */

export interface Session {
  session_id: string;
  user_id: string;
  created_at: string;
  expires_at: string;
  last_activity: string;
}

export interface SessionResponse {
  session_id: string;
  expires_at: string;
}

export interface SessionStatus {
  status: string;
  session: Session;
}

export interface ExecuteRequest {
  query: string;
  symbols: string[];
}

export interface Citation {
  source: string;
  symbol?: string;
  type: string;
  url?: string;
}

export interface TokenUsage {
  [agentName: string]: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ExecuteResponse {
  transaction_id: string;
  status: 'completed' | 'completed_with_errors' | 'failed';
  result: {
    research_data: Record<string, any>;
    analyst_data: Record<string, any>;
    report: string | null;
    summary: string | null;
    edgar_data: Record<string, any>;
    comparison_data: Record<string, any>;
    trend_analysis: Record<string, any>;
    query_type: string | null;
    citations: Citation[];
    errors: string[];
    token_usage: TokenUsage;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  transaction_id?: string;
}

export interface ProgressEvent {
  timestamp: string;
  agent: string;
  event_type: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface ProgressUpdate {
  type: 'progress_update';
  session_id: string;
  transaction_id: string;
  current_agent?: string;
  current_tasks: Record<string, string[]>;
  progress_events: ProgressEvent[];
  execution_order: Array<{
    agent: string;
    start_time: string;
    end_time?: string;
    status: 'running' | 'completed' | 'failed';
  }>;
  timestamp: string;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  services: {
    chroma: 'connected' | 'disconnected';
    neo4j: 'connected' | 'disconnected';
  };
}
