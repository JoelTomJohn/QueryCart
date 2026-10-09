import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.data_loader import get_orders

# OpenAI Tool Specifications
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Retrieve exact details for a specific order by its unique Order ID (e.g., 'ORD-1025'). Use this whenever the user asks about a particular order number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The exact order ID to look up, such as 'ORD-1001', 'ORD-1025'."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Search and filter orders by customer name, city, product name, product category, status, or date range. Returns matching orders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Optional customer name filter (case-insensitive partial or exact match, e.g., 'Rahul', 'Sneha Pillai')."
                    },
                    "city": {
                        "type": "string",
                        "description": "Optional city filter (e.g., 'Chennai', 'Bengaluru', 'Kochi', 'Thiruvananthapuram', 'Hyderabad', 'Pune')."
                    },
                    "product": {
                        "type": "string",
                        "description": "Optional product name filter (e.g., 'Wireless Mouse', 'Standing Desk')."
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter. Valid categories: 'Electronics', 'Accessories', 'Stationery', 'Furniture'."
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional status filter. Valid statuses in dataset: 'delivered', 'cancelled', 'returned', 'processing', 'shipped'. Also supports 'not delivered' (all non-delivered orders), 'awaiting delivery' (active processing and shipped orders), or comma-separated values like 'processing,shipped'."
                    },
                    "exclude_status": {
                        "type": "string",
                        "description": "Optional status to exclude (e.g. 'delivered' to find all orders not yet delivered)."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional start date in YYYY-MM-DD format (inclusive boundary)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional end date in YYYY-MM-DD format (inclusive boundary)."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return (default 20, max 100)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_order_metrics",
            "description": "Authoritatively calculate summary statistics, total order counts, gross/net revenues, cancellation counts and rates, and top customer spending rankings. Can be scoped with optional filters like category, city, customer, status, or date range (e.g. August 2026: start_date='2026-08-01', end_date='2026-08-31').",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional filter by category ('Electronics', 'Accessories', 'Stationery', 'Furniture')."
                    },
                    "city": {
                        "type": "string",
                        "description": "Optional filter by city (e.g., 'Chennai', 'Bengaluru')."
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Optional filter by customer name."
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional filter by status ('delivered', 'cancelled', 'returned', 'processing', 'shipped')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Optional start date in YYYY-MM-DD format (inclusive)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional end date in YYYY-MM-DD format (inclusive)."
                    },
                    "top_n_customers": {
                        "type": "integer",
                        "description": "Number of top spending customers to return (default: 5)."
                    }
                }
            }
        }
    }
]


def lookup_order(order_id: str) -> Dict[str, Any]:
    """
    Retrieve exact order details by order ID. Case-insensitive.
    Returns the order dict or a clean error message.
    """
    if not order_id or not isinstance(order_id, str):
        return {
            "found": False,
            "error": "A valid order_id string is required."
        }

    clean_id = order_id.strip().upper()
    orders = get_orders()

    for o in orders:
        if o["order_id"] == clean_id:
            return {
                "found": True,
                "order": o,
                "message": f"Order {clean_id} found for customer {o['customer_name']} with status '{o['status']}'."
            }

    return {
        "found": False,
        "message": f"Order '{order_id.strip()}' was not found in the dataset. Available order IDs range from ORD-1001 to ORD-1060."
    }


def _matches_date(order_date_str: str, start_date: Optional[str], end_date: Optional[str]) -> bool:
    """Helper to check inclusive date bounds formatted as YYYY-MM-DD."""
    if start_date:
        try:
            if order_date_str < start_date.strip():
                return False
        except Exception:
            pass
    if end_date:
        try:
            if order_date_str > end_date.strip():
                return False
        except Exception:
            pass
    return True


