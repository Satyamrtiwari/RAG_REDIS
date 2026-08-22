import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, User, Zap, Brain, Database, HardDrive, RefreshCw } from 'lucide-react';

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  activeDocId,
  userId
}) {
  const [inputQuery, setInputQuery] = useState('');
  const [bypassCache, setBypassCache] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    onSendMessage(inputQuery.trim(), bypassCache);
    setInputQuery('');
  };

  const renderCacheBadge = (msg) => {
    if (msg.role !== 'assistant' || msg.isGreeting) return null;

    const hitType = msg.cacheHitType || 'none';
    const latency = msg.latencyMs ? `${msg.latencyMs}ms` : '';

    if (hitType === 'exact') {
      return (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.25rem 0.6rem', borderRadius: '9999px', backgroundColor: 'var(--pill-exact-bg)', color: 'var(--pill-exact-text)', fontSize: '0.75rem', fontWeight: 600 }}>
          <Zap size={13} /> Exact Redis Hit • {latency}
        </div>
      );
    }

    if (hitType === 'semantic') {
      return (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.25rem 0.6rem', borderRadius: '9999px', backgroundColor: 'var(--pill-semantic-bg)', color: 'var(--pill-semantic-text)', fontSize: '0.75rem', fontWeight: 600 }}>
          <Brain size={13} /> Semantic Cache Hit • {latency}
        </div>
      );
    }

    return (
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.25rem 0.6rem', borderRadius: '9999px', backgroundColor: 'var(--pill-rag-bg)', color: 'var(--pill-rag-text)', fontSize: '0.75rem', fontWeight: 600 }}>
        <Database size={13} /> Full RAG Vector Search • {latency}
      </div>
    );
  };

  return (
    <main style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 64px)',
      backgroundColor: 'var(--bg-primary)'
    }}>
      {/* Active Document Subheader */}
      <div style={{
        padding: '0.75rem 1.5rem',
        borderBottom: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-secondary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
          <span>Active Context:</span>
          <span style={{ fontWeight: 600, color: 'var(--accent-pink)', padding: '0.15rem 0.5rem', borderRadius: '6px', backgroundColor: 'var(--accent-pink-light)' }}>
            📄 {activeDocId || 'None'}
          </span>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={bypassCache}
            onChange={(e) => setBypassCache(e.target.checked)}
            style={{ cursor: 'pointer' }}
          />
          <span>Bypass Redis Cache</span>
        </label>
      </div>

      {/* Messages Timeline */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem'
      }}>
        {messages.length === 0 ? (
          <div style={{
            margin: 'auto',
            textAlign: 'center',
            maxWidth: '500px',
            padding: '2rem'
          }} className="animate-fade-in">
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: 'var(--accent-pink-light)',
              color: 'var(--accent-pink)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem auto'
            }}>
              <Bot size={24} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              How can I help you today, {userId}?
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Ask questions about your uploaded documents. Exact answers will be cached in Redis for high-speed retrieval!
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
              {[
                "What is the monthly internet stipend for a Tier 2 Senior Engineer?",
                "What is the maximum daily meal allowance for domestic travel?",
                "What is Kisaanu Nexus?",
                "namaste kaise ho aap?"
              ].map((sampleQ, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(sampleQ, bypassCache)}
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  💬 {sampleQ}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className="animate-fade-in"
              style={{
                display: 'flex',
                gap: '1rem',
                maxWidth: '85%',
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
              }}
            >
              {/* Avatar Icon */}
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                backgroundColor: msg.role === 'user' ? 'var(--text-primary)' : 'var(--accent-pink)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>

              {/* Message Content Bubble */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{
                  padding: '1rem 1.25rem',
                  borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  backgroundColor: msg.role === 'user' ? 'var(--accent-pink)' : 'var(--bg-card)',
                  color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-color)',
                  boxShadow: 'var(--shadow-sm)',
                  fontSize: '0.925rem',
                  lineHeight: 1.6
                }}>
                  {msg.role === 'user' ? (
                    <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  )}
                </div>

                {/* Performance Pill Badges */}
                {msg.role === 'assistant' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {renderCacheBadge(msg)}
                    {!msg.isGreeting && msg.cacheHitType !== 'none' && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        💾 2,500 Tokens Saved
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Spinner */}
        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--accent-pink-light)', color: 'var(--accent-pink)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RefreshCw size={16} className="animate-pulse-slow" />
            </div>
            <span>RAG Engine synthesizing context...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSubmit} style={{
        padding: '1rem 1.5rem',
        borderTop: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-secondary)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          padding: '0.5rem 0.75rem',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <input
            type="text"
            placeholder={`Ask a question about '${activeDocId}'...`}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
            style={{
              flex: 1,
              border: 'none',
              backgroundColor: 'transparent',
              color: 'var(--text-primary)',
              fontSize: '0.95rem',
              outline: 'none',
              padding: '0.25rem 0.5rem'
            }}
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            style={{
              padding: '0.6rem 1rem',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: inputQuery.trim() && !isLoading ? 'var(--accent-pink)' : 'var(--border-color)',
              color: '#ffffff',
              fontWeight: 600,
              cursor: inputQuery.trim() && !isLoading ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 0.15s ease'
            }}
          >
            Send <Send size={15} />
          </button>
        </div>
      </form>
    </main>
  );
}
