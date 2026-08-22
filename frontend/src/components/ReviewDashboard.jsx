import React from 'react';
import { Download, FileSpreadsheet, Code, CheckCircle, AlertCircle, AlertTriangle, Plus, Trash2, Edit3 } from 'lucide-react';

export default function ReviewDashboard({ result, onExportExcel, onExportTally, onRevalidate }) {
  if (!result) return null;

  const { transactions, validation } = result;

  const handleCellChange = (id, field, value) => {
    const updated = transactions.map((trx) => {
      if (trx.id !== id) return trx;
      let newTrx = { ...trx, [field]: value };
      if (['debit', 'credit', 'balance'].includes(field)) {
        const num = parseFloat(value);
        newTrx[field] = (isNaN(num) || value === '') ? null : num;
      }
      return newTrx;
    });
    if (onRevalidate) {
      onRevalidate(updated);
    }
  };

  const handleAddRow = () => {
    const newRow = {
      id: 'row_' + Math.random().toString(36).substr(2, 9),
      date: new Date().toISOString().split('T')[0],
      description: 'Manual Transaction Entry',
      reference: '',
      debit: null,
      credit: null,
      balance: transactions.length > 0 ? (transactions[transactions.length - 1].balance || 0.0) : 0.0,
      status: 'VALID',
      validation_message: 'User Added Row',
      page_number: 1
    };
    if (onRevalidate) {
      onRevalidate([...transactions, newRow]);
    }
  };

  const handleDeleteRow = (id) => {
    const updated = transactions.filter((trx) => trx.id !== id);
    if (onRevalidate) {
      onRevalidate(updated);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VALID':
        return <span className="status-tag valid"><CheckCircle size={12} /> Validated</span>;
      case 'REVIEW_NEEDED':
        return <span className="status-tag review"><AlertCircle size={12} /> Review Needed</span>;
      case 'GAP_DETECTED':
      case 'ERROR':
        return <span className="status-tag gap"><AlertTriangle size={12} /> Gap Detected</span>;
      default:
        return <span className="status-tag valid">{status}</span>;
    }
  };

  const getRowClass = (status) => {
    switch (status) {
      case 'VALID': return 'row-valid';
      case 'REVIEW_NEEDED': return 'row-review';
      case 'GAP_DETECTED':
      case 'ERROR': return 'row-gap';
      default: return '';
    }
  };

  return (
    <div className="table-container">
      <div className="table-header-toolbar">
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Transaction Audit & Interactive Review <Edit3 size={16} color="var(--accent-primary)" />
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Click any cell to edit OCR misreads. Balances & gap alerts re-calculate live before exporting.
          </p>
        </div>

        <div className="toolbar-actions">
          <button onClick={handleAddRow} className="btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <Plus size={15} /> Add Row
          </button>
          <button onClick={onExportExcel} className="btn-primary">
            <FileSpreadsheet size={16} /> Export Smart Excel (.xlsx)
          </button>
          <button onClick={onExportTally} className="btn-secondary">
            <Code size={16} /> Export Tally XML
          </button>
        </div>
      </div>

      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th style={{ width: '125px' }}>Date</th>
            <th>Description</th>
            <th style={{ width: '110px' }}>Ref / Chq</th>
            <th style={{ textAlign: 'right', width: '120px' }}>Debit (₹)</th>
            <th style={{ textAlign: 'right', width: '120px' }}>Credit (₹)</th>
            <th style={{ textAlign: 'right', width: '130px' }}>Balance (₹)</th>
            <th style={{ width: '180px' }}>Validation Notes</th>
            <th style={{ width: '50px', textAlign: 'center' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((trx) => (
            <tr key={trx.id} className={getRowClass(trx.status)}>
              <td>
                <input 
                  type="text" 
                  value={trx.date || ''} 
                  onChange={(e) => handleCellChange(trx.id, 'date', e.target.value)}
                  className="cell-input"
                  style={{ fontFamily: 'var(--font-mono)' }}
                />
              </td>
              <td>
                <input 
                  type="text" 
                  value={trx.description || ''} 
                  onChange={(e) => handleCellChange(trx.id, 'description', e.target.value)}
                  className="cell-input"
                  style={{ fontWeight: '500' }}
                />
              </td>
              <td>
                <input 
                  type="text" 
                  value={trx.reference || ''} 
                  onChange={(e) => handleCellChange(trx.id, 'reference', e.target.value)}
                  className="cell-input"
                  style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}
                />
              </td>
              <td>
                <input 
                  type="number" 
                  step="0.01" 
                  placeholder="0.00"
                  value={trx.debit !== null && trx.debit !== undefined ? trx.debit : ''} 
                  onChange={(e) => handleCellChange(trx.id, 'debit', e.target.value)}
                  className="cell-input num-col"
                  style={{ color: trx.debit ? '#f87171' : 'var(--text-muted)' }}
                />
              </td>
              <td>
                <input 
                  type="number" 
                  step="0.01" 
                  placeholder="0.00"
                  value={trx.credit !== null && trx.credit !== undefined ? trx.credit : ''} 
                  onChange={(e) => handleCellChange(trx.id, 'credit', e.target.value)}
                  className="cell-input num-col"
                  style={{ color: trx.credit ? '#34d399' : 'var(--text-muted)' }}
                />
              </td>
              <td>
                <input 
                  type="number" 
                  step="0.01" 
                  value={trx.balance !== null && trx.balance !== undefined ? trx.balance : ''} 
                  onChange={(e) => handleCellChange(trx.id, 'balance', e.target.value)}
                  className="cell-input num-col"
                  style={{ fontWeight: '700' }}
                />
              </td>
              <td>
                {getStatusBadge(trx.status)}
                {trx.validation_message && trx.status !== 'VALID' && (
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {trx.validation_message}
                  </div>
                )}
              </td>
              <td style={{ textAlign: 'center' }}>
                <button 
                  onClick={() => handleDeleteRow(trx.id)}
                  title="Delete Row"
                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                >
                  <Trash2 size={14} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
