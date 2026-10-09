import React from 'react';
import { Menu, Sparkles, Activity, ShieldCheck, Database, LayoutDashboard, ShoppingBag, Bot } from 'lucide-react';

export default function Header({
  onToggleSidebar,
  isAiConfigured,
  modelName,
  health,
  activeTab,
  onTabChange
}) {
  const isHealthy = health?.status === 'healthy';
  const displayModel = modelName || 'gemini-flash-latest';
  const totalOrders = health?.total_orders ?? 60;

  const tabTitles = {
    overview: 'Welcome to QueryCart',
    orders: 'Orders Management',
    assistant: 'AI Order Assistant'
  };

  const tabSubtitles = {
    overview: 'Real-time e-commerce performance and AI order intelligence across 60 transactions',
    orders: 'Explore, filter, and inspect verified orders from June 2026 to September 2026',
    assistant: 'Ask questions about customers, revenue, status, and cancellations with Gemini function calling'
  };

  return (
    <header className="workspace-header">
      <div className="header-left">
        <button
          className="menu-toggle-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="header-greeting-block">
          <div className="header-title-row">
            <h1 className="header-main-title">
              {tabTitles[activeTab] || 'QueryCart Order Intelligence'}
            </h1>
            <span className="live-status-badge">
              <span className={`live-pulse-dot ${isHealthy ? 'online' : 'connecting'}`} />
              <span>{isHealthy ? 'System Active' : 'Connecting'}</span>
            </span>
          </div>
          <p className="header-subtitle">
            {tabSubtitles[activeTab] || 'AI-Powered Order Intelligence'}
          </p>
        </div>
      </div>

      <div className="header-right">
        {/* Connection status indicators */}
        <div className="header-connection-group">
          <div className={`connection-pill ${isHealthy ? 'connected' : 'connecting'}`} title="Backend FastAPI status">
            <Activity size={13} className="conn-icon" />
            <span className="conn-label">{isHealthy ? 'Backend Connected' : 'Connecting...'}</span>
          </div>

          <div className="model-badge" title={`Active AI Model: ${displayModel}`}>
            <Sparkles size={13} className="sparkle-icon" />
            <span className="model-name">{isAiConfigured ? displayModel : 'Gemini Configured'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
