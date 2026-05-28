import { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import api from '../api/client';
import RowDetailDrawer from '../components/RowDetailDrawer';

ChartJS.register(ArcElement, Tooltip, Legend);

const STATUS_BADGE = {
  PENDING: 'badge-pending', FLAGGED: 'badge-flagged',
  APPROVED: 'badge-approved', REJECTED: 'badge-rejected',
};
const SCOPE_BADGE = { 1: 'badge-scope1', 2: 'badge-scope2', 3: 'badge-scope3' };

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [scopeFilter, setScopeFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchSummary = async () => {
    try {
      const { data } = await api.get('/dashboard/summary/');
      setSummary(data);
    } catch { /* ignore */ }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params = { page };
      if (statusFilter) params.status = statusFilter;
      if (scopeFilter) params.scope = scopeFilter;
      if (sourceFilter) params.source_type = sourceFilter;
      const { data } = await api.get('/records/', { params });
      setRecords(data.results || []);
      setTotalCount(data.count || 0);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchSummary(); }, []);
  useEffect(() => { fetchRecords(); }, [statusFilter, scopeFilter, sourceFilter, page]);

  const handleReviewDone = () => {
    setSelectedRecord(null);
    fetchRecords();
    fetchSummary();
  };

  const scopeChart = summary?.scope_co2e ? {
    labels: ['Scope 1', 'Scope 2', 'Scope 3'],
    datasets: [{
      data: [summary.scope_co2e.scope_1, summary.scope_co2e.scope_2, summary.scope_co2e.scope_3],
      backgroundColor: ['#f97316', '#3b82f6', '#8b5cf6'],
      borderColor: ['#0a0f1a', '#0a0f1a', '#0a0f1a'],
      borderWidth: 3,
    }]
  } : null;

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 }, padding: 16 } },
      tooltip: {
        backgroundColor: '#1a2233', borderColor: '#334155', borderWidth: 1,
        titleColor: '#f1f5f9', bodyColor: '#94a3b8',
        callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(1)} kgCO₂e` }
      }
    },
    cutout: '65%',
  };

  const formatCO2 = (v) => {
    if (!v) return '0';
    if (v >= 1000000) return `${(v / 1000000).toFixed(1)}t`;
    if (v >= 1000) return `${(v / 1000).toFixed(1)}kg`;
    return `${v.toFixed(1)}g`;
  };

  return (
    <div>
      <div className="page-header">
        <h2>Review Dashboard</h2>
        <p>Manage, review, and approve emission data records.</p>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="stat-grid">
          <div className="stat-card">
            <span className="stat-label">Total Records</span>
            <span className="stat-value">{summary.total_records}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total CO₂e</span>
            <span className="stat-value">{formatCO2(summary.total_co2e_kg)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Pending Review</span>
            <span className="stat-value" style={{ color: 'var(--status-pending)' }}>
              {summary.by_status?.PENDING || 0}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Flagged</span>
            <span className="stat-value" style={{ color: 'var(--status-flagged)' }}>
              {summary.by_status?.FLAGGED || 0}
            </span>
          </div>
        </div>
      )}



      {/* Filter Bar */}
      <div className="filter-bar">
        <select className="form-select" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="FLAGGED">Flagged</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
        <select className="form-select" value={scopeFilter} onChange={e => { setScopeFilter(e.target.value); setPage(1); }}>
          <option value="">All Scopes</option>
          <option value="1">Scope 1</option>
          <option value="2">Scope 2</option>
          <option value="3">Scope 3</option>
        </select>
        <select className="form-select" value={sourceFilter} onChange={e => { setSourceFilter(e.target.value); setPage(1); }}>
          <option value="">All Sources</option>
          <option value="SAP">SAP</option>
          <option value="UTILITY">Utility</option>
          <option value="TRAVEL">Travel</option>
        </select>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.8rem', alignSelf: 'center' }}>
          {totalCount} records
        </span>
      </div>

      {/* Records Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading"><div className="spinner" /> Loading records...</div>
        ) : records.length === 0 ? (
          <div className="empty-state"><h3>No Records Found</h3><p>Upload data to get started.</p></div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Scope</th>
                <th>Category</th>
                <th>Raw Qty</th>
                <th>Normalised</th>
                <th>CO₂e (kg)</th>
                <th>Status</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec) => (
                <tr key={rec.id} onClick={() => setSelectedRecord(rec)}>
                  <td>{rec.activity_date}</td>
                  <td><span className={`badge ${SCOPE_BADGE[rec.scope]}`}>Scope {rec.scope}</span></td>
                  <td>{rec.category?.replace(/_/g, ' ')}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {Number(rec.quantity_raw).toLocaleString()} {rec.unit_raw}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {Number(rec.quantity_normalised).toLocaleString()} {rec.unit_normalised}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600 }}>
                    {rec.co2e_kg ? Number(rec.co2e_kg).toFixed(2) : '—'}
                  </td>
                  <td><span className={`badge ${STATUS_BADGE[rec.status]}`}>{rec.status}</span></td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{rec.source_filename || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalCount > 50 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
          <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Previous</button>
          <span style={{ padding: '6px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Page {page} of {Math.ceil(totalCount / 50)}
          </span>
          <button className="btn btn-secondary btn-sm" disabled={page * 50 >= totalCount} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}

      {/* Row Detail Drawer */}
      {selectedRecord && (
        <RowDetailDrawer
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          onReviewDone={handleReviewDone}
        />
      )}
    </div>
  );
}
