"""
Database Seeding Script
Creates sample admin + users + tickets for development/testing.

Usage:
    python seed.py
"""
import sys
import os

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.auth.jwt_handler import hash_password

# ── Create all tables ──────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed():
    print("🌱 Seeding database...")

    # ── Clear existing data ────────────────────────────────────────
    db.query(Ticket).delete()
    db.query(User).delete()
    db.commit()

    # ── Create Users ───────────────────────────────────────────────
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password=hash_password("admin123"),
        role=UserRole.admin,
    )
    alice = User(
        name="Alice Johnson",
        email="alice@example.com",
        password=hash_password("alice123"),
        role=UserRole.user,
    )
    bob = User(
        name="Bob Smith",
        email="bob@example.com",
        password=hash_password("bob123"),
        role=UserRole.user,
    )
    carol = User(
        name="Carol White",
        email="carol@example.com",
        password=hash_password("carol123"),
        role=UserRole.user,
    )

    db.add_all([admin, alice, bob, carol])
    db.commit()
    db.refresh(admin)
    db.refresh(alice)
    db.refresh(bob)
    db.refresh(carol)
    print(f"✅ Created {4} users")

    # ── Create Tickets ─────────────────────────────────────────────
    tickets = [
        Ticket(
            title="Login page broken after deployment",
            description="Users are unable to login after the v2.3 deployment. Returns 500 error.",
            status=TicketStatus.open,
            priority=TicketPriority.high,
            category="bug",
            created_by=alice.id,
            assigned_to=admin.id,
        ),
        Ticket(
            title="Add dark mode support",
            description="Users have requested a dark mode option in the settings panel.",
            status=TicketStatus.open,
            priority=TicketPriority.medium,
            category="feature",
            created_by=alice.id,
        ),
        Ticket(
            title="Database connection timeout",
            description="Intermittent connection timeouts observed on the production DB during peak hours.",
            status=TicketStatus.in_progress,
            priority=TicketPriority.high,
            category="infrastructure",
            created_by=bob.id,
            assigned_to=admin.id,
        ),
        Ticket(
            title="Update user documentation",
            description="The API documentation needs to be updated for v2.0 endpoints.",
            status=TicketStatus.open,
            priority=TicketPriority.low,
            category="documentation",
            created_by=bob.id,
        ),
        Ticket(
            title="Payment gateway integration",
            description="Integrate Stripe payment gateway for premium subscriptions.",
            status=TicketStatus.in_progress,
            priority=TicketPriority.high,
            category="feature",
            created_by=carol.id,
            assigned_to=alice.id,
        ),
        Ticket(
            title="Fix broken CSV export",
            description="The CSV export feature is exporting malformed data for rows with commas.",
            status=TicketStatus.closed,
            priority=TicketPriority.medium,
            category="bug",
            created_by=carol.id,
        ),
        Ticket(
            title="Improve search performance",
            description="Full-text search is slow for large datasets. Consider adding Elasticsearch.",
            status=TicketStatus.open,
            priority=TicketPriority.medium,
            category="performance",
            created_by=alice.id,
        ),
        Ticket(
            title="Setup CI/CD pipeline",
            description="Configure GitHub Actions for automated testing and deployment.",
            status=TicketStatus.closed,
            priority=TicketPriority.low,
            category="devops",
            created_by=admin.id,
        ),
    ]

    db.add_all(tickets)
    db.commit()
    print(f"✅ Created {len(tickets)} tickets")

    print("\n🎉 Seeding complete!\n")
    print("=== Login Credentials ===")
    print("Admin  | admin@example.com  | admin123")
    print("Alice  | alice@example.com  | alice123")
    print("Bob    | bob@example.com    | bob123")
    print("Carol  | carol@example.com  | carol123")
    print("\nRun: uvicorn app.main:app --reload")
    print("Docs: http://localhost:8000/docs")

    db.close()

if __name__ == "__main__":
    seed()
