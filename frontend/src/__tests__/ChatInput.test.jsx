import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChatInput from '../components/ChatInput';

describe('ChatInput Component', () => {
  it('updates text input and fires onSendMessage on button click', () => {
    const mockSend = vi.fn();
    render(<ChatInput onSendMessage={mockSend} disabled={false} />);

    const textarea = screen.getByRole('textbox', { name: /order query input/i });
    const sendButton = screen.getByRole('button', { name: /send message/i });

    // Initially disabled button because input is empty
    expect(sendButton).toBeDisabled();

    fireEvent.change(textarea, { target: { value: 'How many orders in Chennai?' } });
    expect(textarea.value).toBe('How many orders in Chennai?');
    expect(sendButton).not.toBeDisabled();

    fireEvent.click(sendButton);
    expect(mockSend).toHaveBeenCalledWith('How many orders in Chennai?');
    expect(textarea.value).toBe('');
  });

  it('submits on Enter keypress, but allows Shift+Enter for multiline', () => {
    const mockSend = vi.fn();
    render(<ChatInput onSendMessage={mockSend} disabled={false} />);

    const textarea = screen.getByRole('textbox', { name: /order query input/i });
    fireEvent.change(textarea, { target: { value: 'Test query' } });

    // Shift + Enter should not submit
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    expect(mockSend).not.toHaveBeenCalled();

    // Plain Enter should submit
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    expect(mockSend).toHaveBeenCalledWith('Test query');
  });

  it('disables input and submit button when disabled prop is true', () => {
    render(<ChatInput onSendMessage={vi.fn()} disabled={true} />);

    const textarea = screen.getByRole('textbox', { name: /order query input/i });
    const sendButton = screen.getByRole('button', { name: /send message/i });

    expect(textarea).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });
});
