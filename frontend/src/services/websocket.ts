/**
 * WebSocket client for real-time progress updates
 */

import { ProgressUpdate } from '../types';
import { WS_BASE_URL } from '../config/api';

type ProgressCallback = (update: ProgressUpdate) => void;
type ErrorCallback = (error: Event) => void;
type CloseCallback = () => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private reconnectTimer: number | null = null;
  private isManualClose = false;

  private progressCallbacks: Set<ProgressCallback> = new Set();
  private errorCallbacks: Set<ErrorCallback> = new Set();
  private closeCallbacks: Set<CloseCallback> = new Set();

  constructor() {
    this.url = WS_BASE_URL;
  }

  /**
   * Connect to WebSocket
   */
  connect(sessionId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      if (this.sessionId === sessionId) {
        return; // Already connected to this session
      }
      this.disconnect();
    }

    this.sessionId = sessionId;
    this.isManualClose = false;
    this.reconnectAttempts = 0;

    this.attemptConnect();
  }

  private attemptConnect(): void {
    if (!this.sessionId) {
      return;
    }

    try {
      const wsUrl = `${this.url}/ws/progress/${this.sessionId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress_update') {
            this.progressCallbacks.forEach((callback) => callback(data));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.errorCallbacks.forEach((callback) => callback(error));
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.closeCallbacks.forEach((callback) => callback());

        // Attempt to reconnect if not manually closed
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          this.reconnectTimer = window.setTimeout(() => {
            this.attemptConnect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.errorCallbacks.forEach((callback) => error as Event);
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.isManualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
  }

  /**
   * Subscribe to progress updates
   */
  onProgress(callback: ProgressCallback): () => void {
    this.progressCallbacks.add(callback);
    return () => {
      this.progressCallbacks.delete(callback);
    };
  }

  /**
   * Subscribe to errors
   */
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.add(callback);
    return () => {
      this.errorCallbacks.delete(callback);
    };
  }

  /**
   * Subscribe to close events
   */
  onClose(callback: CloseCallback): () => void {
    this.closeCallbacks.add(callback);
    return () => {
      this.closeCallbacks.delete(callback);
    };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
