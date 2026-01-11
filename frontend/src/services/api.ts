/**
 * API client for REST endpoints
 */

import {
  SessionResponse,
  SessionStatus,
  ExecuteRequest,
  ExecuteResponse,
  HealthResponse,
} from '../types';
import { API_BASE_URL, DEFAULT_API_KEY } from '../config/api';

class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.apiKey = DEFAULT_API_KEY;
  }

  setApiKey(apiKey: string) {
    this.apiKey = apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Create a session from API key
   */
  async createSession(apiKey?: string): Promise<SessionResponse> {
    const key = apiKey || this.apiKey;
    return this.request<SessionResponse>('/auth/session', {
      method: 'POST',
      headers: {
        'X-API-Key': key,
      },
    });
  }

  /**
   * Get session status
   */
  async getSessionStatus(sessionId: string): Promise<SessionStatus> {
    return this.request<SessionStatus>('/auth/status', {
      method: 'GET',
      headers: {
        'X-Session-ID': sessionId,
      },
    });
  }

  /**
   * Execute agent workflow
   */
  async executeAgents(
    sessionId: string,
    request: ExecuteRequest
  ): Promise<ExecuteResponse> {
    return this.request<ExecuteResponse>('/api/agents/execute', {
      method: 'POST',
      headers: {
        'X-Session-ID': sessionId,
      },
      body: JSON.stringify(request),
    });
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health/');
  }
}

export const apiClient = new ApiClient();
