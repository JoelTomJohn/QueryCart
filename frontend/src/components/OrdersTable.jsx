import React, { useState, useMemo } from 'react';
import { Search, Filter, ShoppingBag, ArrowRight, MessageSquareCode } from 'lucide-react';
import { formatINR } from './KpiCards';

export function StatusBadge({ status }) {
  const norm = (status || '').toLowerCase().trim();

  let badgeClass = 'badge-pending';
  let label = status || 'Pending';

  if (norm === 'delivered') {
    badgeClass = 'badge-delivered';
    label = 'Delivered';
  } else if (norm === 'cancelled') {
    badgeClass = 'badge-cancelled';
    label = 'Cancelled';
  } else if (norm === 'returned') {
    badgeClass = 'badge-returned';
    label = 'Returned';
  } else if (norm === 'shipped') {
    badgeClass = 'badge-shipped';
    label = 'Shipped';
  } else if (norm === 'processing') {
    badgeClass = 'badge-processing';
    label = 'Processing';
  }

  return (
    <span className={`status-badge ${badgeClass}`}>
      <span className="status-indicator-dot" />
      <span>{label}</span>
    </span>
  );
}

export default function OrdersTable({
  orders = [],
  onSelectOrderQuery,
  isFullView = false,
  onNavigateToOrders
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredOrders = useMemo(() => {
    let list = orders;
    if (statusFilter !== 'all') {
      list = list.filter((o) => (o.status || '').toLowerCase() === statusFilter);
    }
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter((o) =>
        (o.order_id && o.order_id.toLowerCase().includes(q)) ||
        (o.customer_name && o.customer_name.toLowerCase().includes(q)) ||
        (o.product && o.product.toLowerCase().includes(q)) ||
        (o.city && o.city.toLowerCase().includes(q)) ||
        (o.category && o.category.toLowerCase().includes(q))
      );
    }
    return list;
  }, [orders, statusFilter, searchTerm]);

  // Display limit: if full view, show up to 60; if overview view, show top 7
  const displayedOrders = isFullView ? filteredOrders : filteredOrders.slice(0, 7);

  const statuses = [
    { id: 'all', label: 'All Orders' },
    { id: 'delivered', label: 'Delivered (48)' },
    { id: 'cancelled', label: 'Cancelled (7)' },
    { id: 'returned', label: 'Returned (3)' },
    { id: 'shipped', label: 'Shipped (1)' },
    { id: 'processing', label: 'Processing (1)' },
  ];

  return (
    <div className={`orders-card ${isFullView ? 'full-view' : ''}`} id="orders-section">
      <div className="orders-header">
        <div className="orders-title-group">
          <div className="orders-icon-badge">
            <ShoppingBag size={18} />
          </div>
          <div>
            <h3 className="orders-title">{isFullView ? 'Orders Management' : 'Recent Orders'}</h3>
            <p className="orders-subtitle">
              {isFullView
                ? `Showing ${filteredOrders.length} of ${orders.length} real orders`
                : 'Latest transactions from active dataset'}
            </p>
          </div>
        </div>

        {!isFullView && onNavigateToOrders && (
          <button
            type="button"
            className="btn-link-action"
            onClick={onNavigateToOrders}
          >
            <span>View All Orders</span>
            <ArrowRight size={14} />
          </button>
        )}
      </div>

      {/* Filter and search toolbar */}
      <div className="orders-toolbar">
        <div className="search-input-wrap">
          <Search size={15} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search by ID, customer, product, city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Filter orders"
          />
          {searchTerm && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearchTerm('')}
              title="Clear search"
            >
              ×
            </button>
          )}
        </div>

        <div className="status-filter-pills" role="tablist" aria-label="Status filters">
          {statuses.map((s) => (
            <button
              key={s.id}
              type="button"
              role="tab"
              aria-selected={statusFilter === s.id}
              className={`filter-pill ${statusFilter === s.id ? 'active' : ''}`}
              onClick={() => setStatusFilter(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="table-wrapper">
        <table className="orders-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Product</th>
              <th>Date</th>
              <th>Amount (INR)</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {displayedOrders.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-table-cell">
                  No orders match your filter criteria.
                </td>
              </tr>
            ) : (
              displayedOrders.map((order) => (
                <tr key={order.order_id} className="order-table-row">
                  <td className="col-order-id">
                    <span className="order-id-badge">{order.order_id}</span>
                  </td>
                  <td className="col-customer">
                    <div className="customer-name">{order.customer_name}</div>
                    <div className="customer-city">{order.city}</div>
                  </td>
                  <td className="col-product">
                    <div className="product-title">{order.product}</div>
                    <div className="product-category">{order.category} (x{order.quantity})</div>
                  </td>
                  <td className="col-date">
                    <span className="order-date-text">{order.order_date}</span>
                  </td>
                  <td className="col-amount">
                    <span className="order-amount-text">{formatINR(order.total_inr)}</span>
                  </td>
                  <td className="col-status">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="col-action" style={{ textAlign: 'right' }}>
                    {onSelectOrderQuery && (
                      <button
                        type="button"
                        className="btn-order-ai-ask"
                        title={`Ask AI assistant about ${order.order_id}`}
                        onClick={() => onSelectOrderQuery(`What is the status of order ${order.order_id}?`)}
                      >
                        <MessageSquareCode size={13} />
                        <span>Ask AI</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!isFullView && orders.length > 7 && (
        <div className="orders-card-footer">
          <span>Displaying 7 of {orders.length} real orders</span>
          {onNavigateToOrders && (
            <button
              type="button"
              className="footer-view-more"
              onClick={onNavigateToOrders}
            >
              Explore all 60 orders →
            </button>
          )}
        </div>
      )}
    </div>
  );
}
