from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from google.genai.errors import ClientError, ServerError

from backend.main import app
from backend.ai_agent import run_chat_turn, clear_response_cache

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_cache_for_tests():
    clear_response_cache()
    yield
    clear_response_cache()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dataset_loaded"] is True
    assert data["total_orders"] == 60
    assert "gemini_configured" in data
    assert "model_name" in data
    assert data["version"] == "1.0.0"

def test_chat_validation_empty_message():
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()

def test_chat_validation_missing_message():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422

def test_chat_without_api_key():
    with patch("backend.ai_agent.get_gemini_api_key", return_value=""):
        res = run_chat_turn("What is the status of ORD-1025?")
        assert "Gemini API Key is not configured" in res["reply"]
        assert len(res["tool_calls"]) == 0

def test_chat_mocked_lookup_tool_calling():
    mock_client = MagicMock()
    mock_chat = MagicMock()

    def fake_send_message(prompt):
        tools = mock_client.chats.create.call_args.kwargs["config"].tools
        lookup_fn = tools[0]
        tool_res = lookup_fn("ORD-1025")
        mock_response = MagicMock()
        mock_response.text = f"Order ORD-1025 for {tool_res['order']['customer_name']} is {tool_res['order']['status']}."
        return mock_response

    mock_chat.send_message.side_effect = fake_send_message
    mock_client.chats.create.return_value = mock_chat

    res = run_chat_turn(
        message="What is the status of order ORD-1025?",
        client=mock_client,
        model="gemini-flash-latest"
    )

    assert "ORD-1025" in res["reply"]
    assert "delivered" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "lookup_order"
    assert res["tool_calls"][0]["arguments"]["order_id"] == "ORD-1025"
    assert res["tool_calls"][0]["result"]["found"] is True

def test_chat_mocked_search_orders_tool_calling():
    mock_client = MagicMock()
    mock_chat = MagicMock()

    def fake_send_message(prompt):
        tools = mock_client.chats.create.call_args.kwargs["config"].tools
        search_fn = tools[1]
        tool_res = search_fn(city="Chennai")
        mock_response = MagicMock()
        mock_response.text = f"Found {tool_res['total_matches']} orders in Chennai."
        return mock_response

    mock_chat.send_message.side_effect = fake_send_message
    mock_client.chats.create.return_value = mock_chat

    res = run_chat_turn(
        message="List orders in Chennai",
        client=mock_client,
        model="gemini-flash-latest"
    )

    assert "Found 21 orders in Chennai" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "search_orders"
    assert res["tool_calls"][0]["result"]["total_matches"] == 21

def test_chat_mocked_metrics_tool_calling():
    mock_client = MagicMock()
    mock_chat = MagicMock()

    def fake_send_message(prompt):
        tools = mock_client.chats.create.call_args.kwargs["config"].tools
        metrics_fn = tools[2]
        tool_res = metrics_fn(category="Electronics", start_date="2026-08-01", end_date="2026-08-31")
        mock_response = MagicMock()
        mock_response.text = f"The total delivered revenue for Electronics in August was ₹{tool_res['revenue_metrics']['delivered_revenue_inr']}."
        return mock_response

    mock_chat.send_message.side_effect = fake_send_message
    mock_client.chats.create.return_value = mock_chat

    res = run_chat_turn(
        message="What was the total revenue from Electronics in August?",
        client=mock_client,
        model="gemini-flash-latest"
    )

    assert "16692" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "calculate_order_metrics"
    assert res["tool_calls"][0]["result"]["revenue_metrics"]["net_revenue_inr"] == 16692.0

def test_chat_fallback_on_404_retired_model():
    # If first model fails with 404 (retired), fallback model succeeds
    mock_client = MagicMock()
    err_404 = ClientError(404, {"error": {"code": 404, "message": "Model not available"}}, None)

    mock_chat_success = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Answer from gemini-flash-latest."
    mock_chat_success.send_message.return_value = mock_resp

    mock_client.chats.create.side_effect = [err_404, mock_chat_success]

    with patch("backend.ai_agent.get_gemini_model", return_value="gemini-2.5-flash"):
        res = run_chat_turn("Hello", client=mock_client)
        assert "gemini-flash-latest" in res["reply"]
        assert mock_client.chats.create.call_count == 2

def test_chat_provider_quota_does_not_retry_further_models():
    # When 429 quota error occurs, it must NOT repeatedly call other models
    mock_client = MagicMock()
    err_429 = ClientError(429, {"error": {"code": 429, "message": "Quota exceeded limit: 20. Please retry in 17h."}}, None)
    mock_client.chats.create.side_effect = err_429

    res = run_chat_turn("Hello", client=mock_client)
    assert "Quota Exceeded" in res["reply"]
    # Exactly one call made, no looping
    assert mock_client.chats.create.call_count == 1

def test_chat_provider_auth_failure():
    mock_client = MagicMock()
    err = ClientError(401, {"error": {"code": 401, "message": "API key invalid"}}, None)
    mock_client.chats.create.side_effect = err

    res = run_chat_turn("Hello", client=mock_client)
    assert "Authentication Failed" in res["reply"]
    assert mock_client.chats.create.call_count == 1

def test_chat_provider_service_unavailable_retry():
    # When first model has 503 high demand spike, next fallback model is tried
    mock_client = MagicMock()
    err_503 = ServerError(503, {"error": {"code": 503, "message": "high demand"}}, None)

    mock_chat_success = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Recovered from demand spike."
    mock_chat_success.send_message.return_value = mock_resp

    mock_client.chats.create.side_effect = [err_503, mock_chat_success]

    res = run_chat_turn("Hello", client=mock_client)
    assert "Recovered from demand spike" in res["reply"]
    assert mock_client.chats.create.call_count == 2

