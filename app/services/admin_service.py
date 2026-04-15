"""
Admin Service - Business Logic for Admin Operations
"""
import logging
import math
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.user import User
from app.schemas.ticket import PaginatedTicketsResponse, AdminStatsResponse

logger = logging.getLogger(__name__)


class AdminService:

    @staticmethod
    def get_all_tickets(
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedTicketsResponse:
        """Admin can view ALL tickets with full filtering capabilities."""
        query = db.query(Ticket)

        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if category:
            query = query.filter(Ticket.category == category)
        if created_by:
            query = query.filter(Ticket.created_by == created_by)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Ticket.title.ilike(search_term),
                    Ticket.description.ilike(search_term),
                )
            )

        # Sorting
        if sort_by == "priority":
            from sqlalchemy import case
            sort_column = case(
                (Ticket.priority == TicketPriority.high, 1),
                (Ticket.priority == TicketPriority.medium, 2),
                (Ticket.priority == TicketPriority.low, 3),
            )
        else:
            sort_column = Ticket.created_at

        query = query.order_by(
            asc(sort_column) if sort_order == "asc" else desc(sort_column)
        )

        total = query.count()
        offset = (page - 1) * limit
        tickets = query.offset(offset).limit(limit).all()
        total_pages = math.ceil(total / limit) if total > 0 else 1

        return PaginatedTicketsResponse(
            tickets=tickets,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @staticmethod
    def get_stats(db: Session) -> AdminStatsResponse:
        """Aggregate statistics for the admin dashboard."""
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.open).count()
        in_progress = db.query(Ticket).filter(Ticket.status == TicketStatus.in_progress).count()
        closed_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.closed).count()
        high_priority = db.query(Ticket).filter(Ticket.priority == TicketPriority.high).count()
        medium_priority = db.query(Ticket).filter(Ticket.priority == TicketPriority.medium).count()
        low_priority = db.query(Ticket).filter(Ticket.priority == TicketPriority.low).count()
        total_users = db.query(User).count()

        logger.info("Admin stats fetched.")
        return AdminStatsResponse(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            in_progress_tickets=in_progress,
            closed_tickets=closed_tickets,
            high_priority_tickets=high_priority,
            medium_priority_tickets=medium_priority,
            low_priority_tickets=low_priority,
            total_users=total_users,
        )
