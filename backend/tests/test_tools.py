import pytest
from backend.tools import lookup_order, search_orders, calculate_order_metrics, execute_tool
from backend.data_loader import load_orders

def test_lookup_order_success():
    res = lookup_order("ORD-1025")
    assert res["found"] is True
    assert res["order"]["order_id"] == "ORD-1025"
    assert res["order"]["customer_name"] == "Karthik Rao"
    assert res["order"]["status"] == "delivered"
    assert res["order"]["total_inr"] == 2397.0

def test_lookup_order_case_insensitive():
    res = lookup_order("ord-1001")
    assert res["found"] is True
    assert res["order"]["order_id"] == "ORD-1001"
    assert res["order"]["customer_name"] == "Rahul Sharma"

def test_lookup_order_not_found():
    res = lookup_order("ORD-9999")
    assert res["found"] is False
    assert "not found" in res["message"].lower()

def test_lookup_order_invalid_inputs():
    res = lookup_order("")
    assert res["found"] is False
    assert "valid order_id" in res["error"].lower()

def test_search_orders_by_city():
    res = search_orders(city="Chennai")
    assert res["total_matches"] == 21
    assert all(o["city"] == "Chennai" for o in res["orders"])

def test_search_orders_by_category():
    res = search_orders(category="Electronics")
    assert res["total_matches"] == 21
    assert all(o["category"] == "Electronics" for o in res["orders"])

def test_search_orders_by_status_cancelled():
    res = search_orders(status="cancelled")
    assert res["total_matches"] == 7
    assert all(o["status"] == "cancelled" for o in res["orders"])

def test_search_orders_by_date_range():
    # August 2026: 2026-08-01 to 2026-08-31
    res = search_orders(start_date="2026-08-01", end_date="2026-08-31", limit=100)
    assert res["total_matches"] > 0
    for o in res["orders"]:
        assert "2026-08-01" <= o["order_date"] <= "2026-08-31"

def test_search_orders_multiple_filters():
    # Category Electronics in August
    res = search_orders(category="Electronics", start_date="2026-08-01", end_date="2026-08-31")
    assert res["total_matches"] == 4
    for o in res["orders"]:
        assert o["category"] == "Electronics"
        assert "2026-08-01" <= o["order_date"] <= "2026-08-31"

def test_search_orders_no_matches():
    res = search_orders(customer_name="NonExistentPerson123")
    assert res["total_matches"] == 0
    assert len(res["orders"]) == 0

def test_calculate_order_metrics_overall():
    metrics = calculate_order_metrics()
    assert metrics["total_orders_count"] == 60
    assert metrics["cancellation_metrics"]["cancelled_orders_count"] == 7
    assert metrics["cancellation_metrics"]["cancellation_rate_percent"] == round(7 / 60 * 100, 2)
    assert metrics["status_breakdown"]["delivered"] == 48
    assert metrics["status_breakdown"]["cancelled"] == 7
    assert metrics["status_breakdown"]["returned"] == 3
    assert metrics["status_breakdown"]["processing"] == 1
    assert metrics["status_breakdown"]["shipped"] == 1
    
    # Top customer should be Rohan Das
    top_customer = metrics["top_customers"][0]
    assert top_customer["customer_name"] == "Rohan Das"
    assert top_customer["total_spent_inr"] == 112282.0

def test_calculate_order_metrics_august_electronics():
    metrics = calculate_order_metrics(
        category="Electronics",
        start_date="2026-08-01",
        end_date="2026-08-31"
    )
    assert metrics["total_orders_count"] == 4
    assert metrics["cancellation_metrics"]["cancelled_orders_count"] == 1
    # 3 delivered orders: 3798 + 10497 + 2397 = 16692
    assert metrics["revenue_metrics"]["net_revenue_inr"] == 16692.0
    assert metrics["revenue_metrics"]["delivered_revenue_inr"] == 16692.0
    # 1 cancelled order: 10497
    assert metrics["cancellation_metrics"]["cancelled_amount_inr"] == 10497.0
    # gross order value = 16692 + 10497 = 27189
    assert metrics["revenue_metrics"]["gross_order_value_inr"] == 27189.0

def test_execute_tool_dispatch():
    res = execute_tool("lookup_order", {"order_id": "ORD-1002"})
    assert res["found"] is True
    assert res["order"]["order_id"] == "ORD-1002"

    res_search = execute_tool("search_orders", {"status": "not delivered", "limit": 50})
    assert res_search["total_matches"] == 12

    res_unknown = execute_tool("invalid_tool", {})
    assert "Unknown tool" in res_unknown["error"]

def test_search_orders_non_delivered():
    # In dataset: 60 total, 48 delivered -> 12 non-delivered (7 cancelled, 3 returned, 1 processing, 1 shipped)
    res = search_orders(status="not delivered", limit=100)
    assert res["total_matches"] == 12
    statuses = {o["status"] for o in res["orders"]}
    assert "delivered" not in statuses
    assert "cancelled" in statuses
    assert "returned" in statuses
    assert "processing" in statuses
    assert "shipped" in statuses

def test_search_orders_exclude_status_delivered():
    res = search_orders(exclude_status="delivered", limit=100)
    assert res["total_matches"] == 12
    statuses = {o["status"] for o in res["orders"]}
    assert "delivered" not in statuses

def test_search_orders_awaiting_delivery():
    # Only active unfulfilled orders (processing and shipped)
    res = search_orders(status="awaiting delivery", limit=100)
    assert res["total_matches"] == 2
    order_ids = {o["order_id"] for o in res["orders"]}
    assert "ORD-1059" in order_ids  # Karthik Rao, processing
    assert "ORD-1060" in order_ids  # Rahul Sharma, shipped
    customers = {o["customer_name"] for o in res["orders"]}
    assert "Karthik Rao" in customers
    assert "Rahul Sharma" in customers

def test_isolated_fixture_dataset(tmp_path):
    # Test with custom temporary CSV to verify isolation
    csv_file = tmp_path / "test_orders.csv"
    csv_file.write_text(
        "order_id,order_date,customer_name,city,product,category,quantity,unit_price_inr,total_inr,payment_method,status\n"
        "ORD-9001,2026-01-01,Test User,Mumbai,Item A,Electronics,1,100,100,UPI,delivered\n"
        "ORD-9002,2026-01-02,Test User,Mumbai,Item B,Electronics,2,200,400,UPI,cancelled\n",
        encoding="utf-8"
    )
    loaded = load_orders(csv_path=str(csv_file), force_reload=True)
    assert len(loaded) == 2
    assert loaded[0]["order_id"] == "ORD-9001"
    assert loaded[1]["status"] == "cancelled"

    # Reload original dataset so subsequent tests use original
    load_orders(force_reload=True)
