import React, { useRef } from 'react';
import { UploadCloud, FileText, Image as ImageIcon, ShieldCheck } from 'lucide-react';

export default function UploadZone({ onFileUpload, isProcessing }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div 
      className="dropzone-card"
      onClick={() => fileInputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        accept=".pdf,.jpg,.jpeg,.png,.webp,.bmp" 
        style={{ display: 'none' }} 
      />
      
      <div className="upload-icon-wrapper">
        <UploadCloud size={32} />
      </div>

      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '4px' }}>
          {isProcessing ? 'Processing Document Offline...' : 'Upload Bank Statement or Mobile Photo'}
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Drag & drop PDF, JPG, PNG, or Passbook scan here, or click to browse
        </p>
      </div>

      <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
        <span className="badge-offline" style={{ color: 'var(--text-secondary)', background: 'var(--bg-surface-elevated)', borderColor: 'var(--border-subtle)' }}>
          <FileText size={14} /> PDF Statements
        </span>
        <span className="badge-offline" style={{ color: 'var(--text-secondary)', background: 'var(--bg-surface-elevated)', borderColor: 'var(--border-subtle)' }}>
          <ImageIcon size={14} /> Mobile Photos / Passbooks
        </span>
        <span className="badge-offline">
          <ShieldCheck size={14} /> 100% Offline Local Machine
        </span>
      </div>
    </div>
  );
}
