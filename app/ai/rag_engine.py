"""
RAG Engine - Retrieval-Augmented Generation: Data Retrieval Layer
Fetches relevant ticket data from the database based on parsed query intent.
NO external vector DB or LangChain used — pure SQL retrieval.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.user import User
from app.ai.query_parser import ParsedQuery

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieves structured ticket context from the database
    based on the parsed query. This context is then passed
    to the response generator to produce a human-readable answer.
    """

    def retrieve(self, db: Session, parsed: ParsedQuery) -> Dict[str, Any]:
        """
        Main retrieval dispatcher. Routes to the correct retrieval
        strategy based on query type.
        """
        query_type = parsed.query_type

        if query_type in ("ticket_status", "summarize_ticket") and parsed.ticket_id:
            return self._retrieve_single_ticket(db, parsed.ticket_id)

        if query_type == "list_tickets":
            return self._retrieve_filtered_tickets(db, parsed)

        if query_type == "user_tickets":
            return self._retrieve_user_tickets(db, parsed)

        if query_type == "stats":
            return self._retrieve_stats(db)

        # Fallback: return recent tickets
        logger.debug("Unknown query type — falling back to recent tickets.")
        return self._retrieve_filtered_tickets(db, parsed)

    def _retrieve_single_ticket(self, db: Session, ticket_id: int) -> Dict[str, Any]:
        """Retrieve full details of a single ticket by ID."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return {"found": False, "ticket_id": ticket_id, "tickets": []}

        creator = db.query(User).filter(User.id == ticket.created_by).first()
        assignee = (
            db.query(User).filter(User.id == ticket.assigned_to).first()
            if ticket.assigned_to else None
        )

        return {
            "found": True,
            "ticket_id": ticket_id,
            "tickets": [self._serialize_ticket(ticket, creator, assignee)],
        }

    def _retrieve_filtered_tickets(self, db: Session, parsed: ParsedQuery) -> Dict[str, Any]:
        """Retrieve tickets matching status/priority/category filters."""
        query = db.query(Ticket)

        if parsed.status:
            query = query.filter(Ticket.status == parsed.status)
        if parsed.priority:
            query = query.filter(Ticket.priority == parsed.priority)
        if parsed.category:
            query = query.filter(Ticket.category == parsed.category)

        # Limit results to avoid massive context
        tickets = query.order_by(Ticket.created_at.desc()).limit(20).all()
        total = query.count()

        serialized = [self._serialize_ticket(t) for t in tickets]
        return {
            "found": len(tickets) > 0,
            "total": total,
            "tickets": serialized,
            "filters": {
                "status": parsed.status,
                "priority": parsed.priority,
                "category": parsed.category,
            },
        }

    def _retrieve_user_tickets(self, db: Session, parsed: ParsedQuery) -> Dict[str, Any]:
        """Retrieve tickets for a specific user (by name or ID)."""
        user = None

        if parsed.user_id:
            user = db.query(User).filter(User.id == parsed.user_id).first()
        elif parsed.username:
            # Case-insensitive name search
            user = (
                db.query(User)
                .filter(User.name.ilike(f"%{parsed.username}%"))
                .first()
            )

        if not user:
            return {
                "found": False,
                "tickets": [],
                "message": f"No user found matching '{parsed.username or parsed.user_id}'",
            }

        tickets = (
            db.query(Ticket)
            .filter(Ticket.created_by == user.id)
            .order_by(Ticket.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "found": True,
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "total": len(tickets),
            "tickets": [self._serialize_ticket(t) for t in tickets],
        }

    def _retrieve_stats(self, db: Session) -> Dict[str, Any]:
        """Retrieve high-level statistics."""
        from app.models.ticket import TicketStatus, TicketPriority

        return {
            "found": True,
            "tickets": [],
            "stats": {
                "total": db.query(Ticket).count(),
                "open": db.query(Ticket).filter(Ticket.status == TicketStatus.open).count(),
                "in_progress": db.query(Ticket).filter(Ticket.status == TicketStatus.in_progress).count(),
                "closed": db.query(Ticket).filter(Ticket.status == TicketStatus.closed).count(),
                "high_priority": db.query(Ticket).filter(Ticket.priority == TicketPriority.high).count(),
                "medium_priority": db.query(Ticket).filter(Ticket.priority == TicketPriority.medium).count(),
                "low_priority": db.query(Ticket).filter(Ticket.priority == TicketPriority.low).count(),
                "total_users": db.query(User).count(),
            },
        }

    def _serialize_ticket(
        self,
        ticket: Ticket,
        creator: Optional[User] = None,
        assignee: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Convert a Ticket ORM object to a plain dictionary for context."""
        return {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category or "N/A",
            "created_by": creator.name if creator else f"User #{ticket.created_by}",
            "assigned_to": assignee.name if assignee else "Unassigned",
            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": ticket.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
