/**
 * Analysis Report component - displays the full analysis report
 * This is the Report tab content in ResultsPanel
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ExecuteResponse } from '../../types';
import './AnalysisReport.css';

interface AnalysisReportProps {
  analysis: ExecuteResponse;
}

export const AnalysisReport: React.FC<AnalysisReportProps> = ({ analysis }) => {
  if (!analysis.result.report) {
    return (
      <div className="analysis-report">
        <div className="analysis-report__empty">
          <p>No report available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-report">
      <div className="analysis-report__header">
        <h2 className="analysis-report__title">Analysis Report</h2>
        {analysis.transaction_id && (
          <p className="analysis-report__transaction">
            Transaction: {analysis.transaction_id}
          </p>
        )}
      </div>
      <div className="analysis-report__content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {analysis.result.report}
        </ReactMarkdown>
        {analysis.result.errors.length > 0 && (
          <div className="analysis-report__errors">
            <h3 className="analysis-report__errors-title">Errors</h3>
            <ul className="analysis-report__errors-list">
              {analysis.result.errors.map((error, index) => (
                <li key={index} className="analysis-report__error-item">{error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
