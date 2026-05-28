import { useState, useEffect } from 'react';
import api from '../api/client';

const DOT_CLASS = {
  UPLOADED: 'uploaded', APPROVED: 'approved', REJECTED: 'rejected',
  FLAGGED: 'flagged', EDITED: 'edited', LOCKED: 'locked',
};

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const { data } = await api.get('/audit-log/');
        setLogs(data.results || []);
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchLogs();
  }, []);

  const formatDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
      + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div className="page-header">
        <h2>Audit Log</h2>
        <p>Complete, immutable record of every action taken in the platform.</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading audit trail...</div>
      ) : logs.length === 0 ? (
        <div className="card">
          <div className="empty-state"><h3>No Audit Entries</h3><p>Actions will appear here as you use the platform.</p></div>
        </div>
      ) : (
        <div className="card">
          <div className="timeline">
            {logs.map((log) => (
              <div key={log.id} className="timeline-item">
                <div className={`timeline-dot ${DOT_CLASS[log.action] || 'edited'}`} />
                <div className="timeline-content">
                  <div className="timeline-header">
                    <span className="timeline-action">
                      <span className={`badge badge-${log.action?.toLowerCase() === 'uploaded' ? 'pending' : log.action?.toLowerCase()}`}>
                        {log.action}
                      </span>
                      {' '}on {log.target_type} #{log.target_id}
                    </span>
                    <span className="timeline-time">{formatDate(log.timestamp)}</span>
                  </div>
                  <div className="timeline-detail">
                    by <strong>{log.actor_name}</strong>
                    {log.detail?.comment && <> — "{log.detail.comment}"</>}
                    {log.detail?.filename && <> — {log.detail.filename}</>}
                    {log.detail?.rows_parsed != null && <> — {log.detail.rows_parsed} rows parsed</>}
                    {log.detail?.old_status && (
                      <> — {log.detail.old_status} → {log.detail.new_status}</>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
