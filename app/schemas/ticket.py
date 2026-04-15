"""
Pydantic Schemas for Ticket - Request/Response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from app.models.ticket import TicketStatus, TicketPriority
from app.schemas.user import UserResponse


class TicketCreateRequest(BaseModel):
    title: str
    description: str
    priority: Optional[TicketPriority] = TicketPriority.medium
    category: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty.")
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters.")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Description cannot be empty.")
        return v

    model_config = {"json_schema_extra": {
        "example": {
            "title": "Login page broken",
            "description": "Users cannot login after last deployment.",
            "priority": "high",
            "category": "bug"
        }
    }}


class TicketUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    category: Optional[str] = None
    assigned_to: Optional[int] = None

    model_config = {"json_schema_extra": {
        "example": {
            "title": "Updated title",
            "priority": "low"
        }
    }}


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatus

    model_config = {"json_schema_extra": {
        "example": {"status": "in_progress"}
    }}


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: Optional[str]
    created_by: int
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None

    model_config = {"from_attributes": True}


class PaginatedTicketsResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    closed_tickets: int
    high_priority_tickets: int
    medium_priority_tickets: int
    low_priority_tickets: int
    total_users: int
