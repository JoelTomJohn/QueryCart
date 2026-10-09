import React, { useState, useRef, useEffect } from 'react';
import { SendHorizonal, CornerDownLeft, Sparkles } from 'lucide-react';

export default function ChatInput({ onSendMessage, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (trimmed && !disabled) {
      onSendMessage(trimmed);
      setText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className="input-container">
      <form onSubmit={handleSubmit} className="input-box-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask a question about orders, customers, status, or revenue..."
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          aria-label="Order query input"
        />
        <button
          type="submit"
          className="btn-send"
          disabled={disabled || !text.trim()}
          aria-label="Send message"
          id="btn-send-message"
        >
          <SendHorizonal size={18} />
        </button>
      </form>
      <div className="input-hints">
        Press <strong>Enter</strong> to send • <strong>Shift + Enter</strong> for new line • Powered by Google Gemini & Python
      </div>
    </div>
  );
}
