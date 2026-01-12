/**
 * Results Panel component with tab navigation
 * Displays analysis results in tabs: Report, Visualizations, Activity, Citations
 */

import React, { useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import { AnalysisReport } from './AnalysisReport';
import { Visualizations } from './Visualizations';
import { AgentActivity } from './AgentActivity';
import { CitationsPanel } from './CitationsPanel';
import { Loading } from '../ui/Loading';
import './ResultsPanel.css';

type TabType = 'report' | 'visualizations' | 'activity' | 'citations';

export const ResultsPanel: React.FC = () => {
  const { currentAnalysis, isLoading } = useAppContext();
  const [activeTab, setActiveTab] = useState<TabType>('report');

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loading message="Generating analysis..." />
      </div>
    );
  }

  if (!currentAnalysis) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <p>Analysis results will appear here</p>
      </div>
    );
  }

  return (
    <div className="results-panel">
      <div className="results-panel__header">
        <div className="results-panel__tabs" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === 'report'}
            className={`results-panel__tab ${
              activeTab === 'report' ? 'results-panel__tab--active' : ''
            }`}
            onClick={() => setActiveTab('report')}
          >
            Report
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'visualizations'}
            className={`results-panel__tab ${
              activeTab === 'visualizations' ? 'results-panel__tab--active' : ''
            }`}
            onClick={() => setActiveTab('visualizations')}
          >
            Visualizations
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'activity'}
            className={`results-panel__tab ${
              activeTab === 'activity' ? 'results-panel__tab--active' : ''
            }`}
            onClick={() => setActiveTab('activity')}
          >
            Activity
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'citations'}
            className={`results-panel__tab ${
              activeTab === 'citations' ? 'results-panel__tab--active' : ''
            }`}
            onClick={() => setActiveTab('citations')}
          >
            Citations
          </button>
        </div>
      </div>
      <div className="results-panel__content">
        {activeTab === 'report' && (
          <AnalysisReport analysis={currentAnalysis} />
        )}
        {activeTab === 'visualizations' && (
          <Visualizations analysis={currentAnalysis} />
        )}
        {activeTab === 'activity' && (
          <AgentActivity analysis={currentAnalysis} />
        )}
        {activeTab === 'citations' && (
          <CitationsPanel analysis={currentAnalysis} />
        )}
      </div>
    </div>
  );
};
