/**
 * API configuration
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

// Default API key (for POC - should be configurable)
export const DEFAULT_API_KEY = import.meta.env.VITE_API_KEY || 'key1';
