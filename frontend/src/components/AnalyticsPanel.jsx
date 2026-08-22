import React from 'react';
import { BarChart3, Zap, Brain, Database, ShieldCheck, X, RotateCcw } from 'lucide-react';

export default function AnalyticsPanel({ isOpen, onClose, stats, onResetStats, userId }) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: '64px',
      right: 0,
      bottom: 0,
      left: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.4)',
      zIndex: 90,
      display: 'flex',
      justifyContent: 'flex-end'
    }} onClick={onClose}>
      <aside
        onClick={(e) => e.stopPropagation()}
        className="animate-fade-in"
        style={{
          width: '320px',
          maxWidth: '100%',
          borderLeft: '1px solid var(--border-color)',
          backgroundColor: 'var(--bg-secondary)',
          height: '100%',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-md)'
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 size={18} style={{ color: 'var(--accent-pink)' }} />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Live Metrics ({userId || 'Guest'})
            </h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <button
              onClick={onResetStats}
              title="Reset metrics to zero"
              style={{
                border: 'none',
                backgroundColor: 'var(--bg-card)',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.35rem',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <RotateCcw size={14} />
            </button>
            <button
              onClick={onClose}
              style={{ border: 'none', backgroundColor: 'transparent', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Main Hit Rate Highlight Card */}
        <div style={{
          padding: '1.25rem',
          borderRadius: '12px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-sm)',
          textAlign: 'center'
        }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Cache Hit Efficiency
          </p>
          <p style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-pink)', lineHeight: 1 }}>
            {stats?.cache_hit_rate_pct ?? 0}%
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            {stats?.total_cache_hits ?? 0} hits out of {stats?.total_queries ?? 0} total queries
          </p>
        </div>

        {/* Breakdown Grid */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ padding: '0.85rem 1rem', borderRadius: '10px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Zap size={16} style={{ color: 'var(--accent-pink)' }} />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>Exact Redis Hits</span>
            </div>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats?.exact_redis_hits ?? 0}</span>
          </div>

          <div style={{ padding: '0.85rem 1rem', borderRadius: '10px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Brain size={16} style={{ color: '#818cf8' }} />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>Semantic Hits</span>
            </div>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats?.semantic_cache_hits ?? 0}</span>
          </div>

          <div style={{ padding: '0.85rem 1rem', borderRadius: '10px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Database size={16} style={{ color: '#10b981' }} />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>Full RAG Calls</span>
            </div>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>{stats?.rag_llm_calls ?? 0}</span>
          </div>
        </div>

        {/* Savings Summary */}
        <div style={{
          padding: '1rem',
          borderRadius: '10px',
          backgroundColor: 'var(--accent-pink-light)',
          border: '1px solid var(--border-focus)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--accent-pink-dark)' }}>
            <ShieldCheck size={16} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Efficiency Savings</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            <span>Estimated Tokens Saved:</span>
            <span style={{ fontWeight: 700 }}>{(stats?.estimated_tokens_saved ?? 0).toLocaleString()}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
            <span>LLM API Calls Saved:</span>
            <span style={{ fontWeight: 700 }}>{stats?.estimated_llm_calls_avoided ?? 0}</span>
          </div>
        </div>
      </aside>
    </div>
  );
}
