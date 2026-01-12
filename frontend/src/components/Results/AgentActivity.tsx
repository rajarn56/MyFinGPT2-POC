/**
 * Agent Activity component - displays agent execution metrics and token usage
 * This is the Activity tab content in ResultsPanel
 */

import React, { useMemo } from 'react';
import { ExecuteResponse } from '../../types';
import { useAppContext } from '../../context/AppContext';
import './AgentActivity.css';

interface AgentActivityProps {
  analysis: ExecuteResponse;
}

interface AgentActivityData {
  agents_executed: string[];
  token_usage: Record<string, number>;
  execution_time: Record<string, number>;
  context_size?: number;
  execution_timeline?: Array<{
    agent: string;
    start_time: string;
    end_time?: string;
    status: 'running' | 'completed' | 'failed';
    duration?: number;
  }>;
}

export const AgentActivity: React.FC<AgentActivityProps> = ({ analysis }) => {
  const { progress } = useAppContext();

  const activityData = useMemo<AgentActivityData>(() => {
    const tokenUsage = analysis.result.token_usage || {};
    const agents = Object.keys(tokenUsage);
    
    // Extract total tokens per agent
    const tokenUsagePerAgent: Record<string, number> = {};
    agents.forEach(agent => {
      const usage = tokenUsage[agent];
      if (usage && typeof usage === 'object') {
        tokenUsagePerAgent[agent] = usage.total_tokens || 0;
      } else if (typeof usage === 'number') {
        tokenUsagePerAgent[agent] = usage;
      }
    });

    // Calculate total tokens
    const totalTokens = Object.values(tokenUsagePerAgent).reduce((sum, tokens) => sum + tokens, 0);

    // Estimate context size from total tokens (rough approximation: 1 token ≈ 4 characters)
    const estimatedContextSize = totalTokens * 4;

    // Extract execution timeline from progress if available
    let executionTimeline: AgentActivityData['execution_timeline'] = undefined;
    if (progress?.execution_order) {
      executionTimeline = progress.execution_order.map(entry => {
        const startTime = new Date(entry.start_time);
        const endTime = entry.end_time ? new Date(entry.end_time) : undefined;
        const duration = endTime 
          ? (endTime.getTime() - startTime.getTime()) / 1000 
          : undefined;

        return {
          ...entry,
          duration,
        };
      });
    }

    // Calculate execution times from timeline
    const executionTime: Record<string, number> = {};
    if (executionTimeline) {
      executionTimeline.forEach(entry => {
        if (entry.duration !== undefined) {
          executionTime[entry.agent] = entry.duration;
        }
      });
    }

    return {
      agents_executed: agents.length > 0 ? agents : [],
      token_usage: tokenUsagePerAgent,
      execution_time: executionTime,
      context_size: estimatedContextSize,
      execution_timeline: executionTimeline,
    };
  }, [analysis, progress]);

  const formatTime = (seconds: number) => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(2)}M`;
    }
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1048576) {
      return `${(bytes / 1048576).toFixed(2)} MB`;
    }
    if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    }
    return `${bytes} B`;
  };

  if (activityData.agents_executed.length === 0) {
    return (
      <div className="agent-activity">
        <div className="agent-activity__empty">
          <h3>No Agent Activity Yet</h3>
          <p>Agent execution metrics will appear here after you send a message.</p>
          <p>You'll see:</p>
          <ul>
            <li>Agents executed</li>
            <li>Token usage per agent</li>
            <li>Execution time</li>
            <li>Context size</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="agent-activity">
      <div className="agent-activity__header">Agent Activity</div>
      <div className="agent-activity__content">
        <div className="agent-activity__section">
          <div className="agent-activity__section-title">Agents Executed</div>
          <div className="agent-activity__agents">
            {activityData.agents_executed.map((agent, index) => (
              <span key={index} className="agent-activity__agent-badge">
                {agent}
              </span>
            ))}
          </div>
        </div>

        {Object.keys(activityData.token_usage).length > 0 && (
          <div className="agent-activity__section">
            <div className="agent-activity__section-title">Token Usage</div>
            <div className="agent-activity__metrics">
              {Object.entries(activityData.token_usage).map(([agent, tokens]) => (
                <div key={agent} className="agent-activity__metric">
                  <span className="agent-activity__metric-label">{agent}:</span>
                  <span className="agent-activity__metric-value">
                    {formatTokens(tokens)} tokens
                  </span>
                </div>
              ))}
              <div className="agent-activity__metric agent-activity__metric--total">
                <span className="agent-activity__metric-label">Total:</span>
                <span className="agent-activity__metric-value">
                  {formatTokens(
                    Object.values(activityData.token_usage).reduce((sum, tokens) => sum + tokens, 0)
                  )} tokens
                </span>
              </div>
            </div>
          </div>
        )}

        {Object.keys(activityData.execution_time).length > 0 && (
          <div className="agent-activity__section">
            <div className="agent-activity__section-title">Execution Time</div>
            <div className="agent-activity__metrics">
              {Object.entries(activityData.execution_time).map(([agent, time]) => (
                <div key={agent} className="agent-activity__metric">
                  <span className="agent-activity__metric-label">{agent}:</span>
                  <span className="agent-activity__metric-value">
                    {formatTime(time)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activityData.context_size !== undefined && (
          <div className="agent-activity__section">
            <div className="agent-activity__section-title">Estimated Context Size</div>
            <div className="agent-activity__context-size">
              {formatBytes(activityData.context_size)}
            </div>
          </div>
        )}

        {/* Execution Timeline */}
        {activityData.execution_timeline && activityData.execution_timeline.length > 0 && (
          <div className="agent-activity__section">
            <div className="agent-activity__section-title">Execution Timeline</div>
            <div className="agent-activity__timeline">
              {activityData.execution_timeline.map((entry, index) => (
                <div
                  key={`${entry.agent}-${index}`}
                  className={`agent-activity__timeline-item agent-activity__timeline-item--${entry.status}`}
                >
                  <div className="agent-activity__timeline-marker">
                    {entry.status === 'completed' && '✓'}
                    {entry.status === 'failed' && '✗'}
                    {entry.status === 'running' && '⟳'}
                  </div>
                  <div className="agent-activity__timeline-content">
                    <div className="agent-activity__timeline-agent">{entry.agent}</div>
                    <div className="agent-activity__timeline-time">
                      {new Date(entry.start_time).toLocaleTimeString()}
                      {entry.end_time && ` - ${new Date(entry.end_time).toLocaleTimeString()}`}
                      {entry.duration !== undefined && ` (${formatTime(entry.duration)})`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
