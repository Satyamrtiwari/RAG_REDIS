import React from 'react';
import { Sun, Moon, User, BarChart2, Zap } from 'lucide-react';

export default function Navbar({
  userId,
  onChangeName,
  theme,
  onToggleTheme,
  healthStatus,
  onToggleAnalytics,
  isAnalyticsOpen
}) {
  const isHealthy = healthStatus?.status === 'healthy';

  return (
    <header style={{
      height: '64px',
      borderBottom: '1px solid var(--border-color)',
      backgroundColor: 'var(--bg-secondary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.5rem',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      {/* Brand Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          backgroundColor: 'var(--accent-pink)',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Zap size={20} />
        </div>
        <div>
          <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
            DocuQuery <span style={{ color: 'var(--accent-pink)' }}>AI</span>
          </h1>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Enterprise RAG & Redis Cache
          </p>
        </div>
      </div>

      {/* Center / Right Control Cluster */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Health Status Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.75rem',
          borderRadius: '9999px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isHealthy ? '#10b981' : '#f59e0b'
          }} className="animate-pulse-slow" />
          <span>{isHealthy ? 'System Status: OK' : 'Connecting...'}</span>
        </div>

        {/* Analytics Drawer Toggle */}
        <button
          onClick={onToggleAnalytics}
          style={{
            padding: '0.45rem 0.85rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: isAnalyticsOpen ? 'var(--accent-pink-light)' : 'var(--bg-card)',
            color: isAnalyticsOpen ? 'var(--accent-pink)' : 'var(--text-primary)',
            fontSize: '0.85rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.15s ease'
          }}
        >
          <BarChart2 size={16} /> Live Metrics
        </button>

        {/* Theme Switcher Toggle */}
        <button
          onClick={onToggleTheme}
          title="Toggle Day / Night Mode"
          style={{
            padding: '0.45rem 0.85rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.15s ease'
          }}
        >
          {theme === 'light' ? <Sun size={16} style={{ color: '#eab308' }} /> : <Moon size={16} style={{ color: '#818cf8' }} />}
          <span>{theme === 'light' ? 'Day Mode' : 'Night Mode'}</span>
        </button>

        {/* User Session Badge */}
        <button
          onClick={onChangeName}
          title="Click to switch session user"
          style={{
            padding: '0.45rem 0.85rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.15s ease'
          }}
        >
          <User size={16} style={{ color: 'var(--accent-pink)' }} />
          <span>{userId || 'Guest'}</span>
        </button>
      </div>
    </header>
  );
}
