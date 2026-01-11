/**
 * Two-column layout component (50/50 split)
 */

import React from 'react';

interface TwoColumnLayoutProps {
  left: React.ReactNode;
  right: React.ReactNode;
}

export const TwoColumnLayout: React.FC<TwoColumnLayoutProps> = ({
  left,
  right,
}) => {
  return (
    <div className="flex h-screen">
      <div className="flex-1 border-r overflow-hidden">{left}</div>
      <div className="flex-1 overflow-hidden">{right}</div>
    </div>
  );
};