def search_orders(
    customer_name: Optional[str] = None,
    city: Optional[str] = None,
    product: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    exclude_status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Filter orders by criteria.
    Supports status filters ('delivered', 'cancelled', 'returned', 'processing', 'shipped'),
    as well as 'not delivered' / 'undelivered', 'awaiting delivery' / 'pending',
    comma-separated statuses ('processing,shipped'), and exclude_status ('delivered').
    """
    orders = get_orders()
    results = []

    c_name = customer_name.strip().lower() if customer_name else None
    c_city = city.strip().lower() if city else None
    c_prod = product.strip().lower() if product else None
    c_cat = category.strip().lower() if category else None
    c_status = status.strip().lower() if status else None
    c_exclude = [s.strip().lower() for s in exclude_status.split(",")] if exclude_status else []

    status_filter_set = None
    not_delivered_mode = False
    awaiting_delivery_mode = False

    if c_status:
        if c_status in ("not delivered", "!delivered", "undelivered", "non-delivered", "not_delivered"):
            not_delivered_mode = True
        elif c_status in ("awaiting delivery", "awaiting_delivery", "pending", "in progress", "active", "unfulfilled"):
            awaiting_delivery_mode = True
        elif "," in c_status:
            status_filter_set = {s.strip() for s in c_status.split(",") if s.strip()}
        else:
            status_filter_set = {c_status}

    for o in orders:
        o_status = o["status"].lower()

        if c_name and c_name not in o["customer_name"].lower():
            continue
        if c_city and c_city != o["city"].lower():
            continue
        if c_prod and c_prod not in o["product"].lower():
            continue
        if c_cat and c_cat != o["category"].lower():
            continue

        # Exclude specific statuses if requested
        if c_exclude and o_status in c_exclude:
            continue

        # Status matching modes
        if not_delivered_mode:
            if o_status == "delivered":
                continue
        elif awaiting_delivery_mode:
            if o_status not in ("processing", "shipped"):
                continue
        elif status_filter_set is not None:
            if o_status not in status_filter_set:
                continue

        if not _matches_date(o["order_date"], start_date, end_date):
            continue

        results.append(o)

    total_matches = len(results)
    safe_limit = max(1, min(limit, 100))
    truncated_results = results[:safe_limit]

    return {
        "total_matches": total_matches,
        "returned_count": len(truncated_results),
        "orders": truncated_results,
        "filters_applied": {
            "customer_name": customer_name,
            "city": city,
            "product": product,
            "category": category,
            "status": status,
            "exclude_status": exclude_status,
            "start_date": start_date,
            "end_date": end_date
        }
    }


def calculate_order_metrics(
    category: Optional[str] = None,
    city: Optional[str] = None,
    customer_name: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_n_customers: int = 5
) -> Dict[str, Any]:
    """
    Authoritative Python calculation for order counts, revenue, cancellations, and top spenders.
    Revenue Policy:
      - 'net_revenue_inr': Sum of total_inr for non-cancelled orders (delivered, shipped, processing, returned).
      - 'delivered_revenue_inr': Sum of total_inr for delivered orders only.
      - 'gross_order_value_inr': Sum of all orders including cancelled.
      - 'cancelled_amount_inr': Sum of total_inr lost to cancelled orders.
    All monetary units are in INR.
    Date boundaries are inclusive (start_date <= order_date <= end_date).
    """
    orders = get_orders()
    filtered: List[Dict[str, Any]] = []

    c_cat = category.strip().lower() if category else None
    c_city = city.strip().lower() if city else None
    c_name = customer_name.strip().lower() if customer_name else None
    c_status = status.strip().lower() if status else None

    for o in orders:
        if c_cat and c_cat != o["category"].lower():
            continue
        if c_city and c_city != o["city"].lower():
            continue
        if c_name and c_name not in o["customer_name"].lower():
            continue
        if c_status and c_status != o["status"].lower():
            continue
        if not _matches_date(o["order_date"], start_date, end_date):
            continue
        filtered.append(o)

    total_orders = len(filtered)
    status_counts: Dict[str, int] = {}
    for o in filtered:
        st = o["status"]
        status_counts[st] = status_counts.get(st, 0) + 1

    gross_order_value = sum(o["total_inr"] for o in filtered)
    
    # Revenue excluding cancellations:
    non_cancelled_orders = [o for o in filtered if o["status"] != "cancelled"]
    net_revenue = sum(o["total_inr"] for o in non_cancelled_orders)
    
    # Delivered revenue:
    delivered_orders = [o for o in filtered if o["status"] == "delivered"]
    delivered_revenue = sum(o["total_inr"] for o in delivered_orders)

    # Cancelled orders:
    cancelled_orders = [o for o in filtered if o["status"] == "cancelled"]
    cancelled_count = len(cancelled_orders)
    cancelled_amount = sum(o["total_inr"] for o in cancelled_orders)
    cancellation_rate = round((cancelled_count / total_orders * 100), 2) if total_orders > 0 else 0.0

    # Returned orders:
    returned_orders = [o for o in filtered if o["status"] == "returned"]
    returned_count = len(returned_orders)
    returned_amount = sum(o["total_inr"] for o in returned_orders)

    # Top customers by spending (based on non-cancelled orders):
    customer_spending: Dict[str, Dict[str, Any]] = {}
    for o in non_cancelled_orders:
        cname = o["customer_name"]
        if cname not in customer_spending:
            customer_spending[cname] = {"customer_name": cname, "total_spent_inr": 0.0, "order_count": 0}
        customer_spending[cname]["total_spent_inr"] += o["total_inr"]
        customer_spending[cname]["order_count"] += 1

    sorted_customers = sorted(
        customer_spending.values(),
        key=lambda x: x["total_spent_inr"],
        reverse=True
    )[:max(1, top_n_customers)]

    avg_order_value = round(net_revenue / len(non_cancelled_orders), 2) if non_cancelled_orders else 0.0

    return {
        "total_orders_count": total_orders,
        "status_breakdown": status_counts,
        "revenue_metrics": {
            "currency": "INR",
            "net_revenue_inr": round(net_revenue, 2),
            "delivered_revenue_inr": round(delivered_revenue, 2),
            "gross_order_value_inr": round(gross_order_value, 2),
            "average_order_value_inr": avg_order_value,
            "revenue_policy_explanation": "Net revenue includes all completed or active orders (delivered, shipped, processing, returned) excluding cancelled orders. Delivered revenue counts only delivered orders. Gross order value includes all orders."
        },
        "cancellation_metrics": {
            "cancelled_orders_count": cancelled_count,
            "cancelled_amount_inr": round(cancelled_amount, 2),
            "cancellation_rate_percent": cancellation_rate
        },
        "return_metrics": {
            "returned_orders_count": returned_count,
            "returned_amount_inr": round(returned_amount, 2)
        },
        "top_customers": sorted_customers,
        "filters_applied": {
            "category": category,
            "city": city,
            "customer_name": customer_name,
            "status": status,
            "start_date": start_date,
            "end_date": end_date
        }
    }


# Canonical tools registry mapping exact tool names
TOOLS_REGISTRY: Dict[str, Any] = {
    "lookup_order": lookup_order,
    "search_orders": search_orders,
    "calculate_order_metrics": calculate_order_metrics,
}

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch and execute tool call safely with validation."""
    clean_name = (tool_name or "").strip()
    if clean_name in ("lookup_order", "wrapped_lookup_order"):
        order_id = arguments.get("order_id", "")
        return lookup_order(order_id)
    elif clean_name in ("search_orders", "wrapped_search_orders"):
        return search_orders(
            customer_name=arguments.get("customer_name"),
            city=arguments.get("city"),
            product=arguments.get("product"),
            category=arguments.get("category"),
            status=arguments.get("status"),
            exclude_status=arguments.get("exclude_status"),
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            limit=arguments.get("limit", 20)
        )
    elif clean_name in ("calculate_order_metrics", "wrapped_calculate_order_metrics"):
        return calculate_order_metrics(
            category=arguments.get("category"),
            city=arguments.get("city"),
            customer_name=arguments.get("customer_name"),
            status=arguments.get("status"),
            start_date=arguments.get("start_date"),
            end_date=arguments.get("end_date"),
            top_n_customers=arguments.get("top_n_customers", 5)
        )
    else:
        return {"error": f"Unknown tool: '{tool_name}'"}
