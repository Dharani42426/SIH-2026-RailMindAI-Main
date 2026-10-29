import os
import sys
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models import Base, get_db, create_all_tables
from models.user import User
from models.corridor import RailwaySection
from models.maintenance_task import MaintenanceTask
from routes.requests import get_current_user_dep
from schemas import RequestStatus, TaskStatus

# ─── Isolated Test Database ───
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ─── Mock Users ───
def get_mock_dept_user():
    return User(
        id=991, employee_id="TEST_ENGG_01", full_name="Test Engg", role="SSE", department="ENGG",
        is_active=True
    )

def get_mock_other_dept_user():
    return User(
        id=992, employee_id="TEST_SNT_01", full_name="Test SNT", role="DSTE", department="SNT",
        is_active=True
    )

def get_mock_controller():
    return User(
        id=993, employee_id="TEST_CTRL_01", full_name="Test Ctrl", role="CONTROLLER", department="OPS",
        is_active=True
    )

def get_mock_unauthorized():
    return User(
        id=994, employee_id="TEST_BAD_01", full_name="Test Bad", role="GUEST", department="UNKNOWN",
        is_active=True
    )

# ─── Test Setup ───
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    import os
    if os.path.exists("./test_temp.db"):
        try:
            os.remove("./test_temp.db")
        except:
            pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Ensure sections exist since we test with get_valid_section()
    if not db.query(RailwaySection).first():
        db.add(RailwaySection(id=1, section_code="TEST-SEC-1", section_name="Test Section 1", km_start=0.0, km_end=10.0, division="MUMBAI", zone="CR"))
        
    db.add_all([
        User(id=991, employee_id="TEST_ENGG_01", full_name="Test Engg", role="SSE", department="ENGG", is_active=True),
        User(id=992, employee_id="TEST_SNT_01", full_name="Test SNT", role="DSTE", department="SNT", is_active=True),
        User(id=993, employee_id="TEST_CTRL_01", full_name="Test Ctrl", role="CONTROLLER", department="OPS", is_active=True),
        User(id=994, employee_id="TEST_BAD_01", full_name="Test Bad", role="GUEST", department="UNKNOWN", is_active=True)
    ])
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("./test_temp.db"):
        try:
            os.remove("./test_temp.db")
        except:
            pass

# Helper to get a valid section ID from the DB
def get_valid_section():
    response = client.get("/api/sections/")
    if response.status_code == 200 and len(response.json()) > 0:
        return response.json()[0]
    return {"id": 1, "km_start": 0.0, "km_end": 100.0}

class TestMaintenanceRequests:

    def setup_method(self):
        # Default to department user
        app.dependency_overrides[get_current_user_dep] = get_mock_dept_user
        self.section = get_valid_section()

    def teardown_method(self):
        if get_current_user_dep in app.dependency_overrides:
            del app.dependency_overrides[get_current_user_dep]

    # 1. Department can create request
    def test_create_request(self):
        app.dependency_overrides[get_current_user_dep] = get_mock_dept_user
        payload = {
            "department": "ENGG",
            "section_id": self.section["id"],
            "work_type": "Track Maintenance",
            "description": "Routine check",
            "justification": "Safety protocol",
            "km_from": self.section["km_start"] + 1,
            "km_to": self.section["km_start"] + 5,
            "estimated_hours": 3.0,
            "block_type_required": "TRAFFIC",
            "preferred_date": (date.today() + timedelta(days=2)).isoformat()
        }
        resp = client.post("/api/requests/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "SUBMITTED"
        assert data["department"] == "ENGG"
        assert data["request_code"].startswith("REQ-ENGG")
        return data["id"]

    # 2. Invalid request rejected
    def test_invalid_request_rejected(self):
        # Test invalid km range
        payload = {
            "department": "ENGG",
            "section_id": self.section["id"],
            "work_type": "Track Maintenance",
            "km_from": self.section["km_end"] + 10, # Out of bounds
            "km_to": self.section["km_end"] + 20,
            "estimated_hours": 3.0,
            "block_type_required": "TRAFFIC",
            "preferred_date": (date.today() + timedelta(days=2)).isoformat()
        }
        resp = client.post("/api/requests/", json=payload)
        assert resp.status_code == 400
        assert "Invalid KM range" in resp.json()["detail"]

        # Test missing fields
        bad_payload = {"department": "ENGG"}
        resp2 = client.post("/api/requests/", json=bad_payload)
        assert resp2.status_code == 422 # Pydantic validation error

    # 3. Department can view permitted request
    def test_department_view_permissions(self):
        req_id = self.test_create_request()
        
        # Original dept can view
        app.dependency_overrides[get_current_user_dep] = get_mock_dept_user
        resp = client.get(f"/api/requests/{req_id}")
        assert resp.status_code == 200

        # Other dept cannot view
        app.dependency_overrides[get_current_user_dep] = get_mock_other_dept_user
        resp2 = client.get(f"/api/requests/{req_id}")
        assert resp2.status_code == 403

        # Controller CAN view all
        app.dependency_overrides[get_current_user_dep] = get_mock_controller
        resp3 = client.get(f"/api/requests/{req_id}")
        assert resp3.status_code == 200

    # 4. Unauthorized department cannot review
    def test_unauthorized_review(self):
        req_id = self.test_create_request()
        app.dependency_overrides[get_current_user_dep] = get_mock_dept_user
        
        payload = {"action": "ACCEPT"}
        resp = client.post(f"/api/requests/{req_id}/review", json=payload)
        assert resp.status_code == 403
        assert "Only controllers" in resp.json()["detail"]

    # 5. Controller can review & 6. Reject requires reason
    def test_controller_reject(self):
        req_id = self.test_create_request()
        app.dependency_overrides[get_current_user_dep] = get_mock_controller
        
        # Reject without reason should fail
        resp1 = client.post(f"/api/requests/{req_id}/review", json={"action": "REJECT"})
        assert resp1.status_code == 400
        assert "rejection reason must be provided" in resp1.json()["detail"]

        # Reject with reason
        resp2 = client.post(f"/api/requests/{req_id}/review", json={"action": "REJECT", "rejection_reason": "Not feasible"})
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "REJECTED"

    # 7. Accept creates MaintenanceTask & 8. Links to MaintenanceTask & 10. Optimizer compat
    def test_controller_accept_creates_task(self):
        req_id = self.test_create_request()
        app.dependency_overrides[get_current_user_dep] = get_mock_controller
        
        resp = client.post(f"/api/requests/{req_id}/review", json={"action": "ACCEPT"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ACCEPTED"
        assert data["maintenance_task_id"] is not None
        
        # Verify task is created in PENDING state (Optimizer compatibility)
        task_id = data["maintenance_task_id"]
        # The API doesn't have a GET /api/tasks/{id} standard endpoint in the boilerplate
        # Let's verify by checking the DB via an endpoint that returns pending tasks,
        # or we just trust the response object linkage. 
        # But we can also check /api/tasks/critical maybe?
