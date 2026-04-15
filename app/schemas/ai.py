"""
Pydantic Schemas for AI Assistant
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AIQueryRequest(BaseModel):
    query: str

    model_config = {"json_schema_extra": {
        "example": {"query": "Show all high priority open tickets"}
    }}


class AIQueryResponse(BaseModel):
    query: str
    answer: str
    data: Optional[Any] = None
    query_type: Optional[str] = None
