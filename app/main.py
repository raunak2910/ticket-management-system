"""
Ticket Management System - Main Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, Base
from app.routes import auth, tickets, admin, ai
from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    logger.info("Starting Ticket Management System...")
    # Create all database tables on startup
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
    yield
    logger.info("Shutting down Ticket Management System...")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Ticket Management System API

A production-ready ticket management system with:
- **JWT Authentication** (register, login)
- **Role-Based Access Control** (Admin / User)
- **Ticket CRUD** with filters, pagination, search, sorting
- **AI/RAG Assistant** for natural language ticket queries

### Roles
- **User**: Manage only their own tickets
- **Admin**: Manage all tickets, view stats, assign tickets
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/ai", tags=["AI Assistant"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "message": "Ticket Management System API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {"status": "healthy", "app": settings.APP_NAME}
