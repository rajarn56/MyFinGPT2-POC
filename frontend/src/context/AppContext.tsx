/**
 * Application context for state management
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { ChatMessage, ExecuteResponse, ProgressUpdate } from '../types';
import { apiClient } from '../services/api';
import { wsClient } from '../services/websocket';
import { sessionService } from '../services/session';

interface AppContextType {
  // Session
  sessionId: string | null;
  initializeSession: () => Promise<void>;

  // Messages
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;

  // Current analysis
  currentAnalysis: ExecuteResponse | null;
  setCurrentAnalysis: (analysis: ExecuteResponse | null) => void;

  // Progress
  progress: ProgressUpdate | null;
  setProgress: (progress: ProgressUpdate | null) => void;

  // Loading state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Send message
  sendMessage: (query: string, symbols: string[]) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

interface AppProviderProps {
  children: React.ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentAnalysis, setCurrentAnalysis] = useState<ExecuteResponse | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

  // Set up WebSocket connection when session is available
  useEffect(() => {
    if (sessionId) {
      wsClient.connect(sessionId);
      const unsubscribe = wsClient.onProgress((update) => {
        setProgress(update);
      });

      return () => {
        unsubscribe();
        wsClient.disconnect();
      };
    }
  }, [sessionId]);

  const initializeSession = useCallback(async () => {
    try {
      const id = await sessionService.getOrCreateSession();
      setSessionId(id);
    } catch (error) {
      console.error('Failed to initialize session:', error);
    }
  }, []);

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const sendMessage = useCallback(
    async (query: string, symbols: string[]) => {
      if (!sessionId) {
        await initializeSession();
        return;
      }

      setIsLoading(true);
      setProgress(null);

      // Add user message
      const userMessage: ChatMessage = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content: query,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMessage);

      try {
        const response = await apiClient.executeAgents(sessionId, {
          query,
          symbols,
        });

        setCurrentAnalysis(response);

        // Add assistant message with summary (or fallback to report if summary not available)
        const messageContent = response.result.summary || response.result.report;
        if (messageContent) {
          const assistantMessage: ChatMessage = {
            id: `msg_${Date.now() + 1}`,
            role: 'assistant',
            content: messageContent,
            timestamp: new Date().toISOString(),
            transaction_id: response.transaction_id,
          };
          addMessage(assistantMessage);
        }
      } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage: ChatMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to process request'}`,
          timestamp: new Date().toISOString(),
        };
        addMessage(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, initializeSession, addMessage]
  );

  return (
    <AppContext.Provider
      value={{
        sessionId,
        initializeSession,
        messages,
        addMessage,
        clearMessages,
        currentAnalysis,
        setCurrentAnalysis,
        progress,
        setProgress,
        isLoading,
        setIsLoading,
        sendMessage,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};
