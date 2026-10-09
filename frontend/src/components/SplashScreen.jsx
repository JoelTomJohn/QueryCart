import React, { useEffect, useState } from 'react';
import { ShoppingCart, Sparkles } from 'lucide-react';

export default function SplashScreen({ onComplete, duration = 1800 }) {
  const [isFadingOut, setIsFadingOut] = useState(false);

  useEffect(() => {
    // Begin fade-out slightly before full completion
    const fadeTimer = setTimeout(() => {
      setIsFadingOut(true);
    }, Math.max(duration - 350, 800));

    // Complete transition and trigger unmount
    const finishTimer = setTimeout(() => {
      if (typeof onComplete === 'function') {
        onComplete();
      }
    }, duration);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(finishTimer);
    };
  }, [duration, onComplete]);

  return (
    <div
      className={`splash-screen-overlay ${isFadingOut ? 'fade-out' : ''}`}
      role="status"
      aria-live="polite"
      aria-label="Loading QueryCart"
    >
      <div className="splash-ambient-glow" aria-hidden="true" />

      <div className="splash-content-card">
        {/* Animated Brand Emblem */}
        <div className="splash-icon-wrapper">
          <div className="splash-icon-glow" aria-hidden="true" />
          <div className="splash-icon-box">
            <ShoppingCart size={36} className="splash-cart-icon" />
            <Sparkles size={16} className="splash-sparkle-icon" />
          </div>
        </div>

        {/* Brand Typography */}
        <div className="splash-text-block">
          <h1 className="splash-brand-title">QueryCart</h1>
          <p className="splash-prominent-tagline">Every Order Made Easy.</p>
          <p className="splash-subtitle-badge">AI-Powered Order Intelligence</p>
        </div>

        {/* Subtle, Professional Loading Bar */}
        <div className="splash-loading-section" aria-hidden="true">
          <div className="splash-progress-track">
            <div className="splash-progress-fill" />
          </div>
          <div className="splash-loading-text">
            <span>Loading workspace</span>
            <span className="splash-dots">...</span>
          </div>
        </div>
      </div>
    </div>
  );
}
