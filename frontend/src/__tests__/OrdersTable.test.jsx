import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import OrdersTable from '../components/OrdersTable';

const MOCK_ORDERS = [
  // 3 Returned orders
  { order_id: 'ORD-1001', customer_name: 'Alice Smith', product: 'Desk Lamp', city: 'Mumbai', category: 'Furniture', quantity: 1, total_inr: 1200, status: 'returned', order_date: '2026-09-01' },
  { order_id: 'ORD-1002', customer_name: 'Bob Jones', product: 'Keyboard', city: 'Delhi', category: 'Electronics', quantity: 1, total_inr: 2500, status: 'Returned', order_date: '2026-09-02' },
  { order_id: 'ORD-1003', customer_name: 'Charlie Brown', product: 'Notebook', city: 'Bangalore', category: 'Stationery', quantity: 3, total_inr: 600, status: ' returned ', order_date: '2026-09-03' },

  // 1 Shipped order
  { order_id: 'ORD-1004', customer_name: 'David Wilson', product: 'Mousepad', city: 'Kolkata', category: 'Accessories', quantity: 2, total_inr: 800, status: 'shipped', order_date: '2026-09-04' },

  // 1 Processing order
  { order_id: 'ORD-1005', customer_name: 'Eva Green', product: 'USB Cable', city: 'Chennai', category: 'Accessories', quantity: 1, total_inr: 450, status: 'processing', order_date: '2026-09-05' },

  // 7 Cancelled orders
  { order_id: 'ORD-1006', customer_name: 'Frank Miller', product: 'Chair', city: 'Hyderabad', category: 'Furniture', quantity: 1, total_inr: 4500, status: 'cancelled', order_date: '2026-09-06' },
  { order_id: 'ORD-1007', customer_name: 'Grace Hopper', product: 'Monitor', city: 'Pune', category: 'Electronics', quantity: 1, total_inr: 12000, status: 'cancelled', order_date: '2026-09-07' },
  { order_id: 'ORD-1008', customer_name: 'Henry Ford', product: 'Pen Pack', city: 'Jaipur', category: 'Stationery', quantity: 5, total_inr: 500, status: 'cancelled', order_date: '2026-09-08' },
  { order_id: 'ORD-1009', customer_name: 'Ivy Taylor', product: 'Webcam', city: 'Ahmedabad', category: 'Electronics', quantity: 1, total_inr: 3200, status: 'cancelled', order_date: '2026-09-09' },
  { order_id: 'ORD-1010', customer_name: 'Jack Ryan', product: 'Backpack', city: 'Surat', category: 'Accessories', quantity: 1, total_inr: 1800, status: 'cancelled', order_date: '2026-09-10' },
  { order_id: 'ORD-1011', customer_name: 'Kate Winslet', product: 'Stapler', city: 'Lucknow', category: 'Stationery', quantity: 2, total_inr: 300, status: 'cancelled', order_date: '2026-09-11' },
  { order_id: 'ORD-1012', customer_name: 'Leo Tolstoy', product: 'Coffee Mug', city: 'Kanpur', category: 'Accessories', quantity: 2, total_inr: 700, status: 'cancelled', order_date: '2026-09-12' },

  // 10 Delivered orders (more than 7 to test max 7 limit)
  { order_id: 'ORD-1013', customer_name: 'Mary Poppins', product: 'Laptop Stand', city: 'Nagpur', category: 'Accessories', quantity: 1, total_inr: 1500, status: 'delivered', order_date: '2026-09-13' },
  { order_id: 'ORD-1014', customer_name: 'Nathan Drake', product: 'Headphones', city: 'Indore', category: 'Electronics', quantity: 1, total_inr: 5500, status: 'delivered', order_date: '2026-09-14' },
  { order_id: 'ORD-1015', customer_name: 'Olivia Wilde', product: 'Bookshelf', city: 'Thane', category: 'Furniture', quantity: 1, total_inr: 8900, status: 'delivered', order_date: '2026-09-15' },
  { order_id: 'ORD-1016', customer_name: 'Peter Parker', product: 'Power Bank', city: 'Bhopal', category: 'Electronics', quantity: 1, total_inr: 2100, status: 'delivered', order_date: '2026-09-16' },
  { order_id: 'ORD-1017', customer_name: 'Quinn Fabray', product: 'Desk Mat', city: 'Patna', category: 'Accessories', quantity: 1, total_inr: 950, status: 'delivered', order_date: '2026-09-17' },
  { order_id: 'ORD-1018', customer_name: 'Rachel Green', product: 'Planner', city: 'Vadodara', category: 'Stationery', quantity: 1, total_inr: 400, status: 'delivered', order_date: '2026-09-18' },
  { order_id: 'ORD-1019', customer_name: 'Steve Rogers', product: 'Bluetooth Speaker', city: 'Ghaziabad', category: 'Electronics', quantity: 1, total_inr: 3400, status: 'delivered', order_date: '2026-09-19' },
  { order_id: 'ORD-1020', customer_name: 'Tony Stark', product: 'Smart Watch', city: 'Ludhiana', category: 'Electronics', quantity: 1, total_inr: 15000, status: 'delivered', order_date: '2026-09-20' },
  { order_id: 'ORD-1021', customer_name: 'Uma Thurman', product: 'Ergonomic Mouse', city: 'Agra', category: 'Electronics', quantity: 1, total_inr: 2800, status: 'delivered', order_date: '2026-09-21' },
  { order_id: 'ORD-1022', customer_name: 'Victor Stone', product: 'Monitor Arm', city: 'Nashik', category: 'Furniture', quantity: 1, total_inr: 4200, status: 'delivered', order_date: '2026-09-22' },
];

