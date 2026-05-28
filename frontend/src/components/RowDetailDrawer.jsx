import { useState } from 'react';
import api from '../api/client';

export default function RowDetailDrawer({ record, onClose, onReviewDone }) {
  const [action, setAction] = useState('');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');

  const handleReview = async () => {
    setSubmitting(true);
    setError('');
    try {
      await api.patch(`/records/${record.id}/review/`, { action, comment });
      onReviewDone();
    } catch (err) {
      setError(err.response?.data?.error || 'Review failed');
    }
    setSubmitting(false);
    setShowConfirm(false);
  };

  const initiateReview = (a) => {
    setAction(a);
    setShowConfirm(true);
  };

  const raw = record.source_row_raw || {};

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-header">
          <h3>Record #{record.id}</h3>
          <button className="drawer-close" onClick={onClose}>✕</button>
        </div>

        <div className="drawer-body">
          {/* Status & Scope */}
          <div className="detail-section">
            <h4>Overview</h4>
            <div className="detail-row">
              <span className="detail-label">Status</span>
              <span className={`badge badge-${record.status?.toLowerCase()}`}>{record.status}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Scope</span>
              <span className={`badge badge-scope${record.scope}`}>Scope {record.scope}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Category</span>
              <span className="detail-value">{record.category?.replace(/_/g, ' ')}</span>
            </div>
            {record.subcategory && (
              <div className="detail-row">
                <span className="detail-label">Subcategory</span>
                <span className="detail-value">{record.subcategory}</span>
              </div>
            )}
            <div className="detail-row">
              <span className="detail-label">Date</span>
              <span className="detail-value">{record.activity_date}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Period</span>
              <span className="detail-value">{record.period_start} → {record.period_end}</span>
            </div>
          </div>

          {/* Raw vs Normalised */}
          <div className="detail-section">
            <h4>Raw vs Normalised</h4>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
              padding: 16, background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)'
            }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Original</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  {Number(record.quantity_raw).toLocaleString()}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{record.unit_raw}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Normalised</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                  {Number(record.quantity_normalised).toLocaleString()}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{record.unit_normalised}</div>
              </div>
            </div>
          </div>

          {/* Emission Factor */}
          <div className="detail-section">
            <h4>Emission Calculation</h4>
            <div className="detail-row">
              <span className="detail-label">Factor</span>
              <span className="detail-value">{record.emission_factor || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Source</span>
              <span className="detail-value">{record.emission_factor_source || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">CO₂e (kg)</span>
              <span className="detail-value" style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
                {record.co2e_kg ? Number(record.co2e_kg).toFixed(2) : '—'}
              </span>
            </div>
          </div>

          {/* Anomaly */}
          {record.is_anomaly && (
            <div className="detail-section">
              <div style={{
                padding: '12px 16px', background: 'var(--status-flagged-bg)',
                border: '1px solid rgba(245,158,11,0.3)', borderRadius: 'var(--radius-md)'
              }}>
                <strong style={{ color: 'var(--status-flagged)' }}>⚠ Anomaly Detected</strong>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 4 }}>{record.anomaly_reason}</p>
              </div>
            </div>
          )}

          {/* Source metadata */}
          {Object.keys(record.metadata || {}).length > 0 && (
            <div className="detail-section">
              <h4>Metadata</h4>
              {Object.entries(record.metadata).map(([k, v]) => (
                <div key={k} className="detail-row">
                  <span className="detail-label">{k.replace(/_/g, ' ')}</span>
                  <span className="detail-value">{String(v)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Raw source data */}
          {Object.keys(raw).length > 0 && (
            <div className="detail-section">
              <h4>Original Source Row</h4>
              <div style={{
                padding: 12, background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-mono)', fontSize: '0.75rem', overflow: 'auto', maxHeight: 200,
                color: 'var(--text-secondary)', lineHeight: 1.8,
              }}>
                {Object.entries(raw).map(([k, v]) => (
                  <div key={k}><span style={{ color: 'var(--accent-secondary)' }}>{k}</span>: {v}</div>
                ))}
              </div>
            </div>
          )}

          {/* Review comment if already reviewed */}
          {record.review_comment && (
            <div className="detail-section">
              <h4>Review Comment</h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{record.review_comment}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                by {record.reviewed_by_name} · {record.reviewed_at}
              </p>
            </div>
          )}

          {/* Review Actions */}
          {!record.is_locked && (
            <div className="detail-section">
              <h4>Review Actions</h4>
              {error && <div className="login-error" style={{ marginBottom: 12 }}>{error}</div>}
              <div className="form-group">
                <label className="form-label">Comment (optional)</label>
                <textarea
                  className="form-input"
                  rows={3}
                  value={comment}
                  onChange={e => setComment(e.target.value)}
                  placeholder="Add a review note..."
                  style={{ resize: 'vertical' }}
                />
              </div>
              <div className="btn-group">
                <button className="btn btn-success" onClick={() => initiateReview('APPROVED')}>✓ Approve</button>
                <button className="btn btn-danger" onClick={() => initiateReview('REJECTED')}>✗ Reject</button>
                <button className="btn btn-secondary" onClick={() => initiateReview('FLAGGED')}
                  style={{ color: 'var(--status-flagged)', borderColor: 'rgba(245,158,11,.3)' }}>
                  ⚑ Flag
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="modal-overlay" onClick={() => setShowConfirm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Confirm {action}</h3>
            <p>
              Are you sure you want to mark this record as <strong>{action}</strong>?
              {action === 'APPROVED' && ' This action confirms the data for audit submission.'}
              {action === 'REJECTED' && ' This record will be excluded from the audit submission.'}
            </p>
            {comment && <p style={{ fontStyle: 'italic', fontSize: '0.85rem' }}>Comment: "{comment}"</p>}
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowConfirm(false)} disabled={submitting}>Cancel</button>
              <button
                className={`btn ${action === 'APPROVED' ? 'btn-success' : action === 'REJECTED' ? 'btn-danger' : 'btn-secondary'}`}
                onClick={handleReview} disabled={submitting}
              >
                {submitting ? 'Processing...' : `Confirm ${action}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
