import React, { useState } from 'react';
import { User, Sparkles, ArrowRight } from 'lucide-react';

export default function WelcomeModal({ isOpen, onSubmitInitialName }) {
  const [nameInput, setNameInput] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanName = nameInput.trim();
    if (cleanName) {
      onSubmitInitialName(cleanName);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.65)',
      backdropFilter: 'blur(6px)',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem'
    }}>
      <div className="animate-fade-in" style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '16px',
        padding: '2.5rem',
        maxWidth: '460px',
        width: '100%',
        boxShadow: 'var(--shadow-md)',
        textAlign: 'center'
      }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'var(--accent-pink-light)',
          color: 'var(--accent-pink)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.25rem auto'
        }}>
          <Sparkles size={28} />
        </div>

        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Welcome to DocuQuery AI
        </h2>
        
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.75rem', lineHeight: 1.5 }}>
          Enter your name or handle to create a personalized, isolated document & cache session:
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ position: 'relative' }}>
            <User size={18} style={{
              position: 'absolute',
              left: '14px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)'
            }} />
            <input
              type="text"
              placeholder="e.g. Satyam, Recruiter_John"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              required
              autoFocus
              style={{
                width: '100%',
                padding: '0.875rem 1rem 0.875rem 2.75rem',
                borderRadius: '10px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                outline: 'none',
                transition: 'border-color 0.15s ease'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={!nameInput.trim()}
            style={{
              padding: '0.875rem 1.5rem',
              borderRadius: '10px',
              border: 'none',
              backgroundColor: nameInput.trim() ? 'var(--accent-pink)' : 'var(--border-color)',
              color: '#ffffff',
              fontSize: '0.95rem',
              fontWeight: 600,
              cursor: nameInput.trim() ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease'
            }}
          >
            Start Workspace Session <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
