import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function GapAlertBanner({ gaps }) {
  if (!gaps || gaps.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {gaps.map((gap, idx) => (
        <div key={idx} className="gap-alert-card">
          <AlertTriangle size={24} style={{ color: '#ef4444', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div className="gap-alert-title">MISSING PAGE / BALANCE GAP DETECTED</div>
            <div className="gap-alert-body">{gap.message}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
