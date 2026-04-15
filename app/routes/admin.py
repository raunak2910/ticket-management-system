"""
Admin Routes
All routes require Admin role.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import require_admin
from app.schemas.ticket import PaginatedTicketsResponse, AdminStatsResponse
from app.services.admin_service import AdminService
from app.models.user import User

router = APIRouter()


@router.get(
    "/tickets",
    response_model=PaginatedTicketsResponse,
    summary="[Admin] List ALL tickets with full filtering",
)
def admin_list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    sort_by: Optional[str] = Query("created_at", description="Sort by: created_at | priority"),
    sort_order: Optional[str] = Query("desc", description="asc | desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Admin-only endpoint to list all tickets in the system.
    Supports all filters including `created_by` (user ID).
    """
    return AdminService.get_all_tickets(
        db=db,
        status=status,
        priority=priority,
        category=category,
        created_by=created_by,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="[Admin] Get system-wide ticket statistics",
)
def admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Returns aggregated statistics:
    - Ticket counts by status and priority
    - Total users in the system
    """
    return AdminService.get_stats(db)
