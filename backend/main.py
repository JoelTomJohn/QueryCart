import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import get_gemini_api_key, get_gemini_model, ORDERS_CSV_PATH, ENVIRONMENT
from backend.schemas import ChatRequest, ChatResponse, HealthResponse
from backend.data_loader import get_orders
from backend.tools import calculate_order_metrics
from backend.ai_agent import run_chat_turn

app = FastAPI(
    title="QueryCart API",
    description="Every Order Made Easy. - AI-Powered Order Intelligence",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint confirming data loading and service configuration."""
    orders_loaded = False
    order_count = 0
    try:
        orders = get_orders()
        orders_loaded = True
        order_count = len(orders)
    except Exception:
        orders_loaded = False

    api_key = get_gemini_api_key()
    model = get_gemini_model()
    gemini_ready = bool(api_key and api_key.strip() and "your_gemini_api_key" not in api_key)

    return HealthResponse(
        status="healthy" if orders_loaded else "degraded",
        dataset_loaded=orders_loaded,
        total_orders=order_count,
        gemini_configured=gemini_ready,
        model_name=model,
        openai_configured=gemini_ready,
        version="1.0.0"
    )

@app.get("/api/dashboard")
def get_dashboard_data():
    """Returns authoritative KPIs, category breakdown, and recent orders from the dataset."""
    try:
        orders = get_orders()
        metrics = calculate_order_metrics()

        category_stats = {}
        for o in orders:
            cat = o["category"]
            if cat not in category_stats:
                category_stats[cat] = {"category": cat, "orders": 0, "sales_inr": 0.0}
            category_stats[cat]["orders"] += 1
            if o["status"] != "cancelled":
                category_stats[cat]["sales_inr"] += o["total_inr"]

        category_list = sorted(category_stats.values(), key=lambda x: x["sales_inr"], reverse=True)
        sorted_orders = sorted(orders, key=lambda x: x["order_date"], reverse=True)

        return {
            "metrics": {
                "total_orders": metrics["total_orders_count"],
                "net_sales_inr": metrics["revenue_metrics"]["net_revenue_inr"],
                "delivered_sales_inr": metrics["revenue_metrics"]["delivered_revenue_inr"],
                "gross_sales_inr": metrics["revenue_metrics"]["gross_order_value_inr"],
                "delivered_orders": metrics["status_breakdown"].get("delivered", 0),
                "cancelled_orders": metrics["cancellation_metrics"]["cancelled_orders_count"],
                "cancelled_amount_inr": metrics["cancellation_metrics"]["cancelled_amount_inr"],
                "cancellation_rate_percent": metrics["cancellation_metrics"]["cancellation_rate_percent"],
                "returned_orders": metrics["status_breakdown"].get("returned", 0),
                "processing_orders": metrics["status_breakdown"].get("processing", 0),
                "shipped_orders": metrics["status_breakdown"].get("shipped", 0),
                "status_breakdown": metrics["status_breakdown"],
            },
            "category_sales": category_list,
            "recent_orders": sorted_orders[:15],
            "all_orders": sorted_orders,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard data: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    Main chat endpoint: validates message, runs AI agent loop with tool calls,
    and returns assistant reply with tool execution metadata.
    """
    clean_message = payload.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty or whitespace."
        )

    try:
        result = run_chat_turn(
            message=clean_message,
            history=payload.history
        )
        return ChatResponse(
            reply=result.get("reply", "No response"),
            tool_calls=result.get("tool_calls", [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

# Optional: Mount frontend build in production if available
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API or health routes
        if full_path.startswith("api") or full_path.startswith("health") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
