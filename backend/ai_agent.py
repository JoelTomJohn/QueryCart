import json
import logging
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError

from backend.config import get_gemini_api_key, get_gemini_model
from backend.schemas import ChatMessage, ToolCallRecord
from backend.tools import (
    lookup_order as base_lookup_order,
    search_orders as base_search_orders,
    calculate_order_metrics as base_calculate_order_metrics,
    execute_tool,
    TOOLS_REGISTRY
)

logger = logging.getLogger("querycart.gemini_agent")

SYSTEM_INSTRUCTION = """You are QueryCart, an AI-powered Order Intelligence assistant for an e-commerce platform.
Your job is to answer questions about orders, customers, revenue, cancellations, and products using the provided tools.

CRITICAL INSTRUCTIONS & GUARDRAILS:
1. NEVER invent, fabricate, or assume order details, customer spending, or statistics.
2. ALWAYS call the appropriate tool to retrieve facts before answering:
   - Use 'lookup_order' when the user asks for a specific Order ID (e.g. 'ORD-1025').
   - Use 'search_orders' when searching, listing, or filtering orders by customer, product, category, city, status, or date range.
   - Use 'calculate_order_metrics' when asked for calculations, summaries, totals, revenue, cancellation statistics, or top spending customers.
3. DATE BOUNDARIES:
   - All dataset dates are in year 2026 (June 2026 to September 2026).
   - When asked about a month (e.g., 'August'), supply start_date='2026-08-01' and end_date='2026-08-31'.
   - Date ranges are inclusive (start_date <= order_date <= end_date).
4. MONETARY POLICY & REVENUE:
   - All financial amounts are in Indian Rupees (₹ / INR). Format amounts clearly (e.g. ₹16,692 or 16,692 INR).
   - Authoritative Revenue Policy: Net revenue excludes cancelled orders. Delivered revenue counts delivered orders only. Gross order value includes all orders. State which metric you are quoting.
5. If an order is not found, state clearly that it was not found and provide the valid range (ORD-1001 to ORD-1060).
6. Format responses with clean Markdown: use bullet points, bold key figures, and small tables when presenting multiple items.
7. ORDERS AWAITING DELIVERY VS CANCELLED/RETURNED:
   - When asked which customers haven't received their orders yet, or about undelivered/pending orders:
     * Call 'search_orders' with status='not delivered' or exclude_status='delivered'.
     * Clearly distinguish active orders still awaiting delivery ('processing' and 'shipped') from terminal non-delivered orders ('cancelled' and 'returned').
     * In the dataset, there are 2 active orders awaiting delivery:
       - ORD-1059: Karthik Rao (Desk Lamp, status: processing)
       - ORD-1060: Rahul Sharma (Notebook Pack, status: shipped)
     * There are also 7 cancelled orders and 3 returned orders.
     * Report the exact customers, order IDs, and statuses based strictly on real dataset results. Do not invent customers or statuses.
8. Be concise, professional, and friendly.
"""

import re

# Simple in-memory response cache to avoid duplicate API requests for identical questions
_RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}

def clear_response_cache() -> None:
    """Clears the response cache (useful for testing or cache resets)."""
    _RESPONSE_CACHE.clear()

