/**
 * Analysis panel component
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { useAppContext } from '../../context/AppContext';
import { Loading } from '../ui/Loading';

export const AnalysisPanel: React.FC = () => {
  const { currentAnalysis, isLoading } = useAppContext();

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loading message="Generating analysis..." />
      </div>
    );
  }

  if (!currentAnalysis?.result.report) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <p>Analysis results will appear here</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b p-4 bg-gray-50">
        <h2 className="text-xl font-semibold">Analysis Report</h2>
        {currentAnalysis.transaction_id && (
          <p className="text-sm text-gray-500 mt-1">
            Transaction: {currentAnalysis.transaction_id}
          </p>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{currentAnalysis.result.report}</ReactMarkdown>
        </div>
        {currentAnalysis.result.citations.length > 0 && (
          <div className="mt-8 border-t pt-4">
            <h3 className="text-lg font-semibold mb-2">Citations</h3>
            <ul className="list-disc list-inside space-y-1">
              {currentAnalysis.result.citations.map((citation, index) => (
                <li key={index} className="text-sm text-gray-600">
                  {citation.source}
                  {citation.symbol && ` - ${citation.symbol}`}
                  {citation.type && ` (${citation.type})`}
                </li>
              ))}
            </ul>
          </div>
        )}
        {currentAnalysis.result.errors.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
            <h3 className="text-lg font-semibold text-red-800 mb-2">Errors</h3>
            <ul className="list-disc list-inside space-y-1">
              {currentAnalysis.result.errors.map((error, index) => (
                <li key={index} className="text-sm text-red-600">{error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
