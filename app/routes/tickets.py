"""
Ticket Routes
All routes require JWT authentication.
Users can only access their own tickets.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.schemas.ticket import (
    TicketCreateRequest, TicketUpdateRequest,
    TicketStatusUpdateRequest, TicketResponse, PaginatedTicketsResponse
)
from app.services.ticket_service import TicketService
from app.models.user import User

router = APIRouter()


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ticket",
)
def create_ticket(
    request: TicketCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a ticket. Automatically assigned to the logged-in user."""
    return TicketService.create_ticket(db, request, current_user)


@router.get(
    "/",
    response_model=PaginatedTicketsResponse,
    summary="List tickets with filters, search, sorting, and pagination",
)
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: open | in_progress | closed"),
    priority: Optional[str] = Query(None, description="Filter by priority: low | medium | high"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    sort_by: Optional[str] = Query("created_at", description="Sort by: created_at | priority"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc | desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List tickets with full filtering support.
    - Regular users see only their own tickets.
    - Supports search, filters, sorting, and pagination.
    """
    return TicketService.get_tickets(
        db=db,
        current_user=current_user,
        status=status,
        priority=priority,
        category=category,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Get a ticket by ID",
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a ticket. Users can only view their own."""
    return TicketService.get_ticket_by_id(db, ticket_id, current_user)


@router.put(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Update ticket details",
)
def update_ticket(
    ticket_id: int,
    request: TicketUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update ticket fields (title, description, priority, category).
    Users can only update their own tickets.
    Admins can also set `assigned_to`.
    """
    return TicketService.update_ticket(db, ticket_id, request, current_user)


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Update ticket status only",
)
def update_ticket_status(
    ticket_id: int,
    request: TicketStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quickly update just the status of a ticket: open | in_progress | closed"""
    return TicketService.update_ticket_status(db, ticket_id, request, current_user)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a ticket",
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a ticket. Users can only delete their own tickets."""
    return TicketService.delete_ticket(db, ticket_id, current_user)
