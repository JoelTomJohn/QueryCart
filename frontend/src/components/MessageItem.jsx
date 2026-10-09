import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Wrench, Copy, Check, Terminal } from 'lucide-react';

export default function MessageItem({ message }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (message.content) {
      navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className={`avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`} aria-hidden="true">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <div className="tool-calls-badge-list" aria-label="Tools used">
            {message.tool_calls.map((t, idx) => (
              <span
                key={idx}
                className="tool-badge"
                title={`Tool parameters: ${JSON.stringify(t.arguments || {})}`}
              >
                <Terminal size={11} className="tool-icon" />
                <span className="tool-name">{t.tool_name}</span>
                {t.arguments?.order_id && (
                  <span className="tool-arg-chip">{t.arguments.order_id}</span>
                )}
              </span>
            ))}
          </div>
        )}

        {isUser ? (
          <div className="user-message-content">{message.content}</div>
        ) : (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {!isUser && message.content && (
          <div className="message-action-bar">
            <button
              type="button"
              onClick={handleCopy}
              className="btn-copy-reply"
              title="Copy answer"
              aria-label="Copy answer to clipboard"
            >
              {copied ? <Check size={12} className="copy-success-icon" /> : <Copy size={12} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
