import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import KpiCards from './components/KpiCards';
import CategoryChart from './components/CategoryChart';
import OrdersTable from './components/OrdersTable';
import MessageList from './components/MessageList';
import ChatInput from './components/ChatInput';
import SplashScreen from './components/SplashScreen';
import * as api from './api';
import { Bot, Sparkles, MessageSquareCode } from 'lucide-react';

const INITIAL_DASHBOARD = {
  metrics: {
    total_orders: 60,
    net_sales_inr: 397678.0,
    delivered_sales_inr: 371040.0,
    gross_sales_inr: 470312.0,
    delivered_orders: 48,
    cancelled_orders: 7,
    cancelled_amount_inr: 72634.0,
    cancellation_rate_percent: 11.67,
    returned_orders: 3,
    processing_orders: 1,
    shipped_orders: 1,
  },
  category_sales: [
    { category: 'Furniture', orders: 10, sales_inr: 182985.0 },
    { category: 'Electronics', orders: 21, sales_inr: 162762.0 },
    { category: 'Accessories', orders: 18, sales_inr: 44057.0 },
    { category: 'Stationery', orders: 11, sales_inr: 7874.0 },
  ],
  recent_orders: [],
  all_orders: [],
};

export default function App({ initialShowSplash = true }) {
  const [showSplash, setShowSplash] = useState(initialShowSplash);
  const [activeTab, setActiveTab] = useState('overview');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUserMessage, setLastUserMessage] = useState(null);
  const [health, setHealth] = useState(null);
  const [dashboardData, setDashboardData] = useState(INITIAL_DASHBOARD);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    let mounted = true;

    // Fetch system health
    if (typeof api.fetchHealth === 'function') {
      api.fetchHealth()
        .then((data) => {
          if (mounted) setHealth(data);
        })
        .catch(() => {
          if (mounted) {
            setHealth({ status: 'degraded', total_orders: 60, gemini_configured: false });
          }
        });
    }

    // Fetch dashboard data
    if (typeof api.fetchDashboard === 'function') {
      api.fetchDashboard()
        .then((dash) => {
          if (mounted && dash) {
            setDashboardData(dash);
          }
        })
        .catch(() => {
          // Keep authoritative initial dashboard metrics
        });
    }

    return () => {
      mounted = false;
    };
  }, []);

  const handleSendMessage = useCallback(async (content) => {
    if (!content.trim() || loading) return;

    setError(null);
    setLastUserMessage(content);

    const userMsg = { role: 'user', content: content.trim() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setLoading(true);

    try {
      const response = await api.sendChatMessage(content.trim(), messages);
      const assistantMsg = {
        role: 'assistant',
        content: response.reply,
        tool_calls: response.tool_calls || []
      };
      setMessages([...newHistory, assistantMsg]);
    } catch (err) {
      const errMsg = err.message || '';
      const isQuota = err.status === 429 || /quota|429|resource_exhausted/i.test(errMsg);
      if (isQuota) {
        const quotaMsg = {
          role: 'assistant',
          content: '⚠️ **Gemini API Quota Exceeded**: The daily free-tier request limit has been reached on Google Cloud (20 requests/day).\n\n**Your local QueryCart dashboard and tools remain fully active:**\n• Explore and filter all 60 verified orders in the **Orders** tab.\n• Review executive KPI cards and category charts on the **Overview** page.\n• Local Python calculation tools and dataset search remain functional.',
          tool_calls: []
        };
        setMessages([...newHistory, quotaMsg]);
        setError(null);
      } else {
        setError(errMsg || 'Unable to connect to the order analysis service. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [messages, loading]);

  const handleRetry = () => {
    if (error && /quota|429|resource_exhausted/i.test(error)) {
      return;
    }
    if (lastUserMessage) {
      setMessages((prev) => {
        if (prev.length > 0 && prev[prev.length - 1].role === 'user') {
          return prev.slice(0, -1);
        }
        return prev;
      });
      handleSendMessage(lastUserMessage);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
    setError(null);
    setLastUserMessage(null);
  };

  const handleSelectOrderQuery = (queryText) => {
    handleSendMessage(queryText);
    if (activeTab === 'orders') {
      setActiveTab('assistant');
    }
  };

  return (
    <div className="app-container">
      {showSplash && (
        <SplashScreen onComplete={() => setShowSplash(false)} duration={1800} />
      )}

      <Sidebar
        health={health}
        onResetChat={handleResetChat}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <div className="main-viewport">
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          isAiConfigured={health?.gemini_configured ?? health?.openai_configured ?? true}
          modelName={health?.model_name}
          health={health}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        <div className="content-scrollable">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="overview-view animate-fade-in">
              {/* Executive KPI Cards */}
              <KpiCards metrics={dashboardData.metrics} />

              {/* Two Column Split: Analytics & Orders / AI Assistant Panel */}
              <div className="dashboard-grid-layout">
                <div className="dashboard-data-col">
                  {/* Category Revenue Breakdown */}
                  <CategoryChart categories={dashboardData.category_sales} />

                  {/* Recent Orders Preview */}
                  <OrdersTable
                    orders={
                      dashboardData.all_orders && dashboardData.all_orders.length > 0
                        ? dashboardData.all_orders
                        : (dashboardData.recent_orders || [])
                    }
                    onSelectOrderQuery={handleSelectOrderQuery}
                    onNavigateToOrders={() => setActiveTab('orders')}
                    isFullView={false}
                  />
                </div>

                {/* AI Order Assistant Panel */}
                <div className="dashboard-assistant-col">
                  <div className="ai-assistant-panel" id="ai-assistant-section">
                    <div className="ai-assistant-header">
                      <div className="ai-panel-title-group">
                        <div className="ai-panel-icon">
                          <Bot size={18} />
                        </div>
                        <div>
                          <h3 className="ai-panel-title">AI Order Assistant</h3>
                          <p className="ai-panel-subtitle">Natural language queries with Gemini function calling</p>
                        </div>
                      </div>
                      <div className="ai-panel-badge">
                        <Sparkles size={12} />
                        <span>Tool Enabled</span>
                      </div>
                    </div>

                    <div className="ai-assistant-chat-body">
                      <MessageList
                        messages={messages}
                        loading={loading}
                        error={error}
                        onRetry={lastUserMessage ? handleRetry : null}
                        onSelectExample={handleSendMessage}
                      />
                    </div>

                    <div className="ai-assistant-input-wrap">
                      <ChatInput
                        onSendMessage={handleSendMessage}
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ORDERS TAB */}
          {activeTab === 'orders' && (
            <div className="orders-view animate-fade-in">
              <OrdersTable
                orders={
                  dashboardData.all_orders && dashboardData.all_orders.length > 0
                    ? dashboardData.all_orders
                    : dashboardData.recent_orders
                }
                onSelectOrderQuery={handleSelectOrderQuery}
                isFullView={true}
              />
            </div>
          )}

          {/* AI ASSISTANT FULL VIEW TAB */}
          {activeTab === 'assistant' && (
            <div className="assistant-view animate-fade-in">
              <div className="full-chat-workspace">
                <div className="full-chat-header">
                  <div className="ai-panel-icon">
                    <Bot size={20} />
                  </div>
                  <div>
                    <h2 className="full-chat-title">AI Order Assistant</h2>
                    <p className="full-chat-subtitle">Ask questions about orders, customers, cities, and revenue</p>
                  </div>
                </div>

                <div className="full-chat-body">
                  <MessageList
                    messages={messages}
                    loading={loading}
                    error={error}
                    onRetry={lastUserMessage ? handleRetry : null}
                    onSelectExample={handleSendMessage}
                  />
                </div>

                <div className="full-chat-input-bar">
                  <ChatInput
                    onSendMessage={handleSendMessage}
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
