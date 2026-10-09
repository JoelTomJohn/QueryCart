import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import SplashScreen from '../components/SplashScreen';

describe('SplashScreen Component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders QueryCart, tagline, and subtitle according to specification', () => {
    render(<SplashScreen onComplete={() => {}} duration={1800} />);

    // 1. Display QueryCart as main heading
    expect(screen.getByRole('heading', { level: 1, name: 'QueryCart' })).toBeInTheDocument();

    // 2. Display Every Order Made Easy. as prominent tagline
    expect(screen.getByText('Every Order Made Easy.')).toBeInTheDocument();

    // 3. Display AI-Powered Order Intelligence as smaller subtitle
    expect(screen.getByText('AI-Powered Order Intelligence')).toBeInTheDocument();

    // 4. Do NOT display "Welcome to QueryCart" on the splash screen
    expect(screen.queryByText(/Welcome to QueryCart/i)).not.toBeInTheDocument();

    // 5. Displays subtle professional loading animation
    expect(screen.getByText(/Loading workspace/i)).toBeInTheDocument();
  });

  it('triggers onComplete callback after duration (1.5-2 seconds)', () => {
    const handleComplete = vi.fn();
    render(<SplashScreen onComplete={handleComplete} duration={1800} />);

    expect(handleComplete).not.toHaveBeenCalled();

    // Fast-forward timers by duration
    act(() => {
      vi.advanceTimersByTime(1800);
    });

    expect(handleComplete).toHaveBeenCalledTimes(1);
  });
});
