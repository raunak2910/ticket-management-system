"""
Unit Tests for Ticket Management System
Run: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.ai.query_parser import QueryParser

# ── Test DB Setup (in-memory SQLite) ──────────────────────────────
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ── Helper: Register + Login ───────────────────────────────────────
def register_and_login(client, email, password, name="Test User", role="user"):
    client.post("/auth/register", json={"name": name, "email": email, "password": password, "role": role})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json().get("access_token")


# ══════════════════════════════════════════════════════════════════
# AUTH TESTS
# ══════════════════════════════════════════════════════════════════

class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "name": "Jane Doe",
            "email": "jane@test.com",
            "password": "pass1234",
            "role": "user",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "jane@test.com"
        assert data["role"] == "user"
        assert "password" not in data

    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={
            "name": "Dup User", "email": "dup@test.com", "password": "pass1234"
        })
        resp = client.post("/auth/register", json={
            "name": "Dup User2", "email": "dup@test.com", "password": "pass1234"
        })
        assert resp.status_code == 409

    def test_register_short_password(self, client):
        resp = client.post("/auth/register", json={
            "name": "Bad User", "email": "bad@test.com", "password": "123"
        })
        assert resp.status_code == 422

    def test_login_success(self, client):
        client.post("/auth/register", json={
            "name": "Login Test", "email": "logintest@test.com", "password": "pass1234"
        })
        resp = client.post("/auth/login", json={
            "email": "logintest@test.com", "password": "pass1234"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        resp = client.post("/auth/login", json={
            "email": "logintest@test.com", "password": "wrongpassword"
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@test.com", "password": "pass1234"
        })
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════
# TICKET TESTS
# ══════════════════════════════════════════════════════════════════

class TestTickets:
    def test_create_ticket(self, client):
        token = register_and_login(client, "ticket_user@test.com", "pass1234", "Ticket User")
        resp = client.post("/tickets/", json={
            "title": "Test Ticket",
            "description": "A test ticket description",
            "priority": "high",
            "category": "bug",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Ticket"
        assert data["priority"] == "high"
        assert data["status"] == "open"

    def test_create_ticket_no_auth(self, client):
        resp = client.post("/tickets/", json={
            "title": "Unauthorized", "description": "Should fail"
        })
        assert resp.status_code == 401

    def test_list_tickets(self, client):
        token = register_and_login(client, "list_user@test.com", "pass1234", "List User")
        client.post("/tickets/", json={
            "title": "My Ticket", "description": "desc", "priority": "low"
        }, headers={"Authorization": f"Bearer {token}"})
        resp = client.get("/tickets/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "tickets" in data
        assert data["total"] >= 1

    def test_get_ticket_by_id(self, client):
        token = register_and_login(client, "getticket@test.com", "pass1234", "Get User")
        create_resp = client.post("/tickets/", json={
            "title": "Get Me", "description": "Fetch this ticket"
        }, headers={"Authorization": f"Bearer {token}"})
        ticket_id = create_resp.json()["id"]

        resp = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == ticket_id

    def test_update_ticket(self, client):
        token = register_and_login(client, "update_user@test.com", "pass1234", "Update User")
        create_resp = client.post("/tickets/", json={
            "title": "Original", "description": "Original desc"
        }, headers={"Authorization": f"Bearer {token}"})
        ticket_id = create_resp.json()["id"]

        resp = client.put(f"/tickets/{ticket_id}", json={
            "title": "Updated Title"
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_update_status(self, client):
        token = register_and_login(client, "status_user@test.com", "pass1234", "Status User")
        create_resp = client.post("/tickets/", json={
            "title": "Status Test", "description": "Testing status update"
        }, headers={"Authorization": f"Bearer {token}"})
        ticket_id = create_resp.json()["id"]

        resp = client.patch(f"/tickets/{ticket_id}/status",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    def test_delete_ticket(self, client):
        token = register_and_login(client, "delete_user@test.com", "pass1234", "Delete User")
        create_resp = client.post("/tickets/", json={
            "title": "Delete Me", "description": "To be deleted"
        }, headers={"Authorization": f"Bearer {token}"})
        ticket_id = create_resp.json()["id"]

        resp = client.delete(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

        # Confirm deleted
        resp = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_user_cannot_access_others_ticket(self, client):
        token1 = register_and_login(client, "user1@test.com", "pass1234", "User One")
        token2 = register_and_login(client, "user2@test.com", "pass1234", "User Two")

        create_resp = client.post("/tickets/", json={
            "title": "Private Ticket", "description": "User 1 only"
        }, headers={"Authorization": f"Bearer {token1}"})
        ticket_id = create_resp.json()["id"]

        resp = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token2}"})
        assert resp.status_code == 403


# ══════════════════════════════════════════════════════════════════
# ADMIN TESTS
# ══════════════════════════════════════════════════════════════════

class TestAdmin:
    def test_admin_can_view_all_tickets(self, client):
        admin_token = register_and_login(
            client, "admin@test.com", "admin1234", "Admin User", role="admin"
        )
        user_token = register_and_login(client, "regular@test.com", "pass1234", "Regular")
        client.post("/tickets/", json={
            "title": "Regular Ticket", "description": "desc"
        }, headers={"Authorization": f"Bearer {user_token}"})

        resp = client.get("/admin/tickets", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_non_admin_cannot_access_admin_routes(self, client):
        token = register_and_login(client, "nonadmin@test.com", "pass1234", "Non Admin")
        resp = client.get("/admin/tickets", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_stats(self, client):
        admin_token = register_and_login(
            client, "statsadmin@test.com", "admin1234", "Stats Admin", role="admin"
        )
        resp = client.get("/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_tickets" in data
        assert "open_tickets" in data


# ══════════════════════════════════════════════════════════════════
# AI QUERY PARSER TESTS (Unit tests — no DB needed)
# ══════════════════════════════════════════════════════════════════

class TestQueryParser:
    def setup_method(self):
        self.parser = QueryParser()

    def test_parse_ticket_status(self):
        result = self.parser.parse("What is the status of ticket 12?")
        assert result.query_type == "ticket_status"
        assert result.ticket_id == 12

    def test_parse_summarize(self):
        result = self.parser.parse("Summarize ticket 5")
        assert result.query_type in ("summarize_ticket", "ticket_status")
        assert result.ticket_id == 5

    def test_parse_list_high_priority(self):
        result = self.parser.parse("Show all high priority open tickets")
        assert result.query_type == "list_tickets"
        assert result.priority == "high"
        assert result.status == "open"

    def test_parse_user_tickets(self):
        result = self.parser.parse("Which tickets were created by user Alice?")
        assert result.query_type == "user_tickets"
        assert result.username is not None

    def test_parse_stats(self):
        result = self.parser.parse("How many tickets are open?")
        assert result.query_type in ("stats", "list_tickets")

    def test_parse_priority_extraction(self):
        result = self.parser.parse("Show all critical tickets")
        assert result.priority == "high"

    def test_parse_status_closed(self):
        result = self.parser.parse("List all resolved tickets")
        assert result.status == "closed"


# ══════════════════════════════════════════════════════════════════
# AI ENDPOINT TESTS
# ══════════════════════════════════════════════════════════════════

class TestAIEndpoint:
    def test_ai_query_requires_auth(self, client):
        resp = client.post("/ai/query", json={"query": "Show all tickets"})
        assert resp.status_code == 401

    def test_ai_query_basic(self, client):
        token = register_and_login(client, "aiuser@test.com", "pass1234", "AI User")
        resp = client.post("/ai/query",
            json={"query": "Show all open tickets"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "query_type" in data

    def test_ai_query_specific_ticket(self, client):
        token = register_and_login(client, "aiuser2@test.com", "pass1234", "AI User 2")
        # Create a ticket first
        create_resp = client.post("/tickets/", json={
            "title": "AI Test Ticket", "description": "For AI query testing"
        }, headers={"Authorization": f"Bearer {token}"})
        ticket_id = create_resp.json()["id"]

        resp = client.post("/ai/query",
            json={"query": f"What is the status of ticket {ticket_id}?"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert "answer" in resp.json()
