import React from 'react';
import { Sun, Moon, User, BarChart2, Zap, Menu } from 'lucide-react';

export default function Navbar({
  userId,
  onChangeName,
  theme,
  onToggleTheme,
  healthStatus,
  onToggleAnalytics,
  isAnalyticsOpen,
  onToggleMobileSidebar
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
      padding: '0 1rem',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      {/* Brand Title & Mobile Menu Trigger */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        {/* Mobile Hamburger Button */}
        <button
          onClick={onToggleMobileSidebar}
          className="show-on-mobile"
          title="Open Document Hub"
          style={{
            padding: '0.4rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Menu size={18} />
        </button>

        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '8px',
          backgroundColor: 'var(--accent-pink)',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Zap size={18} />
        </div>
        <div>
          <h1 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
            DocuQuery <span style={{ color: 'var(--accent-pink)' }}>AI</span>
          </h1>
          <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            Enterprise RAG Engine
          </p>
        </div>
      </div>

      {/* Control Cluster */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {/* Health Status Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.3rem 0.6rem',
          borderRadius: '9999px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          fontSize: '0.75rem',
          color: 'var(--text-secondary)'
        }}>
          <span style={{
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            backgroundColor: isHealthy ? '#10b981' : '#f59e0b'
          }} className="animate-pulse-slow" />
          <span className="hide-on-mobile">{isHealthy ? 'System Status: OK' : 'Connecting...'}</span>
        </div>

        {/* Analytics Drawer Toggle */}
        <button
          onClick={onToggleAnalytics}
          title="Live Analytics Metrics"
          style={{
            padding: '0.4rem 0.6rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: isAnalyticsOpen ? 'var(--accent-pink-light)' : 'var(--bg-card)',
            color: isAnalyticsOpen ? 'var(--accent-pink)' : 'var(--text-primary)',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            transition: 'all 0.15s ease'
          }}
        >
          <BarChart2 size={15} />
          <span className="hide-on-mobile">Metrics</span>
        </button>

        {/* Theme Switcher Toggle */}
        <button
          onClick={onToggleTheme}
          title="Toggle Day / Night Mode"
          style={{
            padding: '0.4rem 0.6rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '0.8rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            transition: 'all 0.15s ease'
          }}
        >
          {theme === 'light' ? <Sun size={15} style={{ color: '#eab308' }} /> : <Moon size={15} style={{ color: '#818cf8' }} />}
          <span className="hide-on-mobile">{theme === 'light' ? 'Day' : 'Night'}</span>
        </button>

        {/* User Session Badge */}
        <button
          onClick={onChangeName}
          title="Click to switch session user"
          style={{
            padding: '0.4rem 0.6rem',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-card)',
            color: 'var(--text-primary)',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            transition: 'all 0.15s ease'
          }}
        >
          <User size={15} style={{ color: 'var(--accent-pink)' }} />
          <span>{userId || 'Guest'}</span>
        </button>
      </div>
    </header>
  );
}
