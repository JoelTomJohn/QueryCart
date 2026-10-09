import React from 'react';
import { ArrowUpRight, Search, PieChart, MapPin, Award, DollarSign, UserCheck } from 'lucide-react';

export const EXAMPLE_QUESTIONS = [
  {
    query: "What is the status of order ORD-1025?",
    label: "Order Lookup",
    icon: Search
  },
  {
    query: "How many orders were cancelled?",
    label: "Cancellation Stats",
    icon: PieChart
  },
  {
    query: "Summarize sales by city.",
    label: "City Sales Breakdown",
    icon: MapPin
  },
  {
    query: "Which products sell the most?",
    label: "Top Products",
    icon: Award
  },
  {
    query: "What was the total revenue from Electronics in August?",
    label: "Scoped Revenue",
    icon: DollarSign
  },
  {
    query: "Which customer has spent the most?",
    label: "Top Customer",
    icon: UserCheck
  }
];

export default function ExampleQueries({ onSelectQuestion, disabled }) {
  return (
    <div className="examples-grid" role="region" aria-label="Example Questions">
      {EXAMPLE_QUESTIONS.map((item, idx) => {
        const Icon = item.icon;
        return (
          <button
            key={idx}
            className="example-card"
            onClick={() => onSelectQuestion(item.query)}
            disabled={disabled}
            type="button"
          >
            <div className="example-card-left">
              <div className="example-icon-wrap">
                <Icon size={14} />
              </div>
              <span className="example-query-text">{item.query}</span>
            </div>
            <ArrowUpRight size={14} className="example-arrow-icon" />
          </button>
        );
      })}
    </div>
  );
}
