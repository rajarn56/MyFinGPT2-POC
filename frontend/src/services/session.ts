/**
 * Session management service
 */

import { SessionResponse } from '../types';
import { apiClient } from './api';

const SESSION_STORAGE_KEY = 'myfingpt_session';
const SESSION_ID_STORAGE_KEY = 'myfingpt_session_id';

export interface StoredSession {
  sessionId: string;
  expiresAt: string;
  createdAt: string;
}

class SessionService {
  /**
   * Get stored session from localStorage
   */
  getStoredSession(): StoredSession | null {
    try {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY);
      if (!stored) {
        return null;
      }

      const session: StoredSession = JSON.parse(stored);

      // Check if session is expired
      if (new Date(session.expiresAt) < new Date()) {
        this.clearSession();
        return null;
      }

      return session;
    } catch (error) {
      console.error('Error reading session from storage:', error);
      return null;
    }
  }

  /**
   * Store session in localStorage
   */
  storeSession(session: SessionResponse): void {
    try {
      const stored: StoredSession = {
        sessionId: session.session_id,
        expiresAt: session.expires_at,
        createdAt: new Date().toISOString(),
      };
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(stored));
      localStorage.setItem(SESSION_ID_STORAGE_KEY, session.session_id);
    } catch (error) {
      console.error('Error storing session:', error);
    }
  }

  /**
   * Clear session from localStorage
   */
  clearSession(): void {
    localStorage.removeItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(SESSION_ID_STORAGE_KEY);
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return localStorage.getItem(SESSION_ID_STORAGE_KEY);
  }

  /**
   * Create or retrieve session
   */
  async getOrCreateSession(apiKey?: string): Promise<string> {
    // Check for existing valid session
    const stored = this.getStoredSession();
    if (stored) {
      // Verify session is still valid
      try {
        await apiClient.getSessionStatus(stored.sessionId);
        return stored.sessionId;
      } catch (error) {
        // Session invalid, create new one
        this.clearSession();
      }
    }

    // Create new session
    const response = await apiClient.createSession(apiKey);
    this.storeSession(response);
    return response.session_id;
  }
}

export const sessionService = new SessionService();