describe('OrdersTable Component (Overview & Recent Orders)', () => {
  it('renders initial Overview table with default All filter showing max 7 orders and correct total count', () => {
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} />);

    // Should display exactly 7 table rows in Overview mode
    const rows = screen.getAllByRole('row');
    // 1 header row + 7 data rows = 8
    expect(rows).toHaveLength(8);

    // Initial count message displays 7 of 22 real orders
    expect(screen.getByText('Displaying 7 of 22 real orders')).toBeInTheDocument();
  });

  it('filters correctly by Returned status (fewer than 7 matches)', () => {
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} />);

    const returnedBtn = screen.getByRole('tab', { name: /returned/i });
    fireEvent.click(returnedBtn);

    // Only 3 returned orders should be displayed
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(4); // 1 header + 3 rows

    expect(screen.getByText('ORD-1001')).toBeInTheDocument();
    expect(screen.getByText('ORD-1002')).toBeInTheDocument();
    expect(screen.getByText('ORD-1003')).toBeInTheDocument();
    expect(screen.queryByText('ORD-1004')).not.toBeInTheDocument();

    // Dynamic count message shows 3 of 3 matching orders
    expect(screen.getByText('Displaying 3 of 3 matching orders')).toBeInTheDocument();
  });

  it('filters correctly by Delivered status when more than 7 orders match', () => {
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} />);

    const deliveredBtn = screen.getByRole('tab', { name: /delivered/i });
    fireEvent.click(deliveredBtn);

    // Should cap display at 7 rows in Overview mode even though 10 match
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(8); // 1 header + 7 rows

    // Dynamic count message clearly distinguishes displayed vs total matching
    expect(screen.getByText('Displaying 7 of 10 matching orders')).toBeInTheDocument();
  });

  it('filters correctly by Cancelled status', () => {
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} />);

    const cancelledBtn = screen.getByRole('tab', { name: /cancelled/i });
    fireEvent.click(cancelledBtn);

    // 7 cancelled orders match and are displayed
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(8); // 1 header + 7 rows

    expect(screen.getByText('ORD-1006')).toBeInTheDocument();
    expect(screen.getByText('ORD-1012')).toBeInTheDocument();
    expect(screen.getByText('Displaying 7 of 7 matching orders')).toBeInTheDocument();
  });

  it('filters correctly by Shipped and Processing statuses (single matches)', () => {
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} />);

    // Shipped
    const shippedBtn = screen.getByRole('tab', { name: /shipped/i });
    fireEvent.click(shippedBtn);
    expect(screen.getByText('ORD-1004')).toBeInTheDocument();
    expect(screen.getByText('Displaying 1 of 1 matching orders')).toBeInTheDocument();

    // Processing
    const processingBtn = screen.getByRole('tab', { name: /processing/i });
    fireEvent.click(processingBtn);
    expect(screen.getByText('ORD-1005')).toBeInTheDocument();
    expect(screen.getByText('Displaying 1 of 1 matching orders')).toBeInTheDocument();
  });

  it('restores unfiltered list when All filter is clicked after another filter', () => {
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} />);

    // Click Returned first
    const returnedBtn = screen.getByRole('tab', { name: /returned/i });
    fireEvent.click(returnedBtn);
    expect(screen.getByText('Displaying 3 of 3 matching orders')).toBeInTheDocument();

    // Now click All Orders
    const allBtn = screen.getByRole('tab', { name: /all/i });
    fireEvent.click(allBtn);

    // Restores to 7 displayed rows and All count message
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(8);
    expect(screen.getByText('Displaying 7 of 22 real orders')).toBeInTheDocument();
  });

  it('handles small datasets where total orders are fewer than 7', () => {
    const smallOrders = MOCK_ORDERS.slice(0, 4); // 4 orders total (3 returned, 1 shipped)
    render(<OrdersTable orders={smallOrders} isFullView={false} />);

    // Shows all 4 orders when total is fewer than 7
    expect(screen.getByText('Displaying 4 of 4 real orders')).toBeInTheDocument();

    // Filter to shipped (1 order)
    const shippedBtn = screen.getByRole('tab', { name: /shipped/i });
    fireEvent.click(shippedBtn);
    expect(screen.getByText('Displaying 1 of 1 matching orders')).toBeInTheDocument();
  });

  it('navigates to all orders when footer button is clicked', () => {
    const handleNav = vi.fn();
    render(<OrdersTable orders={MOCK_ORDERS} isFullView={false} onNavigateToOrders={handleNav} />);

    const exploreBtn = screen.getByRole('button', { name: /explore all 22 orders/i });
    fireEvent.click(exploreBtn);
    expect(handleNav).toHaveBeenCalledTimes(1);
  });
});
