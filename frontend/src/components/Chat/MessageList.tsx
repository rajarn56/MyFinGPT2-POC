/**
 * Message list component
 */

import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatMessage } from '../../types';
import { Loading } from '../ui/Loading';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full text-gray-500">
          <p>Start a conversation by asking about a stock or company</p>
        </div>
      )}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isLoading && (
        <div className="flex justify-start mb-4">
          <div className="bg-gray-100 rounded-lg px-4 py-2">
            <Loading message="Analyzing..." />
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
