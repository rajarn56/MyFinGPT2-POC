/**
 * Agent Activity component - displays agent execution metrics and token usage
 * This is the Activity tab content in ResultsPanel
 */

import React, { useMemo } from 'react';
import { ExecuteResponse } from '../../types';
import './AgentActivity.css';

interface AgentActivityProps {
  analysis: ExecuteResponse;
}

interface AgentActivityData {
  agents_executed: string[];
  token_usage: Record<string, number>;
  execution_time: Record<string, number>;
  context_size?: number;
}

export const AgentActivity: React.FC<AgentActivityProps> = ({ analysis }) => {
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

    return {
      agents_executed: agents.length > 0 ? agents : [],
      token_usage: tokenUsagePerAgent,
      execution_time: {}, // Not available in current API response
      context_size: estimatedContextSize,
    };
  }, [analysis]);

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
      </div>
    </div>
  );
};
