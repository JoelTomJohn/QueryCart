from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., description="The message content")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's query or prompt")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Previous messages in this session")

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Any

class ChatResponse(BaseModel):
    reply: str
    tool_calls: Optional[List[ToolCallRecord]] = Field(default_factory=list)

class HealthResponse(BaseModel):
    status: str
    dataset_loaded: bool
    total_orders: int
    gemini_configured: bool
    model_name: str
    version: str
    openai_configured: Optional[bool] = None
