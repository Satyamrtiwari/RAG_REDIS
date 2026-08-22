import React, { useRef, useState } from 'react';
import { Upload, FileText, Trash2, CheckCircle2, FileCode, File, X } from 'lucide-react';

export default function DocumentSidebar({
  documents,
  activeDocId,
  onSelectDoc,
  onUploadDoc,
  onDeleteDoc,
  isUploading,
  isMobileOpen,
  onCloseMobile
}) {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onUploadDoc(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUploadDoc(e.dataTransfer.files[0]);
    }
  };

  const getFileIcon = (filename) => {
    if (!filename) return <FileText size={18} />;
    const lower = filename.toLowerCase();
    if (lower.endsWith('.pdf')) return <FileText size={18} style={{ color: '#ef4444' }} />;
    if (lower.endsWith('.docx') || lower.endsWith('.doc')) return <File size={18} style={{ color: '#3b82f6' }} />;
    if (lower.endsWith('.md')) return <FileCode size={18} style={{ color: '#8b5cf6' }} />;
    return <FileText size={18} />;
  };

  const sidebarContent = (
    <aside style={{
      width: '300px',
      borderRight: '1px solid var(--border-color)',
      backgroundColor: 'var(--bg-secondary)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '1.25rem',
      boxShadow: isMobileOpen ? 'var(--shadow-md)' : 'none'
    }}>
      {/* Sidebar Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Document Hub
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '9999px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
            {documents.length} Files
          </span>
          {isMobileOpen && (
            <button
              onClick={onCloseMobile}
              style={{ border: 'none', backgroundColor: 'transparent', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
            >
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Upload Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? 'var(--accent-pink)' : 'var(--border-color)'}`,
          borderRadius: '12px',
          padding: '1.25rem 1rem',
          backgroundColor: dragOver ? 'var(--accent-pink-light)' : 'var(--bg-card)',
          textAlign: 'center',
          cursor: 'pointer',
          marginBottom: '1.25rem',
          transition: 'all 0.2s ease'
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.docx,.doc,.md,.txt"
          style={{ display: 'none' }}
        />
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '50%',
          backgroundColor: 'var(--accent-pink-light)',
          color: 'var(--accent-pink)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 0.5rem auto'
        }}>
          <Upload size={18} />
        </div>
        <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
          {isUploading ? 'Ingesting Document...' : 'Upload PDF, DOCX, or MD'}
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Drag & drop or tap to browse
        </p>
      </div>

      {/* Uploading Status Progress */}
      {isUploading && (
        <div style={{
          padding: '0.75rem',
          borderRadius: '8px',
          backgroundColor: 'var(--accent-pink-light)',
          border: '1px solid var(--border-focus)',
          marginBottom: '1rem',
          fontSize: '0.8rem',
          color: 'var(--accent-pink-dark)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <div className="animate-pulse-slow">Processing ...</div>
        </div>
      )}

      {/* Document List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No documents uploaded yet.<br />Upload a PDF to start chatting!
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = activeDocId === doc.document_id;
            return (
              <div
                key={doc.document_id}
                onClick={() => {
                  onSelectDoc(doc.document_id);
                  if (onCloseMobile) onCloseMobile();
                }}
                style={{
                  padding: '0.75rem',
                  borderRadius: '10px',
                  border: `1px solid ${isSelected ? 'var(--accent-pink)' : 'var(--border-color)'}`,
                  backgroundColor: isSelected ? 'var(--accent-pink-light)' : 'var(--bg-card)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', overflow: 'hidden' }}>
                  {getFileIcon(doc.filename)}
                  <div style={{ overflow: 'hidden' }}>
                    <p style={{
                      fontSize: '0.85rem',
                      fontWeight: isSelected ? 600 : 500,
                      color: 'var(--text-primary)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {doc.filename || doc.document_id}
                    </p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      ID: {doc.document_id}
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  {isSelected && <CheckCircle2 size={16} style={{ color: 'var(--accent-pink)' }} />}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteDoc(doc.document_id);
                    }}
                    title="Delete document"
                    style={{
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      padding: '0.25rem',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Fixed View */}
      <div className="hide-on-mobile" style={{ height: 'calc(100vh - 64px)' }}>
        {sidebarContent}
      </div>

      {/* Mobile Slide-Over Drawer Overlay */}
      {isMobileOpen && (
        <div style={{
          position: 'fixed',
          top: '64px',
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 90,
          display: 'flex'
        }} onClick={onCloseMobile}>
          <div onClick={(e) => e.stopPropagation()} style={{ height: '100%' }} className="animate-fade-in">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
