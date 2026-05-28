import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../api/client';

const SOURCE_TYPES = [
  { value: 'SAP', label: 'SAP — Fuel & Procurement', desc: 'Pipe-delimited IDoc flat file (.txt/.csv)' },
  { value: 'UTILITY', label: 'Utility — Electricity', desc: 'Green Button / portal CSV export' },
  { value: 'TRAVEL', label: 'Travel — Corporate', desc: 'Concur-style expense CSV export' },
];

export default function UploadPage() {
  const [sourceType, setSourceType] = useState('SAP');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      setResult(null);
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/plain': ['.txt'], 'text/csv': ['.csv'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);

    try {
      const { data } = await api.post('/ingestions/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(data);
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Please check the file format.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Upload Data</h2>
        <p>Ingest emission data from SAP, utility bills, or corporate travel exports.</p>
      </div>

      {/* Source type selector */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">Select Data Source</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
          {SOURCE_TYPES.map((src) => (
            <button
              key={src.value}
              onClick={() => setSourceType(src.value)}
              style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                border: `2px solid ${sourceType === src.value ? 'var(--accent-primary)' : 'var(--border)'}`,
                background: sourceType === src.value ? 'var(--accent-primary-subtle)' : 'var(--bg-elevated)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all var(--transition-fast)',
              }}
            >
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem', marginBottom: 4 }}>
                {src.label}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{src.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Dropzone */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
          <input {...getInputProps()} />
          <div className="dropzone-icon">📁</div>
          {file ? (
            <>
              <div className="dropzone-text" style={{ color: 'var(--accent-primary)' }}>{file.name}</div>
              <div className="dropzone-hint">{(file.size / 1024).toFixed(1)} KB — Click or drag to replace</div>
            </>
          ) : (
            <>
              <div className="dropzone-text">
                {isDragActive ? 'Drop your file here...' : 'Drag & drop a file, or click to browse'}
              </div>
              <div className="dropzone-hint">Supports .txt and .csv files up to 10 MB</div>
            </>
          )}
        </div>

        {file && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
            <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
              {uploading ? (
                <><div className="spinner" style={{ width: 16, height: 16, borderWidth: 2, marginRight: 6 }} /> Processing...</>
              ) : (
                'Upload & Parse'
              )}
            </button>
          </div>
        )}
      </div>

      {/* Result / Error */}
      {error && (
        <div className="upload-result error">
          <strong>❌ Upload Failed</strong>
          <p style={{ marginTop: 8, color: 'var(--text-secondary)' }}>{error}</p>
        </div>
      )}

      {result && (
        <div className="upload-result success">
          <strong>✅ Upload Successful</strong>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginTop: 16 }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>ROWS PARSED</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{result.rows_parsed}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>FLAGGED</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-flagged)' }}>{result.rows_flagged}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>ERRORS</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-rejected)' }}>{result.parse_errors?.length || 0}</div>
            </div>
          </div>

          {result.parse_errors?.length > 0 && (
            <div className="parse-errors">
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8 }}>Parse Errors</h4>
              {result.parse_errors.map((err, i) => (
                <div key={i} className="parse-error-item">
                  <span className="parse-error-row">Row {err.row}</span>
                  <span className="parse-error-msg">{err.error}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