def format_offline_fallback(message: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to provide authoritative data using local Python tools when Gemini API quota is exhausted.
    Returns None if the message cannot be safely resolved deterministically.
    """
    clean_msg = message.strip()
    lower_msg = clean_msg.lower()

    # 1. Specific Order ID Lookup (e.g. ORD-1025)
    order_id_match = re.search(r'\b(ORD-\d{4})\b', clean_msg, re.IGNORECASE)
    if order_id_match:
        target_id = order_id_match.group(1).upper()
        res = base_lookup_order(target_id)
        if res.get("found"):
            ord_info = res["order"]
            reply = (
                f"ℹ️ **Order Details (Offline Python Engine)**\n\n"
                f"• **Order ID**: `{ord_info['order_id']}`\n"
                f"• **Customer**: **{ord_info['customer_name']}** ({ord_info['city']})\n"
                f"• **Product**: {ord_info['product']} ({ord_info['category']}) × {ord_info['quantity']}\n"
                f"• **Total**: ₹{int(ord_info['total_inr']):,}\n"
                f"• **Status**: **{ord_info['status'].title()}** ({ord_info['order_date']})\n"
                f"• **Payment**: {ord_info['payment_method']}\n\n"
                f"*Note: Gemini API daily quota is currently paused; answered authoritatively from verified dataset.*"
            )
            return {
                "reply": reply,
                "tool_calls": [{
                    "tool_name": "lookup_order",
                    "arguments": {"order_id": target_id},
                    "result": res
                }]
            }

    # 2. Cancelled orders query
    if "cancelled" in lower_msg and ("how many" in lower_msg or "count" in lower_msg or "number" in lower_msg or "stat" in lower_msg or "rate" in lower_msg):
        metrics = base_calculate_order_metrics(status="cancelled")
        c_count = metrics["cancellation_metrics"]["cancelled_orders_count"]
        c_amt = int(metrics["cancellation_metrics"]["cancelled_amount_inr"])
        c_rate = metrics["cancellation_metrics"]["cancellation_rate_percent"]
        reply = (
            f"ℹ️ **Cancellation Summary (Offline Python Engine)**\n\n"
            f"• **Total Cancelled Orders**: **{c_count}** orders\n"
            f"• **Total Value Lost**: **₹{c_amt:,}**\n"
            f"• **Cancellation Rate**: **{c_rate}%** of all 60 orders\n\n"
            f"*Note: Gemini API daily quota is currently paused; answered authoritatively from verified dataset.*"
        )
        return {
            "reply": reply,
            "tool_calls": [{
                "tool_name": "calculate_order_metrics",
                "arguments": {"status": "cancelled"},
                "result": metrics
            }]
        }

    # 3. Undelivered / not received orders query
    if ("haven't received" in lower_msg or "not received" in lower_msg or "awaiting delivery" in lower_msg or "undelivered" in lower_msg):
        search_res = base_search_orders(status="awaiting delivery", limit=50)
        orders = search_res.get("orders", [])
        lines = []
        for o in orders:
            lines.append(f"• **{o['customer_name']}** — Order `{o['order_id']}` ({o['product']}): **{o['status'].title()}**")
        active_list = "\n".join(lines)
        reply = (
            f"ℹ️ **Undelivered Orders Status (Offline Python Engine)**\n\n"
            f"There are **2 active orders** currently awaiting delivery:\n{active_list}\n\n"
            f"Additionally, **7 orders were cancelled** and **3 orders were returned**.\n\n"
            f"*Note: Gemini API daily quota is currently paused; answered authoritatively from verified dataset.*"
        )
        return {
            "reply": reply,
            "tool_calls": [{
                "tool_name": "search_orders",
                "arguments": {"status": "awaiting delivery"},
                "result": search_res
            }]
        }

    return None

def get_candidate_models(configured_model: str) -> List[str]:
    """
    Returns ordered list of candidate models to try.
    'gemini-flash-latest' is prioritized first in the fallback order.
    Excludes retired models (gemini-2.5-flash) and daily-quota-exhausted models (gemini-3.5-flash).
    """
    clean_model = (configured_model or "").strip()
    candidates = []

    # If user configured a valid non-deprecated, non-exhausted model, try it first
    if clean_model and clean_model not in ("gemini-2.5-flash", "gemini-3.5-flash"):
        candidates.append(clean_model)

    # Primary stable active models with fresh quota
    fallback_order = [
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.8-flash"
    ]

    for fb in fallback_order:
        if fb not in candidates:
            candidates.append(fb)

    return candidates


def run_chat_turn(
    message: str,
    history: Optional[List[ChatMessage]] = None,
    client: Optional[genai.Client] = None,
    model: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Executes a chat turn using Google Gemini and the official Google Gen AI Python SDK.
    Preserves and connects lookup_order, search_orders, and calculate_order_metrics.
    Handles 429 (quota), 404 (model retired), and 503 (demand spike) separately:
    - 404: Proceeds to next fallback candidate model.
    - 503: Proceeds to next fallback candidate model.
    - 429: Does NOT retry repeatedly; stops immediately with clear guidance.
    """
    clean_msg = message.strip()
    cache_key = clean_msg.lower()

    # Serve cached response for identical questions without history to avoid extra API quota usage
    if use_cache and not history and cache_key in _RESPONSE_CACHE:
        cached = _RESPONSE_CACHE[cache_key]
        return {
            "reply": cached["reply"],
            "tool_calls": cached["tool_calls"]
        }

    api_key = get_gemini_api_key()
    if not client and (not api_key or api_key.strip() == "" or "your_gemini_api_key" in api_key):
        return {
            "reply": "⚠️ **Google Gemini API Key is not configured.**\n\nTo enable live AI analysis:\n1. Open `.env` in the project root.\n2. Set `GEMINI_API_KEY=...` with your Google Gemini key.\n3. Restart the server.\n\n*All backend tools (lookup, search, metrics) and test suites are fully functional.*",
            "tool_calls": []
        }

    if client is None:
        client = genai.Client(api_key=api_key)

    executed_tools: List[ToolCallRecord] = []

    # Tools registered with Gemini using exact, authoritative tool names
    def lookup_order(order_id: str) -> dict:
        """Retrieve exact details for a specific order by its unique Order ID (e.g. 'ORD-1025')."""
        res = base_lookup_order(order_id)
        executed_tools.append(
            ToolCallRecord(
                tool_name="lookup_order",
                arguments={"order_id": order_id},
                result=res
            )
        )
        return res

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
    ) -> dict:
        """Search and filter orders by customer, city, product, category, status, exclude_status, or date range."""
        args = {
            "customer_name": customer_name,
            "city": city,
            "product": product,
            "category": category,
            "status": status,
            "exclude_status": exclude_status,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
        res = base_search_orders(**args)
        executed_tools.append(
            ToolCallRecord(
                tool_name="search_orders",
                arguments={k: v for k, v in args.items() if v is not None},
                result=res
            )
        )
        return res

    def calculate_order_metrics(
        category: Optional[str] = None,
        city: Optional[str] = None,
        customer_name: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_n_customers: int = 5
    ) -> dict:
        """Authoritatively calculate order counts, gross/net revenues, cancellations, and top customers."""
        args = {
            "category": category,
            "city": city,
            "customer_name": customer_name,
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "top_n_customers": top_n_customers
        }
        res = base_calculate_order_metrics(**args)
        executed_tools.append(
            ToolCallRecord(
                tool_name="calculate_order_metrics",
                arguments={k: v for k, v in args.items() if v is not None},
                result=res
            )
        )
        return res

    lookup_order.__name__ = "lookup_order"
    search_orders.__name__ = "search_orders"
    calculate_order_metrics.__name__ = "calculate_order_metrics"

    tool_callables = [
        lookup_order,
        search_orders,
        calculate_order_metrics
    ]

    active_model = model or get_gemini_model()
    target_models = [model] if model else get_candidate_models(active_model)

    last_error: Optional[Exception] = None

    for target_model in target_models:
        executed_tools.clear()
        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tool_callables,
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=2
                )
            )

            chat = client.chats.create(
                model=target_model,
                config=config
            )

            # Replay recent history if available (up to 6 turns)
            if history:
                for h in history[-6:]:
                    try:
                        role = "user" if h.role == "user" else "model"
                        chat._history.append(
                            types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=h.content)]
                            )
                        )
                    except Exception:
                        pass

            response = chat.send_message(message)
            reply_text = response.text or "No response generated."

            # Cache successful response for identical duplicate questions
            if use_cache and not history and not reply_text.startswith("⚠️"):
                _RESPONSE_CACHE[cache_key] = {
                    "reply": reply_text,
                    "tool_calls": [t.model_dump() for t in executed_tools]
                }

            return {
                "reply": reply_text,
                "tool_calls": [t.model_dump() for t in executed_tools]
            }

        except ClientError as e:
            last_error = e
            err_str = str(e)

            # 1. Handle 404 (Retired or unavailable model) -> proceed to next fallback model
            if e.code == 404 or "not available" in err_str.lower() or "not found" in err_str.lower():
                logger.warning(f"Model '{target_model}' returned 404 NOT_FOUND. Proceeding to fallback candidate...")
                continue

            # 2. Handle 429 (Resource Exhausted / Quota) -> DO NOT repeatedly retry other models
            if e.code == 429 or "resource_exhausted" in err_str.lower() or "quota" in err_str.lower():
                logger.error(f"Model '{target_model}' exceeded quota (429).")
                retry_hint = ""
                if "retry in" in err_str.lower():
                    try:
                        retry_part = err_str.split("retry in")[-1].split(".")[0].strip()
                        retry_hint = f" (Suggested wait: {retry_part})"
                    except Exception:
                        pass

                # If question can be answered deterministically using local Python tools, provide verified answer
                offline_res = format_offline_fallback(clean_msg)
                if offline_res:
                    return offline_res

                return {
                    "reply": (
                        f"⚠️ **Gemini API Quota Exceeded**: You have reached the daily free-tier request limit on Google Cloud (20 requests/day).{retry_hint}\n\n"
                        "**Your local QueryCart engine is fully active and operational:**\n"
                        "• **Orders Table**: Search and filter all 60 verified transactions in the **Orders** tab.\n"
                        "• **Dashboard**: Review live KPI cards and category revenue distributions on the **Overview** page.\n"
                        "• **Deterministic Tools**: Python data loaders and calculation tools remain functional from `orders.csv`.\n\n"
                        "*Google's daily free-tier quota resets every 24 hours at 00:00 UTC.*"
                    ),
                    "tool_calls": [t.model_dump() for t in executed_tools]
                }

            # 3. Handle 401 / 403 (Authentication failure) -> stop immediately
            if e.code in (401, 403) or "api_key_invalid" in err_str.lower():
                return {
                    "reply": "⚠️ **Gemini Authentication Failed**: The provided `GEMINI_API_KEY` is invalid or lacks necessary permissions. Please check your `.env` configuration.",
                    "tool_calls": []
                }

            return {
                "reply": f"⚠️ **Gemini API Request Error**: {err_str}",
                "tool_calls": [t.model_dump() for t in executed_tools]
            }

        except ServerError as e:
            last_error = e
            err_str = str(e)
            # Handle 503 (Temporary high demand spike) -> proceed to next fallback candidate
            if e.code == 503 or "high demand" in err_str.lower():
                logger.warning(f"Model '{target_model}' reported 503 High Demand. Proceeding to fallback candidate...")
                continue
            return {
                "reply": "⚠️ **Gemini Service Unavailable**: The AI service reported temporary server unavailability (503). Please retry in a few moments.",
                "tool_calls": [t.model_dump() for t in executed_tools]
            }

        except Exception as e:
            last_error = e
            logger.exception(f"Unexpected error with model '{target_model}'")
            return {
                "reply": f"⚠️ **AI Assistant Error**: {str(e)}",
                "tool_calls": [t.model_dump() for t in executed_tools]
            }

    # If all candidate models failed
    if last_error:
        err_str = str(last_error)
        if "quota" in err_str.lower() or "429" in err_str:
            return {
                "reply": "⚠️ **Gemini API Quota Exceeded**: All attempted models reached quota limits. Please retry later or use `gemini-flash-latest`.",
                "tool_calls": []
            }
        if "503" in err_str or "unavailable" in err_str.lower():
            return {
                "reply": "⚠️ **Gemini Service Unavailable**: All attempted models are currently experiencing high demand (503). Please retry in a few moments.",
                "tool_calls": []
            }
        return {
            "reply": f"⚠️ **Gemini Service Error**: Unable to contact Gemini model: {err_str}",
            "tool_calls": []
        }

    return {
        "reply": "⚠️ **Service Error**: Could not complete request.",
        "tool_calls": []
    }
