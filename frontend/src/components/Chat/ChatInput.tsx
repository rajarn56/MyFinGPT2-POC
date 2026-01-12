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

    // Extract stock symbols from input (for UI feedback only)
    // Backend will handle intelligent extraction using LLM
    const symbols = extractSymbols(input);

    // Log extracted symbols for debugging
    if (symbols.length > 0) {
      console.log('Frontend extracted symbols:', symbols);
    } else {
      console.log('No symbols extracted by frontend - backend will handle extraction');
    }

    // Always send query - backend will extract symbols if frontend didn't find any
    onSend(input.trim(), symbols);
    setInput('');
  };

  const extractSymbols = (text: string): string[] => {
    // Common words to filter out
    const commonWords = new Set([
      'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS',
      'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY',
      'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'WAY', 'USE', 'SHE', 'MAN', 'HAD'
    ]);

    const symbols: string[] = [];
    
    // First, try to extract from parenthetical notation: "Company (SYMBOL)"
    const parentheticalPattern = /\(([A-Z]{1,5})\)/gi;
    const parentheticalMatches = text.match(parentheticalPattern);
    if (parentheticalMatches) {
      parentheticalMatches.forEach(match => {
        const symbol = match.slice(1, -1).toUpperCase(); // Remove parentheses
        if (symbol && !commonWords.has(symbol) && !symbols.includes(symbol)) {
          symbols.push(symbol);
        }
      });
    }
    
    // Then, extract standalone symbols (1-5 uppercase letters)
    const symbolPattern = /\b[A-Z]{1,5}\b/g;
    const matches = text.match(symbolPattern);
    if (matches) {
      matches.forEach(match => {
        const symbol = match.toUpperCase();
        // Filter out common words and already found symbols
        if (!commonWords.has(symbol) && !symbols.includes(symbol) && symbol.length >= 1 && symbol.length <= 5) {
          symbols.push(symbol);
        }
      });
    }
    
    return symbols;
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
