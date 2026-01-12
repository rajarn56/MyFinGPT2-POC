/**
 * Chat interface component
 */

import React, { useState } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ProgressVisualization } from '../Progress/ProgressVisualization';
import { useAppContext } from '../../context/AppContext';
import './ChatInterface.css';

export const ChatInterface: React.FC = () => {
  const { messages, isLoading, sendMessage, progress } = useAppContext();
  const [showProgress, setShowProgress] = useState(false);

  return (
    <div className="flex flex-col h-full chat-interface">
      <div className="border-b p-4 bg-gray-50 chat-interface__header">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Chat</h2>
          {progress && (
            <button
              onClick={() => setShowProgress(!showProgress)}
              className="chat-interface__progress-toggle"
              aria-label="Toggle progress visualization"
            >
              {showProgress ? 'Hide' : 'Show'} Progress
            </button>
          )}
        </div>
      </div>
      {showProgress && progress && (
        <div className="chat-interface__progress">
          <ProgressVisualization />
        </div>
      )}
      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};
