import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import * as api from '../api';

vi.mock('../api', () => ({
  fetchHealth: vi.fn(),
  fetchDashboard: vi.fn(),
  sendChatMessage: vi.fn(),
}));

describe('QueryCart App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.fetchHealth.mockResolvedValue({
      status: 'healthy',
      total_orders: 60,
      gemini_configured: true,
      model_name: 'gemini-2.5-flash',
      dataset_loaded: true
    });
    api.fetchDashboard.mockResolvedValue({
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
        status_breakdown: { delivered: 48, cancelled: 7, returned: 3, shipped: 1, processing: 1 }
      },
      category_sales: [
        { category: 'Furniture', orders: 10, sales_inr: 182985.0 },
        { category: 'Electronics', orders: 21, sales_inr: 162762.0 },
        { category: 'Accessories', orders: 18, sales_inr: 44057.0 },
        { category: 'Stationery', orders: 11, sales_inr: 7874.0 }
      ],
      recent_orders: [],
      all_orders: []
    });
  });

  it('renders branding, tagline, and the 4 example queries', async () => {
    render(<App />);

    expect(screen.getAllByText('QueryCart').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Every Order Made Easy.').length).toBeGreaterThan(0);
    expect(screen.getAllByText('AI-Powered Order Intelligence').length).toBeGreaterThan(0);

    expect(screen.getByText('What is the status of order ORD-1025?')).toBeInTheDocument();
    expect(screen.getByText('How many orders were cancelled?')).toBeInTheDocument();
    expect(screen.getByText('What was the total revenue from Electronics in August?')).toBeInTheDocument();
    expect(screen.getByText('Which customer has spent the most?')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Welcome to QueryCart')).toBeInTheDocument();
      expect(screen.getByText('System Active')).toBeInTheDocument();
      expect(screen.getByText('Your orders, sales, and AI-powered insights — all in one place.')).toBeInTheDocument();
    });

    // Verify System Health and Dataset Specs are removed from the dashboard
    expect(screen.queryByText('System Health')).not.toBeInTheDocument();
    expect(screen.queryByText('Dataset Specs')).not.toBeInTheDocument();
  });

  it('handles sending a message and renders the assistant response with tool badges', async () => {
    api.sendChatMessage.mockResolvedValueOnce({
      reply: 'Order ORD-1025 is delivered.',
      tool_calls: [
        {
          tool_name: 'lookup_order',
          arguments: { order_id: 'ORD-1025' },
          result: { found: true }
        }
      ]
    });

    render(<App />);

    // Click example question
    const exampleBtn = screen.getByText('What is the status of order ORD-1025?');
    fireEvent.click(exampleBtn);

    // Verify user message appears
    expect(screen.getByText('What is the status of order ORD-1025?')).toBeInTheDocument();

    // Verify assistant reply appears
    await waitFor(() => {
      expect(screen.getByText('Order ORD-1025 is delivered.')).toBeInTheDocument();
    });

    // Verify tool badge is rendered
    expect(screen.getByText('lookup_order')).toBeInTheDocument();
  });

  it('displays error banner and retry option when API request fails', async () => {
    api.sendChatMessage.mockRejectedValueOnce(new Error('Network error connecting to API'));

    render(<App />);

    const exampleBtn = screen.getByText('How many orders were cancelled?');
    fireEvent.click(exampleBtn);

    await waitFor(() => {
      expect(screen.getByText(/Network error connecting to API/i)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('resets chat session when reset button is clicked', async () => {
    api.sendChatMessage.mockResolvedValueOnce({
      reply: '7 orders were cancelled.',
      tool_calls: []
    });

    render(<App />);

    const exampleBtn = screen.getByText('How many orders were cancelled?');
    fireEvent.click(exampleBtn);

    await waitFor(() => {
      expect(screen.getByText('7 orders were cancelled.')).toBeInTheDocument();
    });

    // Click reset button
    const resetBtn = screen.getByRole('button', { name: /reset chat session/i });
    fireEvent.click(resetBtn);

    // Verify message list is cleared and welcome hero examples reappear
    expect(screen.queryByText('7 orders were cancelled.')).not.toBeInTheDocument();
  });

  it('handles 429 quota error gracefully: preserves user message and displays friendly assistant note without retry loop', async () => {
    const quotaError = new Error('HTTP 429: Resource has been exhausted (e.g. check quota)');
    quotaError.status = 429;
    api.sendChatMessage.mockRejectedValueOnce(quotaError);

    render(<App />);

    const exampleBtn = screen.getByText('What is the status of order ORD-1025?');
    fireEvent.click(exampleBtn);

    // User message is preserved
    expect(screen.getByText('What is the status of order ORD-1025?')).toBeInTheDocument();

    // Friendly quota response is shown in the chat
    await waitFor(() => {
      expect(screen.getByText(/Gemini API Quota Exceeded/i)).toBeInTheDocument();
      expect(screen.getByText(/daily free-tier request limit/i)).toBeInTheDocument();
    });

    // Retry button is NOT displayed, preventing retry loops
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('filters Overview Recent Orders by status and updates the dynamic order-count message', async () => {
    api.fetchDashboard.mockResolvedValueOnce({
      metrics: {
        total_orders: 4,
        net_sales_inr: 7500,
        delivered_sales_inr: 500,
        gross_sales_inr: 7500,
        delivered_orders: 1,
        cancelled_orders: 1,
        cancelled_amount_inr: 4000,
        cancellation_rate_percent: 25,
        returned_orders: 2,
        processing_orders: 0,
        shipped_orders: 0,
      },
      category_sales: [],
      recent_orders: [],
      all_orders: [
        { order_id: 'ORD-2001', customer_name: 'Pooja', product: 'Lamp', city: 'Delhi', category: 'Furniture', quantity: 1, total_inr: 1000, status: 'returned', order_date: '2026-09-01' },
        { order_id: 'ORD-2002', customer_name: 'Rahul', product: 'Desk', city: 'Pune', category: 'Furniture', quantity: 1, total_inr: 2000, status: 'returned', order_date: '2026-09-02' },
        { order_id: 'ORD-2003', customer_name: 'Amit', product: 'Book', city: 'Goa', category: 'Stationery', quantity: 1, total_inr: 500, status: 'delivered', order_date: '2026-09-03' },
        { order_id: 'ORD-2004', customer_name: 'Sara', product: 'Chair', city: 'Mumbai', category: 'Furniture', quantity: 1, total_inr: 4000, status: 'cancelled', order_date: '2026-09-04' },
      ]
    });

    render(<App />);

    // Wait for dashboard data to load
    await waitFor(() => {
      expect(screen.getByText('Displaying 4 of 4 real orders')).toBeInTheDocument();
    });

    // Click Returned filter pill in Overview
    const returnedTab = screen.getByRole('tab', { name: /returned/i });
    fireEvent.click(returnedTab);

    // Verify only returned orders are visible
    expect(screen.getByText('ORD-2001')).toBeInTheDocument();
    expect(screen.getByText('ORD-2002')).toBeInTheDocument();
    expect(screen.queryByText('ORD-2003')).not.toBeInTheDocument();

    // Verify dynamic count message updates
    expect(screen.getByText('Displaying 2 of 2 matching orders')).toBeInTheDocument();

    // Click All Orders to restore
    const allTab = screen.getByRole('tab', { name: /all/i });
    fireEvent.click(allTab);
    expect(screen.getByText('Displaying 4 of 4 real orders')).toBeInTheDocument();
    expect(screen.getByText('ORD-2003')).toBeInTheDocument();
  });
});


