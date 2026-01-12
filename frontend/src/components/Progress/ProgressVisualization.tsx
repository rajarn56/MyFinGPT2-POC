/**
 * Progress Visualization component - displays real-time agent execution progress
 * Shows timeline, agent status, and progress events
 */

import React, { useMemo } from 'react';
import { useAppContext } from '../../context/AppContext';
import { ProgressUpdate } from '../../types';
import './ProgressVisualization.css';

export const ProgressVisualization: React.FC = () => {
  const { progress, isLoading } = useAppContext();

  const timelineData = useMemo(() => {
    if (!progress || !progress.execution_order || progress.execution_order.length === 0) {
      return null;
    }

    return progress.execution_order.map((entry, index) => {
      const startTime = new Date(entry.start_time);
      const endTime = entry.end_time ? new Date(entry.end_time) : null;
      const duration = endTime 
        ? (endTime.getTime() - startTime.getTime()) / 1000 
        : null;

      return {
        ...entry,
        index,
        startTime,
        endTime,
        duration,
        isActive: entry.status === 'running',
      };
    });
  }, [progress]);

  const currentAgent = progress?.current_agent;
  const currentTasks = progress?.current_tasks || {};
  const progressEvents = progress?.progress_events || [];

  if (!progress && !isLoading) {
    return (
      <div className="progress-visualization">
        <div className="progress-visualization__empty">
          <h3>No Active Progress</h3>
          <p>Progress updates will appear here when agents are executing.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="progress-visualization">
      <div className="progress-visualization__header">
        <h3 className="progress-visualization__title">Execution Progress</h3>
        {currentAgent && (
          <div className="progress-visualization__current-agent">
            <span className="progress-visualization__label">Current Agent:</span>
            <span className="progress-visualization__agent-name">{currentAgent}</span>
          </div>
        )}
      </div>

      {/* Execution Timeline */}
      {timelineData && timelineData.length > 0 && (
        <div className="progress-visualization__section">
          <h4 className="progress-visualization__section-title">Execution Timeline</h4>
          <div className="progress-visualization__timeline">
            {timelineData.map((entry) => (
              <div
                key={entry.agent}
                className={`progress-visualization__timeline-item ${
                  entry.isActive ? 'progress-visualization__timeline-item--active' : ''
                } progress-visualization__timeline-item--${entry.status}`}
              >
                <div className="progress-visualization__timeline-marker">
                  {entry.status === 'completed' && '✓'}
                  {entry.status === 'failed' && '✗'}
                  {entry.status === 'running' && '⟳'}
                </div>
                <div className="progress-visualization__timeline-content">
                  <div className="progress-visualization__timeline-agent">{entry.agent}</div>
                  <div className="progress-visualization__timeline-time">
                    {entry.startTime.toLocaleTimeString()}
                    {entry.endTime && ` - ${entry.endTime.toLocaleTimeString()}`}
                    {entry.duration && ` (${entry.duration.toFixed(2)}s)`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current Tasks */}
      {Object.keys(currentTasks).length > 0 && (
        <div className="progress-visualization__section">
          <h4 className="progress-visualization__section-title">Active Tasks</h4>
          <div className="progress-visualization__tasks">
            {Object.entries(currentTasks).map(([agent, tasks]) => (
              <div key={agent} className="progress-visualization__task-group">
                <div className="progress-visualization__task-agent">{agent}:</div>
                <ul className="progress-visualization__task-list">
                  {tasks.map((task, index) => (
                    <li key={index} className="progress-visualization__task-item">
                      {task}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Progress Events */}
      {progressEvents.length > 0 && (
        <div className="progress-visualization__section">
          <h4 className="progress-visualization__section-title">Progress Events</h4>
          <div className="progress-visualization__events">
            {progressEvents.slice(-10).reverse().map((event, index) => (
              <div
                key={index}
                className={`progress-visualization__event progress-visualization__event--${event.event_type}`}
              >
                <div className="progress-visualization__event-time">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
                <div className="progress-visualization__event-message">
                  {event.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
