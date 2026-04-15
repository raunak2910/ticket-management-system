"""
Ticket Service - Business Logic Layer
Handles all ticket operations with proper authorization checks
"""
import logging
import math
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.models.user import User, UserRole
from app.schemas.ticket import (
    TicketCreateRequest, TicketUpdateRequest,
    TicketStatusUpdateRequest, PaginatedTicketsResponse
)
from app.core.exceptions import TicketNotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)


class TicketService:

    @staticmethod
    def create_ticket(db: Session, request: TicketCreateRequest, current_user: User) -> Ticket:
        """Create a new ticket assigned to the current user."""
        ticket = Ticket(
            title=request.title,
            description=request.description,
            priority=request.priority,
            category=request.category,
            created_by=current_user.id,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        logger.info(f"Ticket #{ticket.id} created by user #{current_user.id}")
        return ticket

    @staticmethod
    def get_tickets(
        db: Session,
        current_user: User,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "created_at",
        sort_order: Optional[str] = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedTicketsResponse:
        """
        List tickets with filters, search, sorting, and pagination.
        - Users see only their own tickets
        - Admins can optionally filter by created_by
        """
        query = db.query(Ticket)

        # Users can only see their own tickets
        if current_user.role != UserRole.admin:
            query = query.filter(Ticket.created_by == current_user.id)

        # Apply filters
        if status:
            query = query.filter(Ticket.status == status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        if category:
            query = query.filter(Ticket.category == category)

        # Full-text search in title and description
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Ticket.title.ilike(search_term),
                    Ticket.description.ilike(search_term),
                )
            )

        # Sorting
        sort_column = Ticket.created_at
        if sort_by == "priority":
            # Custom priority sort order: high > medium > low
            from sqlalchemy import case
            sort_column = case(
                (Ticket.priority == TicketPriority.high, 1),
                (Ticket.priority == TicketPriority.medium, 2),
                (Ticket.priority == TicketPriority.low, 3),
            )

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
    def get_ticket_by_id(db: Session, ticket_id: int, current_user: User) -> Ticket:
        """Get a single ticket by ID with ownership check."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise TicketNotFoundError(ticket_id)

        # Non-admins can only view their own tickets
        if current_user.role != UserRole.admin and ticket.created_by != current_user.id:
            raise UnauthorizedError("You can only view your own tickets.")

        return ticket

    @staticmethod
    def update_ticket(
        db: Session, ticket_id: int, request: TicketUpdateRequest, current_user: User
    ) -> Ticket:
        """Update ticket fields (non-admin can only update own tickets)."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise TicketNotFoundError(ticket_id)

        if current_user.role != UserRole.admin and ticket.created_by != current_user.id:
            raise UnauthorizedError("You can only update your own tickets.")

        # Only update provided fields (partial update)
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ticket, field, value)

        db.commit()
        db.refresh(ticket)
        logger.info(f"Ticket #{ticket_id} updated by user #{current_user.id}")
        return ticket

    @staticmethod
    def update_ticket_status(
        db: Session, ticket_id: int, request: TicketStatusUpdateRequest, current_user: User
    ) -> Ticket:
        """Update only the status of a ticket."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise TicketNotFoundError(ticket_id)

        if current_user.role != UserRole.admin and ticket.created_by != current_user.id:
            raise UnauthorizedError("You can only update status of your own tickets.")

        old_status = ticket.status
        ticket.status = request.status
        db.commit()
        db.refresh(ticket)
        logger.info(
            f"Ticket #{ticket_id} status changed: {old_status} -> {request.status} "
            f"by user #{current_user.id}"
        )
        return ticket

    @staticmethod
    def delete_ticket(db: Session, ticket_id: int, current_user: User) -> dict:
        """Delete a ticket (users can only delete their own)."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise TicketNotFoundError(ticket_id)

        if current_user.role != UserRole.admin and ticket.created_by != current_user.id:
            raise UnauthorizedError("You can only delete your own tickets.")

        db.delete(ticket)
        db.commit()
        logger.info(f"Ticket #{ticket_id} deleted by user #{current_user.id}")
        return {"message": f"Ticket #{ticket_id} deleted successfully."}
