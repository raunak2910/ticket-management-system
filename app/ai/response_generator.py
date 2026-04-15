"""
Response Generator - Natural Language Response Formatting
Converts structured DB retrieval results into human-readable answers.
Uses template-based generation (no LangChain).
Optionally enhanced with OpenAI API if configured.
"""
import logging
from typing import Any, Dict

from app.ai.query_parser import ParsedQuery
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates natural language responses from retrieved ticket data.
    Falls back to template-based generation if OpenAI is not configured.
    """

    def generate(self, parsed: ParsedQuery, context: Dict[str, Any]) -> str:
        """
        Generate a human-readable response.
        Tries OpenAI first (if key available), then falls back to templates.
        """
        if settings.OPENAI_API_KEY:
            try:
                return self._generate_with_openai(parsed, context)
            except Exception as e:
                logger.warning(f"OpenAI generation failed, using template fallback: {e}")

        return self._generate_from_template(parsed, context)

    # ─────────────────────────────────────────────
    # TEMPLATE-BASED GENERATION
    # ─────────────────────────────────────────────

    def _generate_from_template(self, parsed: ParsedQuery, context: Dict[str, Any]) -> str:
        """Route to the appropriate template based on query type."""
        qt = parsed.query_type

        if not context.get("found") and context.get("message"):
            return context["message"]

        if qt == "ticket_status":
            return self._format_ticket_status(context)

        if qt == "summarize_ticket":
            return self._format_ticket_summary(context)

        if qt == "list_tickets":
            return self._format_ticket_list(context, parsed)

        if qt == "user_tickets":
            return self._format_user_tickets(context)

        if qt == "stats":
            return self._format_stats(context)

        return self._format_ticket_list(context, parsed)

    def _format_ticket_status(self, context: Dict[str, Any]) -> str:
        if not context.get("found") or not context.get("tickets"):
            return f"❌ Ticket #{context.get('ticket_id')} was not found."

        t = context["tickets"][0]
        status_emoji = {"open": "🟡", "in_progress": "🔵", "closed": "✅"}.get(t["status"], "⚪")
        priority_emoji = {"high": "🔴", "medium": "🟠", "low": "🟢"}.get(t["priority"], "⚪")

        return (
            f"📋 **Ticket #{t['id']}: {t['title']}**\n\n"
            f"{status_emoji} **Status:** {t['status'].replace('_', ' ').title()}\n"
            f"{priority_emoji} **Priority:** {t['priority'].title()}\n"
            f"📁 **Category:** {t['category']}\n"
            f"👤 **Created by:** {t['created_by']}\n"
            f"👷 **Assigned to:** {t['assigned_to']}\n"
            f"🕐 **Created:** {t['created_at']}\n"
            f"🔄 **Last Updated:** {t['updated_at']}"
        )

    def _format_ticket_summary(self, context: Dict[str, Any]) -> str:
        if not context.get("found") or not context.get("tickets"):
            return f"❌ Ticket #{context.get('ticket_id')} was not found."

        t = context["tickets"][0]
        desc_preview = t["description"][:300] + "..." if len(t["description"]) > 300 else t["description"]

        return (
            f"📝 **Summary of Ticket #{t['id']}**\n\n"
            f"**Title:** {t['title']}\n\n"
            f"**Description:**\n{desc_preview}\n\n"
            f"**Status:** {t['status'].replace('_', ' ').title()} | "
            f"**Priority:** {t['priority'].title()} | "
            f"**Category:** {t['category']}\n\n"
            f"**Created by:** {t['created_by']} on {t['created_at']}\n"
            f"**Assigned to:** {t['assigned_to']}"
        )

    def _format_ticket_list(self, context: Dict[str, Any], parsed: ParsedQuery) -> str:
        tickets = context.get("tickets", [])
        total = context.get("total", len(tickets))
        filters = context.get("filters", {})

        # Build filter description
        filter_parts = []
        if filters.get("status"):
            filter_parts.append(f"status={filters['status'].replace('_', ' ')}")
        if filters.get("priority"):
            filter_parts.append(f"priority={filters['priority']}")
        if filters.get("category"):
            filter_parts.append(f"category={filters['category']}")
        filter_desc = " | ".join(filter_parts) if filter_parts else "all"

        if not tickets:
            return f"🔍 No tickets found matching your criteria ({filter_desc})."

        priority_emoji = {"high": "🔴", "medium": "🟠", "low": "🟢"}
        status_emoji = {"open": "🟡", "in_progress": "🔵", "closed": "✅"}

        lines = [
            f"🎫 **Found {total} ticket(s)** [{filter_desc}]",
            f"Showing {len(tickets)} result(s):\n",
        ]
        for t in tickets:
            pe = priority_emoji.get(t["priority"], "⚪")
            se = status_emoji.get(t["status"], "⚪")
            lines.append(
                f"{pe} **#{t['id']}** — {t['title']}\n"
                f"   {se} {t['status'].replace('_', ' ').title()} | "
                f"👤 {t['created_by']} | 📅 {t['created_at']}"
            )
        return "\n".join(lines)

    def _format_user_tickets(self, context: Dict[str, Any]) -> str:
        if not context.get("found"):
            return context.get("message", "User not found.")

        user = context.get("user", {})
        tickets = context.get("tickets", [])
        total = context.get("total", 0)

        if not tickets:
            return f"👤 User **{user.get('name')}** has no tickets."

        lines = [
            f"👤 **Tickets for {user.get('name')}** (ID: {user.get('id')})",
            f"📧 {user.get('email')} | {total} ticket(s) total\n",
        ]
        priority_emoji = {"high": "🔴", "medium": "🟠", "low": "🟢"}
        status_emoji = {"open": "🟡", "in_progress": "🔵", "closed": "✅"}

        for t in tickets:
            pe = priority_emoji.get(t["priority"], "⚪")
            se = status_emoji.get(t["status"], "⚪")
            lines.append(
                f"{pe} **#{t['id']}** — {t['title']}\n"
                f"   {se} {t['status'].replace('_', ' ').title()} | 📅 {t['created_at']}"
            )
        return "\n".join(lines)

    def _format_stats(self, context: Dict[str, Any]) -> str:
        stats = context.get("stats", {})
        if not stats:
            return "No statistics available."

        return (
            f"📊 **Ticket System Statistics**\n\n"
            f"🎫 **Total Tickets:** {stats['total']}\n\n"
            f"**By Status:**\n"
            f"  🟡 Open: {stats['open']}\n"
            f"  🔵 In Progress: {stats['in_progress']}\n"
            f"  ✅ Closed: {stats['closed']}\n\n"
            f"**By Priority:**\n"
            f"  🔴 High: {stats['high_priority']}\n"
            f"  🟠 Medium: {stats['medium_priority']}\n"
            f"  🟢 Low: {stats['low_priority']}\n\n"
            f"👥 **Total Users:** {stats['total_users']}"
        )

    # ─────────────────────────────────────────────
    # OPENAI-ENHANCED GENERATION (OPTIONAL)
    # ─────────────────────────────────────────────

    def _generate_with_openai(self, parsed: ParsedQuery, context: Dict[str, Any]) -> str:
        """
        Use OpenAI API to generate a more natural response.
        Retrieval is still done from DB — OpenAI only generates the final text.
        """
        import json
        import httpx

        system_prompt = (
            "You are a helpful ticket management assistant. "
            "Answer the user's question about tickets clearly and concisely. "
            "Use the provided ticket data. Format nicely with markdown."
        )

        user_message = (
            f"User query: {parsed.raw_query}\n\n"
            f"Retrieved ticket data:\n{json.dumps(context, indent=2, default=str)}"
        )

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 500,
                "temperature": 0.4,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
