import React from 'react';
import { ShieldCheck, Cpu, Zap, FileSpreadsheet, Heart, CheckCircle2, AlertTriangle } from 'lucide-react';
import UploadZone from './UploadZone';

export default function HeroLanding({ onFileUpload, isProcessing }) {
  return (
    <div className="hero-section">
      <div className="hero-content">
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '16px' }}>
          <span className="love-badge">
            <Heart size={14} fill="#e11d48" /> Ratio (made with love for my love)
          </span>
          <span className="badge-offline">
            <ShieldCheck size={14} /> 100% Offline Desktop Engine
          </span>
        </div>

        <h2>
          Turn Any Bank Statement Into <span>Validated Excel</span> Data
        </h2>

        <p className="hero-subtitle">
          Ratio extracts, mathematically verifies, and detects missing page gaps across 50+ bank formats, passbook photos, and mutual fund statements—completely offline on your PC.
        </p>

        <UploadZone onFileUpload={onFileUpload} isProcessing={isProcessing} />
      </div>

      {/* Unique Animated Card */}
      <div className="hero-graphic-container">
        <div className="animated-hero-card">
          <div className="scan-line"></div>
          
          <div className="hero-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }}></div>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }}></div>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }}></div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', marginLeft: '6px' }}>
                LIVE EXTRACTION & GAP DETECTOR
              </span>
            </div>
            <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--accent-primary)', background: '#eef2ff', padding: '2px 8px', borderRadius: '10px' }}>
              CPU Optimized
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px' }}>
            <div className="mock-row valid-mock">
              <span>01-04-2026 OPENING BALANCE</span>
              <span style={{ fontWeight: '700' }}>₹1,50,000.00</span>
            </div>

            <div className="mock-row valid-mock">
              <span>02-04-2026 UPI VENDOR PAYMENT</span>
              <span style={{ fontWeight: '700', color: '#dc2626' }}>-₹15,000.00</span>
            </div>

            <div className="mock-row valid-mock">
              <span>03-04-2026 NEFT CLIENT DEPOSIT</span>
              <span style={{ fontWeight: '700', color: '#059669' }}>+₹50,000.00</span>
            </div>

            <div className="mock-row gap-mock">
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={14} color="#dc2626" />
                <span style={{ fontWeight: '700' }}>MISSING PAGE GAP DETECTED</span>
              </div>
              <span style={{ fontWeight: '700', fontSize: '11px' }}>Mismatch: ₹38,000</span>
            </div>

            <div className="mock-row valid-mock">
              <span>18-04-2026 SOFTWARE SUBSCRIPTION</span>
              <span style={{ fontWeight: '700' }}>₹90,000.00</span>
            </div>
          </div>

          <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle2 size={14} color="#059669" /> Auto Math Validation
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FileSpreadsheet size={14} color="#4f46e5" /> Tally Ready XML
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
