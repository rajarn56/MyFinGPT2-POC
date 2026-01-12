/**
 * Two-column layout component with resizable panels
 */

import React, { useState, useRef, useEffect } from 'react';
import './TwoColumnLayout.css';

interface TwoColumnLayoutProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultLeftWidth?: number; // Percentage (0-100)
  minLeftWidth?: number; // Percentage
  minRightWidth?: number; // Percentage
}

export const TwoColumnLayout: React.FC<TwoColumnLayoutProps> = ({
  left,
  right,
  defaultLeftWidth = 50,
  minLeftWidth = 20,
  minRightWidth = 20,
}) => {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const containerWidth = containerRef.current.offsetWidth;
      const newLeftWidth = (e.clientX / containerWidth) * 100;

      // Enforce min widths
      if (newLeftWidth >= minLeftWidth && newLeftWidth <= 100 - minRightWidth) {
        setLeftWidth(newLeftWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, minLeftWidth, minRightWidth]);

  const toggleLeft = () => {
    setLeftCollapsed(!leftCollapsed);
    if (!leftCollapsed) {
      // Store current width before collapsing
      setLeftWidth(defaultLeftWidth);
    }
  };

  const toggleRight = () => {
    setRightCollapsed(!rightCollapsed);
  };

  return (
    <div ref={containerRef} className="two-column-layout">
      {/* Left Panel */}
      <div
        className={`two-column-layout__left ${
          leftCollapsed ? 'two-column-layout__left--collapsed' : ''
        }`}
        style={{
          width: leftCollapsed ? '0%' : `${leftWidth}%`,
          display: leftCollapsed ? 'none' : 'flex',
        }}
      >
        {left}
        <button
          className="two-column-layout__toggle two-column-layout__toggle--left"
          onClick={toggleLeft}
          aria-label={leftCollapsed ? 'Expand left panel' : 'Collapse left panel'}
        >
          {leftCollapsed ? '◀' : '▶'}
        </button>
      </div>

      {/* Resizer */}
      {!leftCollapsed && !rightCollapsed && (
        <div
          className={`two-column-layout__resizer ${
            isResizing ? 'two-column-layout__resizer--active' : ''
          }`}
          onMouseDown={handleMouseDown}
          aria-label="Resize panels"
        >
          <div className="two-column-layout__resizer-handle" />
        </div>
      )}

      {/* Right Panel */}
      <div
        className={`two-column-layout__right ${
          rightCollapsed ? 'two-column-layout__right--collapsed' : ''
        }`}
        style={{
          width: rightCollapsed ? '0%' : `${100 - leftWidth}%`,
          display: rightCollapsed ? 'none' : 'flex',
        }}
      >
        {right}
        <button
          className="two-column-layout__toggle two-column-layout__toggle--right"
          onClick={toggleRight}
          aria-label={rightCollapsed ? 'Expand right panel' : 'Collapse right panel'}
        >
          {rightCollapsed ? '▶' : '◀'}
        </button>
      </div>

      {/* Collapsed Panel Buttons */}
      {leftCollapsed && (
        <button
          className="two-column-layout__expand-button two-column-layout__expand-button--left"
          onClick={toggleLeft}
          aria-label="Expand left panel"
        >
          ◀
        </button>
      )}
      {rightCollapsed && (
        <button
          className="two-column-layout__expand-button two-column-layout__expand-button--right"
          onClick={toggleRight}
          aria-label="Expand right panel"
        >
          ▶
        </button>
      )}
    </div>
  );
};
