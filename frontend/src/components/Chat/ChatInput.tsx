/**
 * Chat input component
 */

import React, { useState, KeyboardEvent } from 'react';
import { Button } from '../ui/Button';

interface ChatInputProps {
  onSend: (message: string, symbols: string[]) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim() || disabled) {
      return;
    }

    // Extract stock symbols from input (simple pattern matching)
    const symbolPattern = /\b[A-Z]{1,5}\b/g;
    const symbols = Array.from(new Set(input.match(symbolPattern) || []));

    onSend(input.trim(), symbols);
    setInput('');
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t p-4 bg-white">
      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about a stock or company (e.g., Analyze AAPL)"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          rows={3}
          disabled={disabled}
        />
        <Button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="self-end"
        >
          Send
        </Button>
      </div>
    </div>
  );
};
