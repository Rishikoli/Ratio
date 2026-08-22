import React, { useState } from 'react';
import { Cpu, Shield, Heart, FileSpreadsheet, ArrowLeft } from 'lucide-react';
import HeroLanding from './components/HeroLanding';
import StatsHeader from './components/StatsHeader';
import GapAlertBanner from './components/GapAlertBanner';
import ReviewDashboard from './components/ReviewDashboard';
import CapitalGainsCard from './components/CapitalGainsCard';

export default function App() {
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (file) => {
    setIsProcessing(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Processing failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  const handleRevalidate = async (updatedTransactions) => {
    if (!result) return;
    try {
      const response = await fetch('http://localhost:8000/api/revalidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metadata: result.metadata,
          transactions: updatedTransactions,
          capital_gains: result.capital_gains,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setResult(data);
      }
    } catch (err) {
      console.error("Revalidation error:", err);
    }
  };

  const getExportFilename = (suffix, ext) => {
    if (!result) return `Ratio_Export.${ext}`;
    const rawName = result.metadata.source_file ? result.metadata.source_file.replace(/\.[^/.]+$/, "") : result.metadata.institution;
    const cleanName = rawName.replace(/[^\w\-]/g, "_").replace(/_+/g, "_").replace(/^_+|_+$/g, "");
    return `${cleanName}_${suffix}.${ext}`;
  };

  const handleExportExcel = async () => {
    if (!result) return;
    try {
      const response = await fetch('http://localhost:8000/api/export/excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = getExportFilename('Ratio_Audit', 'xlsx');
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('Failed to export Excel file');
    }
  };

  const handleExportTally = async () => {
    if (!result) return;
    try {
      const response = await fetch('http://localhost:8000/api/export/tally', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = getExportFilename('Tally_Vouchers', 'xml');
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('Failed to export Tally XML');
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-title" onClick={handleReset} style={{ cursor: 'pointer' }}>
          <div className="brand-logo">R</div>
          <div className="brand-text">
            <h1>Ratio</h1>
            <p>Financial Document Intelligence & Gap Detector</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
          <div className="love-badge">
            <Heart size={14} fill="#e11d48" /> Ratio (made with love for my love)
          </div>

          <div className="badge-offline">
            <span className="pulse-dot"></span> Offline Engine Active
          </div>

          {result && (
            <button onClick={handleReset} className="btn-secondary" style={{ padding: '6px 14px', fontSize: '12px' }}>
              <ArrowLeft size={14} /> Upload Another
            </button>
          )}
        </div>
      </header>

      {/* Main Hero Landing View or Audit Dashboard */}
      {!result ? (
        <HeroLanding onFileUpload={handleFileUpload} isProcessing={isProcessing} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <StatsHeader metadata={result.metadata} validation={result.validation} />
          {result.capital_gains && <CapitalGainsCard cgData={result.capital_gains} />}
          <GapAlertBanner gaps={result.validation.gaps} />
          <ReviewDashboard 
            result={result} 
            onExportExcel={handleExportExcel} 
            onExportTally={handleExportTally} 
            onRevalidate={handleRevalidate}
          />
        </div>
      )}

      {error && (
        <div className="gap-alert-card">
          <div>
            <div className="gap-alert-title">Processing Error</div>
            <div className="gap-alert-body">{error}</div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <div>© 2026 Ratio Desktop Engine — Offline Financial Intelligence</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#e11d48', fontWeight: '600' }}>
          Ratio (made with love for my love) <Heart size={14} fill="#e11d48" />
        </div>
      </footer>
    </div>
  );
}
