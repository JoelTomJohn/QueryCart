import React, { useEffect, useRef } from 'react';
import MessageItem from './MessageItem';
import ExampleQueries from './ExampleQueries';
import { AlertCircle, Bot, Sparkles, MessageSquare } from 'lucide-react';

export default function MessageList({
  messages,
  loading,
  error,
  onRetry,
  onSelectExample
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, error]);

  const isEmpty = messages.length === 0;

  return (
    <div className="messages-container" role="log" aria-live="polite">
      {isEmpty && (
        <div className="welcome-hero">
          <div className="welcome-icon-glow">
            <Bot size={26} />
          </div>
          <h2 className="welcome-hero-title">Every Order Made Easy.</h2>
          <p className="welcome-hero-subtitle">
            QueryCart queries your verified 60-order dataset using Google Gemini function calling and authoritative Python calculations.
            Click any suggested query below or type your own question:
          </p>
          <ExampleQueries onSelectQuestion={onSelectExample} disabled={loading} />
        </div>
      )}

      {messages.map((msg, index) => (
        <MessageItem key={index} message={msg} />
      ))}

      {loading && (
        <div className="loading-row" aria-label="QueryCart is thinking">
          <div className="avatar bot-avatar">
            <Bot size={18} />
          </div>
          <div className="loading-bubble">
            <div className="dots-container">
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span className="loading-dot" />
            </div>
            <span className="loading-text">
              Analyzing dataset...
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="error-banner" role="alert">
          <div className="error-content-left">
            <AlertCircle size={18} className="error-icon" />
            <span className="error-message-text">{error}</span>
          </div>
          {onRetry && !/quota|429|resource_exhausted/i.test(error) && (
            <button type="button" className="btn-retry" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
