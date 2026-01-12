/**
 * Visualizations component - displays charts and visual data
 * This is the Visualizations tab content in ResultsPanel
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { ExecuteResponse } from '../../types';
import './Visualizations.css';

interface VisualizationsProps {
  analysis: ExecuteResponse;
}

interface ChartData {
  title: string;
  data: any[];
  layout: any;
}

export const Visualizations: React.FC<VisualizationsProps> = ({ analysis }) => {
  const charts = useMemo(() => {
    const chartData: ChartData[] = [];

    // Process comparison_data
    const comparisonData = analysis.result.comparison_data || {};
    if (comparisonData.comparison_type === 'side_by_side' && comparisonData.metrics) {
      const metrics = comparisonData.metrics;
      const symbols = Object.keys(metrics);

      if (symbols.length > 0) {
        // Price comparison chart
        const prices = symbols.map(symbol => {
          const price = metrics[symbol]?.current_price;
          return price && typeof price === 'number' ? price : null;
        }).filter(p => p !== null);

        if (prices.length > 0) {
          chartData.push({
            title: 'Price Comparison',
            data: [{
              x: symbols,
              y: prices,
              type: 'bar',
              marker: {
                color: 'rgb(0, 123, 255)',
              },
            }],
            layout: {
              xaxis: { title: 'Symbol' },
              yaxis: { title: 'Price ($)' },
            },
          });
        }

        // Market Cap comparison chart
        const marketCaps = symbols.map(symbol => {
          const cap = metrics[symbol]?.market_cap;
          return cap && typeof cap === 'number' ? cap : null;
        }).filter(c => c !== null);

        if (marketCaps.length > 0) {
          chartData.push({
            title: 'Market Cap Comparison',
            data: [{
              x: symbols,
              y: marketCaps,
              type: 'bar',
              marker: {
                color: 'rgb(40, 167, 69)',
              },
            }],
            layout: {
              xaxis: { title: 'Symbol' },
              yaxis: { title: 'Market Cap ($)' },
            },
          });
        }

        // P/E Ratio comparison chart
        const peRatios = symbols.map(symbol => {
          const pe = metrics[symbol]?.pe_ratio;
          return pe && typeof pe === 'number' ? pe : null;
        }).filter(p => p !== null);

        if (peRatios.length > 0) {
          chartData.push({
            title: 'P/E Ratio Comparison',
            data: [{
              x: symbols,
              y: peRatios,
              type: 'bar',
              marker: {
                color: 'rgb(255, 193, 7)',
              },
            }],
            layout: {
              xaxis: { title: 'Symbol' },
              yaxis: { title: 'P/E Ratio' },
            },
          });
        }

        // Sentiment comparison chart
        const sentiments = symbols.map(symbol => {
          const sentiment = metrics[symbol]?.sentiment;
          const sentimentMap: Record<string, number> = {
            bullish: 1,
            neutral: 0,
            bearish: -1,
          };
          return sentiment ? (sentimentMap[sentiment.toLowerCase()] ?? 0) : null;
        }).filter(s => s !== null);

        if (sentiments.length > 0) {
          chartData.push({
            title: 'Sentiment Comparison',
            data: [{
              x: symbols,
              y: sentiments,
              type: 'bar',
              marker: {
                color: sentiments.map(s => s === 1 ? 'rgb(40, 167, 69)' : s === -1 ? 'rgb(220, 53, 69)' : 'rgb(108, 117, 125)'),
              },
            }],
            layout: {
              xaxis: { title: 'Symbol' },
              yaxis: { 
                title: 'Sentiment',
                tickvals: [-1, 0, 1],
                ticktext: ['Bearish', 'Neutral', 'Bullish'],
              },
            },
          });
        }
      }
    }

    // Process trend_analysis
    const trendAnalysis = analysis.result.trend_analysis || {};
    Object.entries(trendAnalysis).forEach(([symbol, trendData]: [string, any]) => {
      if (trendData && typeof trendData === 'object') {
        // Price trend chart (if historical prices available)
        if (trendData.price_trend && trendData.data_points) {
          const dataPoints = trendData.data_points;
          if (Array.isArray(dataPoints) && dataPoints.length > 0) {
            const dates = dataPoints.map((_: any, i: number) => i);
            const prices = dataPoints;

            chartData.push({
              title: `${symbol} Price Trend`,
              data: [{
                x: dates,
                y: prices,
                type: 'scatter',
                mode: 'lines+markers',
                name: symbol,
                line: {
                  color: 'rgb(0, 123, 255)',
                },
              }],
              layout: {
                xaxis: { title: 'Time Period' },
                yaxis: { title: 'Price ($)' },
              },
            });
          }
        }

        // Trend strength indicator
        if (trendData.trend_strength !== undefined) {
          chartData.push({
            title: `${symbol} Trend Strength`,
            data: [{
              x: [symbol],
              y: [trendData.trend_strength],
              type: 'bar',
              marker: {
                color: trendData.trend_strength > 0.5 ? 'rgb(40, 167, 69)' : 
                       trendData.trend_strength < -0.5 ? 'rgb(220, 53, 69)' : 
                       'rgb(108, 117, 125)',
              },
            }],
            layout: {
              xaxis: { title: 'Symbol' },
              yaxis: { title: 'Trend Strength', range: [-1, 1] },
            },
          });
        }
      }
    });

    return chartData;
  }, [analysis]);

  if (charts.length === 0) {
    return (
      <div className="visualizations">
        <div className="visualizations__empty">
          <h3>No Visualizations Yet</h3>
          <p>Charts and graphs will appear here when you receive comparison or trend analysis data.</p>
          <p>Try asking for stock comparisons or trend analysis to see visualizations!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="visualizations">
      {charts.map((chart, index) => (
        <div key={index} className="visualizations__chart">
          <Plot
            data={chart.data}
            layout={{
              ...chart.layout,
              title: chart.title,
              margin: { l: 60, r: 20, t: 60, b: 60 },
              height: 400,
            }}
            config={{
              responsive: true,
              displayModeBar: true,
            }}
          />
        </div>
      ))}
    </div>
  );
};
