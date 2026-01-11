/**
 * Chat interface component
 */

import React from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useAppContext } from '../../context/AppContext';

export const ChatInterface: React.FC = () => {
  const { messages, isLoading, sendMessage } = useAppContext();

  return (
    <div className="flex flex-col h-full">
      <div className="border-b p-4 bg-gray-50">
        <h2 className="text-xl font-semibold">Chat</h2>
      </div>
      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};
