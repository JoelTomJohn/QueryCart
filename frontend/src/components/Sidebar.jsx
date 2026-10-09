import React from 'react';
import {
  ShoppingCart,
  LayoutDashboard,
  ShoppingBag,
  Bot,
  RotateCcw,
  Database,
  Zap,
  CheckCircle,
  FileSpreadsheet,
  X
} from 'lucide-react';

export default function Sidebar({
  health,
  onResetChat,
  isOpen,
  onClose,
  activeTab = 'overview',
  onTabChange,
  unreadCount = 0
}) {
  const isHealthy = health?.status === 'healthy';
  const totalOrders = health?.total_orders ?? 60;
  const isAiConfigured = health?.gemini_configured ?? health?.openai_configured ?? true;

  const navItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: LayoutDashboard,
      badge: 'Live',
    },
    {
      id: 'orders',
      label: 'Orders',
      icon: ShoppingBag,
      badge: '60',
    },
    {
      id: 'assistant',
      label: 'AI Assistant',
      icon: Bot,
      badge: 'Gemini',
    },
  ];

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`} aria-label="Sidebar navigation">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-wrapper">
          <div className="brand-logo-icon" aria-hidden="true">
            <ShoppingCart size={20} />
          </div>
          <div className="brand-text-block">
            <div className="brand-title">QueryCart</div>
            <div className="brand-tagline">Ask your orders anything.</div>
            <div className="brand-subtitle">AI-Powered Order Intelligence</div>
          </div>
        </div>
        {isOpen && (
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <div className="sidebar-nav-section">
        <div className="nav-section-title">Navigation</div>
        <nav className="sidebar-nav" role="navigation" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item-btn ${isActive ? 'active' : ''}`}
                onClick={() => {
                  if (onTabChange) onTabChange(item.id);
                  if (isOpen && onClose) onClose();
                }}
                aria-current={isActive ? 'page' : undefined}
                id={`nav-${item.id}`}
              >
                <div className="nav-item-left">
                  <Icon size={18} className="nav-icon" />
                  <span className="nav-label">{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`nav-badge ${isActive ? 'active-badge' : ''}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Health / Status info */}
      <div className="sidebar-content">
        <div>
          <div className="section-label">System Health</div>
          <div className="status-card">
            <div className="status-row">
              <span className="status-label-muted">API Status</span>
              <span className={`status-pill ${isHealthy ? 'online' : 'degraded'}`}>
                <span className="pulse-dot" />
                {isHealthy ? 'Connected' : 'Connecting...'}
              </span>
            </div>
            <div className="status-row">
              <span className="status-label-muted">Dataset</span>
              <span className="status-val-highlight">
                <Database size={13} />
                {totalOrders} Orders Loaded
              </span>
            </div>
            <div className="status-row">
              <span className="status-label-muted">AI Engine</span>
              <span className="status-val-ai">
                <Zap size={13} />
                {isAiConfigured ? 'Gemini Active' : 'Key Needed'}
              </span>
            </div>
          </div>
        </div>

        <div>
          <div className="section-label">Dataset Specs</div>
          <div className="specs-card">
            <div className="specs-row">
              <span className="specs-bullet">•</span>
              <span><strong>Range:</strong> Jun 2026 – Sep 2026</span>
            </div>
            <div className="specs-row">
              <span className="specs-bullet">•</span>
              <span><strong>Currency:</strong> INR (₹)</span>
            </div>
            <div className="specs-row">
              <span className="specs-bullet">•</span>
              <span><strong>Tools:</strong> Lookup, Search, Metrics</span>
            </div>
            <div className="specs-row">
              <span className="specs-bullet">•</span>
              <span><strong>Authoritative:</strong> Python Engine</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <button
          type="button"
          className="btn-reset"
          onClick={onResetChat}
          title="Reset current conversation"
          id="btn-reset-chat"
          aria-label="Reset chat session"
        >
          <RotateCcw size={15} />
          <span>Reset Chat Session</span>
        </button>
      </div>
    </aside>
  );
}
