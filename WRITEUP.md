# QueryCart — Engineering Writeup

## 1. System Architecture
QueryCart is built as an end-to-end, deterministic Order Intelligence platform combining modern conversational AI with authoritative data processing. The system consists of:
- **Frontend Presentation Layer**: Built with React 18 and Vite, featuring a responsive SaaS interface with dark navy styling (`#0B1120`), restrained indigo and cyan accents, real-time message streaming feedback, tool execution badges, and session history management.
- **Backend Application Layer**: FastAPI ASGI service exposing `/health` and `/api/chat` with strict CORS and input validation, mounting the compiled React production client for single-port unified serving.
- **Authoritative Data Layer**: Direct in-memory parsing and cached querying over `orders.csv` using strict Python typing and mathematical aggregations, ensuring zero synthetic or hallucinated numbers.

## 2. Tool-Selection Flow
Rather than letting the LLM generate unverified responses or calculate metrics using token probability, QueryCart utilizes **Google Gemini native function/tool calling** via the official Google Gen AI Python SDK (`google-genai`):
1. **User Inquiry**: The user asks an analytical or lookup query (e.g., *"What was the total revenue from Electronics in August?"* or *"What is the status of order ORD-1025?"*).
2. **Intent & Argument Resolution**: The Gemini model selects the target tool (`lookup_order`, `search_orders`, or `calculate_order_metrics`) and extracts structured arguments (e.g., `category="Electronics"`, `start_date="2026-08-01"`, `end_date="2026-08-31"`).
3. **Deterministic Backend Execution**: The FastAPI runtime executes the corresponding Python function against the real dataset, recording execution details for the UI.
4. **Context Injection & Synthesis**: The Python result dictionary is returned to Gemini. The model synthesizes a concise, formatted explanation citing exact figures and INR currency.
5. **Loop Termination**: The Google Gen AI chat session ensures bounded execution cycles and handles multi-turn context.

## 3. Guardrails & Authoritative Calculation Assumptions
- **Zero Fabrication**: Prompts and system policies strictly prohibit generating fake statistics or making ungrounded assumptions.
- **Python-Enforced Business Logic**: All monetary sums, cancellation percentages, and rankings are calculated strictly in Python, not LLM token prediction.
- **Explicit Revenue Policy**: 
  - *Net Revenue*: Sum of all non-cancelled orders (delivered, shipped, processing, returned).
  - *Delivered Revenue*: Sum of orders strictly in `delivered` status.
  - *Gross Order Value*: Sum of all orders including cancelled items.
- **Date Boundaries**: Inclusive boundaries (`start_date <= order_date <= end_date`) with ISO 8601 `YYYY-MM-DD` formatting over the 2026 dataset timeframe.
- **Monetary Unit**: Consistent INR (`₹`) formatting across backend calculations and frontend presentation.
- **Provider Resilience**: Graceful error degradation for missing API keys, invalid credentials (401/403), rate/quota limits (`429 Resource Exhausted`), and temporary server unavailability (`503 Service Unavailable`). Automatic fallback across active candidate models ensures continuity if a specific model experiences demand spikes.

## 4. Deployment Approach
QueryCart utilizes a **unified fullstack service pattern** on Render configured via `render.yaml`:
- **Build Phase**: Installs Python requirements, installs Node modules, and compiles the React application into static assets (`frontend/dist`).
- **Runtime Phase**: Uvicorn runs FastAPI on `$PORT`. FastAPI hosts the API endpoints and serves the compiled Single-Page Application (SPA) with static fallback routing.
- This pattern eliminates cross-origin latency, CORS preflight overhead, and dual-server orchestration costs on free/starter tiers.

## 5. Future Improvements
- **Excel File Upload**: Allow users to upload Excel (`.xlsx`) or CSV files directly through the dashboard, enabling QueryCart to analyze their own order data instead of relying only on the existing dataset.
- **Database Persistence**: Transition the static CSV into PostgreSQL with SQLAlchemy/Tortoise-ORM for multi-tenant streaming order updates and indexing.
- **Dynamic Visualization**: Add automatic charting (e.g., Recharts) rendered dynamically based on tool metrics outputs.
- **Semantic Product Search**: Incorporate vector embeddings (pgvector) to support natural language queries for vague product descriptions.
- **Role-Based Access Control**: Multi-user permissions restricting access to customer PII.

## 6. AI Tools Used
During the development of QueryCart, Google Antigravity IDE and Gemini agents were utilized for automated repository analysis, dataset integrity verification, test suite generation across pytest and Vitest, and responsive interface styling.
