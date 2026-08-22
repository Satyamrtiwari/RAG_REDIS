import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DocumentSidebar from './components/DocumentSidebar';
import ChatInterface from './components/ChatInterface';
import AnalyticsPanel from './components/AnalyticsPanel';
import WelcomeModal from './components/WelcomeModal';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://rag-redis-backend.onrender.com';

export default function App() {
  // Theme State ('light' soft pink day mode vs 'dark' night mode)
  const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'light');
  
  // User Session State
  const [userId, setUserId] = useState(() => localStorage.getItem('app_user_id') || '');
  const [isWelcomeModalOpen, setIsWelcomeModalOpen] = useState(!localStorage.getItem('app_user_id'));

  // Document & Context State
  const [documents, setDocuments] = useState([]);
  const [activeDocId, setActiveDocId] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([]);
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Analytics & Health State
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [stats, setStats] = useState({});
  const [healthStatus, setHealthStatus] = useState({ status: 'connecting' });

  // Update Theme Attribute on Body
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  // Initial Data Fetching
  useEffect(() => {
    fetchHealth();
    fetchStats(userId || 'satyam');
  }, []);

  // Fetch Documents & Refresh Stats when UserId changes
  useEffect(() => {
    if (userId) {
      fetchDocuments(userId);
      fetchStats(userId);
    }
  }, [userId]);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        const data = await res.json();
        setHealthStatus(data);
      }
    } catch (e) {
      setHealthStatus({ status: 'degraded' });
    }
  };

  const fetchStats = async (user) => {
    try {
      const targetUser = user || userId || 'satyam';
      const res = await fetch(`${API_BASE_URL}/api/v1/cache/stats?user_id=${encodeURIComponent(targetUser)}`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.warn('Failed to fetch cache stats:', e);
    }
  };

  const handleResetStats = async () => {
    try {
      const targetUser = userId || 'satyam';
      const res = await fetch(`${API_BASE_URL}/api/v1/cache/stats/reset?user_id=${encodeURIComponent(targetUser)}`, {
        method: 'POST'
      });
      if (res.ok) {
        fetchStats(targetUser);
      }
    } catch (e) {
      console.warn('Failed to reset stats:', e);
    }
  };

  const fetchDocuments = async (user) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/documents?user_id=${encodeURIComponent(user)}`);
      if (res.ok) {
        const data = await res.json();
        const docList = data.documents || [];
        setDocuments(docList);
        if (docList.length > 0 && !activeDocId) {
          setActiveDocId(docList[0].document_id);
        }
      }
    } catch (e) {
      console.warn('Failed to fetch documents:', e);
    }
  };

  const handleInitialNameSubmit = (name) => {
    const clean = name.trim();
    setUserId(clean);
    localStorage.setItem('app_user_id', clean);
    setIsWelcomeModalOpen(false);
    setActiveDocId('');
    setDocuments([]);
    setMessages([]);
    fetchDocuments(clean);
    fetchStats(clean);
  };

  const handleUploadDoc = async (file) => {
    if (!file) return;
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId || 'satyam');

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setActiveDocId(data.document_id);
        await fetchDocuments(userId || 'satyam');
        fetchStats(userId || 'satyam');
      } else {
        const errData = await res.json();
        alert(`Upload error: ${errData.detail || 'Failed to upload document'}`);
      }
    } catch (e) {
      alert(`Upload error: ${e.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (docId) => {
    const user = userId || 'satyam';
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/documents/${docId}?user_id=${encodeURIComponent(user)}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        const remaining = documents.filter((d) => d.document_id !== docId);
        setDocuments(remaining);
        fetchStats(user);
        if (activeDocId === docId) {
          setActiveDocId(remaining.length > 0 ? remaining[0].document_id : '');
        }
      } else {
        const errData = await res.json();
        alert(`Failed to delete document: ${errData.detail || 'Delete error'}`);
      }
    } catch (e) {
      alert(`Failed to delete document: ${e.message}`);
    }
  };

  const handleSendMessage = async (questionText, bypassCache) => {
    const userMsg = { role: 'user', content: questionText };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: questionText,
          user_id: userId || 'satyam',
          document_id: activeDocId || 'default',
          bypass_cache: bypassCache
        })
      });

      if (res.ok) {
        const data = await res.json();
        const aiMsg = {
          role: 'assistant',
          content: data.answer,
          cacheHitType: data.cache_hit_type,
          isGreeting: data.is_greeting,
          latencyMs: data.latency_ms
        };
        setMessages((prev) => [...prev, aiMsg]);
        fetchStats(userId || 'satyam');
      } else {
        const errData = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `⚠️ Error: ${errData.detail || 'Server error occurred'}`, isGreeting: true }
        ]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `⚠️ Connection Error: Failed to communicate with FastAPI server.`, isGreeting: true }
      ]);
    } finally {
      setIsLoadingChat(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Welcome Modal Popup */}
      <WelcomeModal
        isOpen={isWelcomeModalOpen}
        onSubmitInitialName={handleInitialNameSubmit}
      />

      {/* Top Navbar */}
      <Navbar
        userId={userId}
        onChangeName={() => setIsWelcomeModalOpen(true)}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        healthStatus={healthStatus}
        onToggleAnalytics={() => setIsAnalyticsOpen(!isAnalyticsOpen)}
        isAnalyticsOpen={isAnalyticsOpen}
        onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
      />

      {/* Main Content Workspace */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Document Sidebar */}
        <DocumentSidebar
          documents={documents}
          activeDocId={activeDocId}
          onSelectDoc={(docId) => setActiveDocId(docId)}
          onUploadDoc={handleUploadDoc}
          onDeleteDoc={handleDeleteDoc}
          isUploading={isUploading}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
        />

        {/* Chat Timeline Area */}
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoadingChat}
          activeDocId={activeDocId}
          userId={userId}
        />

        {/* Analytics Drawer */}
        <AnalyticsPanel
          isOpen={isAnalyticsOpen}
          onClose={() => setIsAnalyticsOpen(false)}
          stats={stats}
          onResetStats={handleResetStats}
          userId={userId}
        />
      </div>
    </div>
  );
}
