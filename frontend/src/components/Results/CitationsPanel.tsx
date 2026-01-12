/**
 * Citations Panel component - displays citations and references
 * This is the Citations tab content in ResultsPanel
 */

import React, { useState, useMemo } from 'react';
import { ExecuteResponse } from '../../types';
import './CitationsPanel.css';

interface CitationsPanelProps {
  analysis: ExecuteResponse;
}

export const CitationsPanel: React.FC<CitationsPanelProps> = ({ analysis }) => {
  const citations = analysis.result.citations || [];
  const [filterSource, setFilterSource] = useState<string>('');
  const [filterSymbol, setFilterSymbol] = useState<string>('');
  const [filterAgent, setFilterAgent] = useState<string>('');

  // Get unique values for filters
  const uniqueSources = useMemo(() => {
    const sources = new Set<string>();
    citations.forEach(citation => {
      if (citation.source) sources.add(citation.source);
    });
    return Array.from(sources).sort();
  }, [citations]);

  const uniqueSymbols = useMemo(() => {
    const symbols = new Set<string>();
    citations.forEach(citation => {
      if (citation.symbol) symbols.add(citation.symbol);
    });
    return Array.from(symbols).sort();
  }, [citations]);

  const uniqueAgents = useMemo(() => {
    const agents = new Set<string>();
    citations.forEach(citation => {
      // Extract agent from citation if available (may be in metadata or type field)
      if ((citation as any).agent) {
        agents.add((citation as any).agent);
      }
    });
    return Array.from(agents).sort();
  }, [citations]);

  // Filter citations
  const filteredCitations = useMemo(() => {
    return citations.filter(citation => {
      if (filterSource && citation.source !== filterSource) return false;
      if (filterSymbol && citation.symbol !== filterSymbol) return false;
      if (filterAgent && (citation as any).agent !== filterAgent) return false;
      return true;
    });
  }, [citations, filterSource, filterSymbol, filterAgent]);

  if (citations.length === 0) {
    return (
      <div className="citations-panel">
        <div className="citations-panel__empty">
          <h3>No Citations Available</h3>
          <p>Citations will appear here when available from the analysis.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="citations-panel">
      <div className="citations-panel__header">
        <h2 className="citations-panel__title">Citations</h2>
        <p className="citations-panel__count">
          {filteredCitations.length} of {citations.length} citation{filteredCitations.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Filters */}
      {(uniqueSources.length > 0 || uniqueSymbols.length > 0 || uniqueAgents.length > 0) && (
        <div className="citations-panel__filters">
          {uniqueSources.length > 0 && (
            <div className="citations-panel__filter">
              <label htmlFor="filter-source" className="citations-panel__filter-label">
                Filter by Source:
              </label>
              <select
                id="filter-source"
                value={filterSource}
                onChange={(e) => setFilterSource(e.target.value)}
                className="citations-panel__filter-select"
              >
                <option value="">All Sources</option>
                {uniqueSources.map(source => (
                  <option key={source} value={source}>{source}</option>
                ))}
              </select>
            </div>
          )}

          {uniqueSymbols.length > 0 && (
            <div className="citations-panel__filter">
              <label htmlFor="filter-symbol" className="citations-panel__filter-label">
                Filter by Symbol:
              </label>
              <select
                id="filter-symbol"
                value={filterSymbol}
                onChange={(e) => setFilterSymbol(e.target.value)}
                className="citations-panel__filter-select"
              >
                <option value="">All Symbols</option>
                {uniqueSymbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>
          )}

          {uniqueAgents.length > 0 && (
            <div className="citations-panel__filter">
              <label htmlFor="filter-agent" className="citations-panel__filter-label">
                Filter by Agent:
              </label>
              <select
                id="filter-agent"
                value={filterAgent}
                onChange={(e) => setFilterAgent(e.target.value)}
                className="citations-panel__filter-select"
              >
                <option value="">All Agents</option>
                {uniqueAgents.map(agent => (
                  <option key={agent} value={agent}>{agent}</option>
                ))}
              </select>
            </div>
          )}

          {(filterSource || filterSymbol || filterAgent) && (
            <button
              onClick={() => {
                setFilterSource('');
                setFilterSymbol('');
                setFilterAgent('');
              }}
              className="citations-panel__clear-filters"
            >
              Clear Filters
            </button>
          )}
        </div>
      )}

      {/* Citations List */}
      <div className="citations-panel__content">
        {filteredCitations.length === 0 ? (
          <div className="citations-panel__empty">
            <p>No citations match the selected filters.</p>
          </div>
        ) : (
          <ul className="citations-panel__list">
            {filteredCitations.map((citation, index) => (
              <li key={index} className="citations-panel__item">
                <div className="citations-panel__item-header">
                  <div className="citations-panel__item-source">
                    {citation.source}
                  </div>
                  {(citation as any).agent && (
                    <span className="citations-panel__item-badge">
                      {(citation as any).agent}
                    </span>
                  )}
                </div>
                <div className="citations-panel__item-details">
                  {citation.symbol && (
                    <div className="citations-panel__item-detail">
                      <span className="citations-panel__item-label">Symbol:</span>
                      <span className="citations-panel__item-value">{citation.symbol}</span>
                    </div>
                  )}
                  {citation.type && (
                    <div className="citations-panel__item-detail">
                      <span className="citations-panel__item-label">Type:</span>
                      <span className="citations-panel__item-value">{citation.type}</span>
                    </div>
                  )}
                  {(citation as any).data_point && (
                    <div className="citations-panel__item-detail">
                      <span className="citations-panel__item-label">Data Point:</span>
                      <span className="citations-panel__item-value">{(citation as any).data_point}</span>
                    </div>
                  )}
                  {(citation as any).date && (
                    <div className="citations-panel__item-detail">
                      <span className="citations-panel__item-label">Date:</span>
                      <span className="citations-panel__item-value">{(citation as any).date}</span>
                    </div>
                  )}
                </div>
                {citation.url && (
                  <a
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="citations-panel__item-link"
                  >
                    {citation.url}
                  </a>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