def test_tool_names_registered_identically_to_definitions():
    # Verify tools registered in GenerateContentConfig match exact schema names
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "OK"
    mock_chat.send_message.return_value = mock_resp
    mock_client.chats.create.return_value = mock_chat

    run_chat_turn("Hello", client=mock_client, model="gemini-flash-latest")
    tools = mock_client.chats.create.call_args.kwargs["config"].tools
    tool_names = [t.__name__ for t in tools]

    assert tool_names == ["lookup_order", "search_orders", "calculate_order_metrics"]
    assert "wrapped_search_orders" not in tool_names
    assert "wrapped_lookup_order" not in tool_names

def test_chat_customers_not_received_orders_regression():
    # Regression test for: "Which customers haven't received their orders yet?"
    # Prevents AI Assistant Error: 'search_orders'
    mock_client = MagicMock()
    mock_chat = MagicMock()

    def fake_send_message(prompt):
        tools = mock_client.chats.create.call_args.kwargs["config"].tools
        # Directly invoke the search_orders tool registered at index 1
        search_fn = tools[1]
        assert search_fn.__name__ == "search_orders"
        tool_res = search_fn(status="awaiting delivery")
        
        # Build answer using real CSV data returned by tool
        lines = []
        for o in tool_res["orders"]:
            lines.append(f"- {o['customer_name']} (Order {o['order_id']}, status: {o['status']})")
        orders_summary = "\n".join(lines)
        
        mock_response = MagicMock()
        mock_response.text = (
            f"The following customers have active orders awaiting delivery:\n{orders_summary}\n\n"
            "Additionally, 7 orders were cancelled and 3 were returned."
        )
        return mock_response

    mock_chat.send_message.side_effect = fake_send_message
    mock_client.chats.create.return_value = mock_chat

    res = run_chat_turn(
        message="Which customers haven't received their orders yet?",
        client=mock_client,
        model="gemini-flash-latest"
    )

    assert "Karthik Rao" in res["reply"]
    assert "Rahul Sharma" in res["reply"]
    assert "ORD-1059" in res["reply"]
    assert "ORD-1060" in res["reply"]
    assert "cancelled" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "search_orders"
    assert res["tool_calls"][0]["result"]["total_matches"] == 2

def test_chat_provider_quota_offline_fallback_order_lookup():
    # When 429 quota error occurs, deterministic order lookup is handled by local Python tool
    mock_client = MagicMock()
    err_429 = ClientError(429, {"error": {"code": 429, "message": "Resource exhausted"}}, None)
    mock_client.chats.create.side_effect = err_429

    res = run_chat_turn("Where is order ORD-1025?", client=mock_client)
    assert "ORD-1025" in res["reply"]
    assert "Karthik Rao" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "lookup_order"
    assert res["tool_calls"][0]["result"]["found"] is True
    # Verify mock_client chats.create was called only once and did not loop
    assert mock_client.chats.create.call_count == 1

def test_chat_provider_quota_offline_fallback_cancellations():
    # When 429 occurs, cancellation queries are resolved via calculate_order_metrics offline
    mock_client = MagicMock()
    err_429 = ClientError(429, {"error": {"code": 429, "message": "Resource exhausted"}}, None)
    mock_client.chats.create.side_effect = err_429

    res = run_chat_turn("How many orders were cancelled?", client=mock_client)
    assert "Cancellation Summary" in res["reply"]
    assert "7" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "calculate_order_metrics"
    assert res["tool_calls"][0]["result"]["cancellation_metrics"]["cancelled_orders_count"] == 7
    assert mock_client.chats.create.call_count == 1

def test_chat_provider_quota_offline_fallback_unreceived_orders():
    # When 429 occurs, undelivered queries are resolved via search_orders offline
    mock_client = MagicMock()
    err_429 = ClientError(429, {"error": {"code": 429, "message": "Resource exhausted"}}, None)
    mock_client.chats.create.side_effect = err_429

    res = run_chat_turn("Which customers haven't received their orders yet?", client=mock_client)
    assert "Karthik Rao" in res["reply"]
    assert "Rahul Sharma" in res["reply"]
    assert "ORD-1059" in res["reply"]
    assert "ORD-1060" in res["reply"]
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool_name"] == "search_orders"
    assert res["tool_calls"][0]["result"]["total_matches"] == 2
    assert mock_client.chats.create.call_count == 1

def test_chat_automatic_function_calling_limits_remote_calls():
    # Verify that types.GenerateContentConfig sets maximum_remote_calls=2 to limit tool-calling iterations
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "All set."
    mock_chat.send_message.return_value = mock_resp
    mock_client.chats.create.return_value = mock_chat

    run_chat_turn("Check orders", client=mock_client, model="gemini-flash-latest")
    config = mock_client.chats.create.call_args.kwargs["config"]
    assert config.automatic_function_calling is not None
    assert config.automatic_function_calling.maximum_remote_calls == 2

def test_chat_duplicate_query_caching():
    # Verify in-memory caching prevents duplicate model calls for identical questions
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Cached order insight answer."
    mock_chat.send_message.return_value = mock_resp
    mock_client.chats.create.return_value = mock_chat

    # First turn calls the API
    res1 = run_chat_turn("What products sell best?", client=mock_client)
    assert res1["reply"] == "Cached order insight answer."
    assert mock_client.chats.create.call_count == 1

    # Second turn for the identical query uses the cache without creating another chat or sending a request
    res2 = run_chat_turn("What products sell best?", client=mock_client)
    assert res2["reply"] == "Cached order insight answer."
    assert mock_client.chats.create.call_count == 1

