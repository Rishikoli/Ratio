import React from 'react';
import { TrendingUp, PieChart, Tag, DollarSign } from 'lucide-react';

export default function CapitalGainsCard({ cgData }) {
  if (!cgData || !cgData.items || cgData.items.length === 0) return null;

  return (
    <div className="table-container" style={{ marginBottom: '24px' }}>
      <div className="table-header-toolbar" style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)', color: 'white' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} /> Capital Gains Tax Computation (ITR Schedule CG Ready)
          </h3>
          <p style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.8)' }}>
            Parsed STCG & LTCG entries for Mutual Funds and Equity investments
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', padding: '20px' }}>
        <div className="stat-card" style={{ background: '#f8fafc' }}>
          <span className="stat-label">TOTAL PURCHASE COST</span>
          <span className="stat-value" style={{ color: 'var(--text-primary)' }}>
            ₹{cgData.total_purchase_cost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="stat-card" style={{ background: '#f8fafc' }}>
          <span className="stat-label">TOTAL SALE PROCEEDS</span>
          <span className="stat-value" style={{ color: 'var(--text-primary)' }}>
            ₹{cgData.total_sale_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="stat-card" style={{ background: '#ecfdf5', borderColor: '#a7f3d0' }}>
          <span className="stat-label" style={{ color: '#047857' }}>NET STCG (15% / 20%)</span>
          <span className="stat-value" style={{ color: '#059669' }}>
            ₹{cgData.total_stcg.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="stat-card" style={{ background: '#f3e8ff', borderColor: '#ddd6fe' }}>
          <span className="stat-label" style={{ color: '#6d28d9' }}>NET LTCG (12.5% / 10%)</span>
          <span className="stat-value" style={{ color: '#7c3aed' }}>
            ₹{cgData.total_ltcg.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Capital Gains Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Scheme Name / Investment</th>
            <th style={{ width: '120px', textAlign: 'center' }}>Folio No</th>
            <th style={{ width: '120px', textAlign: 'center' }}>Purchase Date</th>
            <th style={{ width: '140px', textAlign: 'right' }}>Purchase Cost (₹)</th>
            <th style={{ width: '120px', textAlign: 'center' }}>Sale Date</th>
            <th style={{ width: '140px', textAlign: 'right' }}>Sale Proceeds (₹)</th>
            <th style={{ width: '130px', textAlign: 'right' }}>Net STCG (₹)</th>
            <th style={{ width: '130px', textAlign: 'right' }}>Net LTCG (₹)</th>
          </tr>
        </thead>
        <tbody>
          {cgData.items.map((item) => (
            <tr key={item.id}>
              <td style={{ fontWeight: '600' }}>{item.scheme_name}</td>
              <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{item.folio_no || '-'}</td>
              <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)' }}>{item.purchase_date || '-'}</td>
              <td className="num-col">₹{item.purchase_cost.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
              <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)' }}>{item.sale_date || '-'}</td>
              <td className="num-col">₹{item.sale_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
              <td className="num-col" style={{ color: item.stcg > 0 ? '#059669' : 'var(--text-muted)' }}>
                {item.stcg ? `₹${item.stcg.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
              </td>
              <td className="num-col" style={{ color: item.ltcg > 0 ? '#7c3aed' : 'var(--text-muted)' }}>
                {item.ltcg ? `₹${item.ltcg.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
