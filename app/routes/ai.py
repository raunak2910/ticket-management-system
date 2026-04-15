"""
AI Assistant Routes
POST /ai/query — Natural language ticket queries using RAG
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user
from app.schemas.ai import AIQueryRequest, AIQueryResponse
from app.ai.query_parser import QueryParser
from app.ai.rag_engine import RAGEngine
from app.ai.response_generator import ResponseGenerator
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton instances (lightweight, stateless)
query_parser = QueryParser()
rag_engine = RAGEngine()
response_generator = ResponseGenerator()


@router.post(
    "/query",
    response_model=AIQueryResponse,
    summary="Ask a natural language question about tickets",
)
def ai_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ## AI Ticket Assistant (RAG-powered)

    Ask natural language questions about tickets. Examples:

    - `"What is the status of ticket 12?"`
    - `"Show all high priority open tickets"`
    - `"Summarize ticket 5"`
    - `"Which tickets were created by John?"`
    - `"How many tickets are open?"`

    ### How it works:
    1. **Query Parser** classifies intent and extracts entities (ticket ID, priority, status, username)
    2. **RAG Engine** retrieves relevant ticket data from the database
    3. **Response Generator** formats a human-readable answer from the retrieved context

    No LangChain used — pure custom implementation.
    """
    logger.info(f"AI query from user #{current_user.id}: '{request.query}'")

    # Step 1: Parse natural language query
    parsed = query_parser.parse(request.query)

    # Step 2: Retrieve relevant data from DB
    context = rag_engine.retrieve(db, parsed)

    # Step 3: Generate human-readable response
    answer = response_generator.generate(parsed, context)

    return AIQueryResponse(
        query=request.query,
        answer=answer,
        data=context.get("tickets") or context.get("stats"),
        query_type=parsed.query_type,
    )
