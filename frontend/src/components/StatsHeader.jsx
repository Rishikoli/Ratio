import React from 'react';

export default function StatsHeader({ metadata, validation }) {
  if (!metadata || !validation) return null;

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <span className="stat-label">INSTITUTION</span>
        <span className="stat-value" style={{ color: '#3b82f6', fontSize: '16px' }}>{metadata.institution}</span>
      </div>

      <div className="stat-card">
        <span className="stat-label">TOTAL TRANSACTIONS</span>
        <span className="stat-value">{validation.total_rows}</span>
      </div>

      <div className="stat-card">
        <span className="stat-label">VALIDATED ROWS</span>
        <span className="stat-value" style={{ color: 'var(--valid-color)' }}>{validation.valid_rows}</span>
      </div>

      <div className="stat-card">
        <span className="stat-label">REVIEW NEEDED</span>
        <span className="stat-value" style={{ color: 'var(--review-color)' }}>{validation.review_rows}</span>
      </div>

      <div className="stat-card">
        <span className="stat-label">MISSING PAGE GAPS</span>
        <span className="stat-value" style={{ color: 'var(--gap-color)' }}>{validation.gaps.length}</span>
      </div>
    </div>
  );
}
