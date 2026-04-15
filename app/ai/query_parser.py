"""
Query Parser - Natural Language Understanding
Parses user queries using rule-based NLP and keyword matching.
No external NLP libraries required.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuery:
    """Structured representation of a parsed natural language query."""
    query_type: str                        # e.g. "ticket_status", "list_tickets", "summarize", "user_tickets"
    ticket_id: Optional[int] = None        # Specific ticket ID if mentioned
    status: Optional[str] = None           # open, in_progress, closed
    priority: Optional[str] = None        # low, medium, high
    username: Optional[str] = None        # User name filter
    user_id: Optional[int] = None         # User ID filter
    category: Optional[str] = None        # Category filter
    keywords: List[str] = field(default_factory=list)  # Extra keywords
    raw_query: str = ""                   # Original query string


class QueryParser:
    """
    Rule-based query parser.
    Identifies intent and extracts entities from natural language queries.
    """

    # Status keywords
    STATUS_MAP = {
        "open": "open",
        "in progress": "in_progress",
        "in_progress": "in_progress",
        "inprogress": "in_progress",
        "closed": "closed",
        "close": "closed",
        "done": "closed",
        "resolved": "closed",
        "completed": "closed",
    }

    # Priority keywords
    PRIORITY_MAP = {
        "high": "high",
        "urgent": "high",
        "critical": "high",
        "medium": "medium",
        "normal": "medium",
        "moderate": "medium",
        "low": "low",
        "minor": "low",
    }

    def parse(self, query: str) -> ParsedQuery:
        """
        Main entry point. Parse a raw query string into a structured ParsedQuery.
        """
        normalized = query.lower().strip()
        parsed = ParsedQuery(raw_query=query, query_type="unknown")

        # --- Intent Detection ---
        parsed.query_type = self._detect_intent(normalized)

        # --- Entity Extraction ---
        parsed.ticket_id = self._extract_ticket_id(normalized)
        parsed.status = self._extract_status(normalized)
        parsed.priority = self._extract_priority(normalized)
        parsed.username = self._extract_username(query)  # preserve case for names
        parsed.user_id = self._extract_user_id(normalized)

        logger.debug(f"Parsed query: type={parsed.query_type}, ticket_id={parsed.ticket_id}, "
                     f"status={parsed.status}, priority={parsed.priority}")
        return parsed

    def _detect_intent(self, text: str) -> str:
        """Classify the query intent."""
        # Ticket status check
        if re.search(r"\bstatus\b", text) and re.search(r"\bticket\b", text):
            return "ticket_status"

        # Specific ticket lookup
        if re.search(r"\bticket\s+#?\d+\b", text):
            if "summarize" in text or "summary" in text or "detail" in text:
                return "summarize_ticket"
            return "ticket_status"

        # Summarize
        if re.search(r"\b(summarize|summary|details? of|describe)\b", text):
            return "summarize_ticket"

        # User-based queries
        if re.search(r"\b(by user|created by|assigned to|belonging to|from user)\b", text):
            return "user_tickets"

        # Listing tickets — with or without explicit "ticket" keyword
        if re.search(r"\b(show|list|get|find|display|all|fetch)\b", text):
            return "list_tickets"

        # Stats/overview
        if re.search(r"\b(stats|statistics|overview|count|how many|total)\b", text):
            return "stats"

        # Fallback: if any ticket keyword present
        if "ticket" in text:
            return "list_tickets"

        return "unknown"

    def _extract_ticket_id(self, text: str) -> Optional[int]:
        """Extract a ticket ID from the query. e.g. 'ticket 12', 'ticket #5'"""
        match = re.search(r"ticket\s+#?(\d+)", text)
        if match:
            return int(match.group(1))
        # Also match standalone numbers if context is clear
        match = re.search(r"#(\d+)", text)
        if match:
            return int(match.group(1))
        return None

    def _extract_status(self, text: str) -> Optional[str]:
        """Extract status from text using STATUS_MAP."""
        for keyword, status in self.STATUS_MAP.items():
            if keyword in text:
                return status
        return None

    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority from text using PRIORITY_MAP."""
        for keyword, priority in self.PRIORITY_MAP.items():
            if keyword in text:
                return priority
        return None

    def _extract_username(self, text: str) -> Optional[str]:
        """
        Try to extract a username after keywords like 'by user X' or 'created by X'.
        Preserves original casing.
        """
        patterns = [
            r"by user[:\s]+([A-Za-z][A-Za-z\s]+?)(?:\?|$|,|\band\b)",
            r"created by[:\s]+([A-Za-z][A-Za-z\s]+?)(?:\?|$|,|\band\b)",
            r"assigned to[:\s]+([A-Za-z][A-Za-z\s]+?)(?:\?|$|,|\band\b)",
            r"from user[:\s]+([A-Za-z][A-Za-z\s]+?)(?:\?|$|,|\band\b)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_user_id(self, text: str) -> Optional[int]:
        """Extract user ID if mentioned like 'user id 5' or 'user #3'."""
        match = re.search(r"user\s+(?:id\s+)?#?(\d+)", text)
        if match:
            return int(match.group(1))
        return None
