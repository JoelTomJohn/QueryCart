import React from 'react';
import { Package, TrendingUp, CheckCircle2, XCircle, ArrowUpRight } from 'lucide-react';

export function formatINR(val) {
  if (val === null || val === undefined) return '₹0';
  const num = Math.round(Number(val));
  return '₹' + num.toLocaleString('en-IN');
}

export default function KpiCards({ metrics }) {
  const totalOrders = metrics?.total_orders ?? 60;
  const netSales = metrics?.net_sales_inr ?? 397678;
  const deliveredOrders = metrics?.delivered_orders ?? 48;
  const cancelledOrders = metrics?.cancelled_orders ?? 7;
  const deliveredSales = metrics?.delivered_sales_inr ?? 371040;
  const cancelledAmount = metrics?.cancelled_amount_inr ?? 72634;

  const cards = [
    {
      id: 'kpi-total-orders',
      title: 'Total Orders',
      value: totalOrders,
      formatted: totalOrders.toString(),
      subtext: 'Jun 2026 – Sep 2026',
      badge: '100% Indexed',
      badgeType: 'neutral',
      icon: Package,
      accentColor: '#38bdf8', // electric sky blue
      glowClass: 'glow-blue',
    },
    {
      id: 'kpi-total-sales',
      title: 'Total Sales',
      value: netSales,
      formatted: formatINR(netSales),
      subtext: 'Net Revenue (excl. cancelled)',
      badge: '4 Categories',
      badgeType: 'positive',
      icon: TrendingUp,
      accentColor: '#8b5cf6', // electric violet
      glowClass: 'glow-violet',
    },
    {
      id: 'kpi-delivered-orders',
      title: 'Delivered Orders',
      value: deliveredOrders,
      formatted: deliveredOrders.toString(),
      subtext: `${formatINR(deliveredSales)} delivered`,
      badge: '80.0% Success',
      badgeType: 'positive',
      icon: CheckCircle2,
      accentColor: '#10b981', // emerald
      glowClass: 'glow-emerald',
    },
    {
      id: 'kpi-cancelled-orders',
      title: 'Cancelled Orders',
      value: cancelledOrders,
      formatted: cancelledOrders.toString(),
      subtext: `${formatINR(cancelledAmount)} cancelled`,
      badge: '11.7% Rate',
      badgeType: 'warning',
      icon: XCircle,
      accentColor: '#f43f5e', // rose
      glowClass: 'glow-rose',
    },
  ];

  return (
    <section className="kpi-grid" aria-label="Key Performance Indicators">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.id} className={`kpi-card ${card.glowClass}`} id={card.id}>
            <div className="kpi-card-header">
              <span className="kpi-title">{card.title}</span>
              <div
                className="kpi-icon-badge"
                style={{
                  backgroundColor: `${card.accentColor}18`,
                  color: card.accentColor,
                  borderColor: `${card.accentColor}33`,
                }}
              >
                <Icon size={18} />
              </div>
            </div>

            <div className="kpi-card-body">
              <div className="kpi-value">{card.formatted}</div>
              <div className="kpi-footer">
                <span className={`kpi-trend-pill ${card.badgeType}`}>
                  {card.badge}
                </span>
                <span className="kpi-subtext">{card.subtext}</span>
              </div>
            </div>
          </div>
        );
      })}
    </section>
  );
}
