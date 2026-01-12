/**
 * Main application layout
 */

import React from 'react';
import { TwoColumnLayout } from './TwoColumnLayout';
import { ChatInterface } from '../Chat/ChatInterface';
import { ResultsPanel } from '../Results/ResultsPanel';

export const AppLayout: React.FC = () => {
  return (
    <TwoColumnLayout
      left={<ChatInterface />}
      right={<ResultsPanel />}
    />
  );
};
