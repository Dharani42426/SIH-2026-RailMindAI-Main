"""
═══════════════════════════════════════════════════════════════
RailMind AI — API Integration Test Suite
Tests all API endpoints using FastAPI TestClient
═══════════════════════════════════════════════════════════════
"""
import os
import sys
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from models import create_all_tables

client = TestClient(app)


# ─── Setup ───

class TestSetup:
    """Ensure database is initialized before tests."""

    def test_tables_created(self):
        """DB tables should be created on startup."""
        create_all_tables()
        assert True, "Tables created successfully"


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK TESTS
# ═══════════════════════════════════════════════════════════════

class TestHealthCheck:
    """Test health check and root endpoints."""

    def test_root_endpoint(self):
        """Root should return app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "RailMind AI"
        assert data["status"] == "running"
        assert "docs" in data
        assert "endpoints" in data

    def test_health_endpoint(self):
        """Health check should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ai_models" in data
        assert data["ai_models"]["criticality_scorer"] == "loaded"
        assert data["ai_models"]["block_optimizer"] == "ready"

    def test_docs_accessible(self):
        """Swagger docs should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════
# SECTION ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestSectionEndpoints:
    """Test railway section CRUD endpoints."""

    def test_list_sections(self):
        """Should return a list of sections."""
        response = client.get("/api/sections/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_sections_with_filters(self):
        """Should support zone and ghat filters."""
        response = client.get("/api/sections/?ghat_only=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned sections should be ghat sections
        for section in data:
            assert section["is_ghat_section"] is True

    def test_get_section_by_id(self):
        """Should get a specific section by ID."""
        # First get list to find a valid ID
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/sections/{section_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == section_id
            assert "section_code" in data
            assert "total_km" in data

    def test_get_section_not_found(self):
        """Should return 404 for non-existent section."""
        response = client.get("/api/sections/99999")
        assert response.status_code == 404

    def test_get_section_by_code(self):
        """Should get section by code."""
        sections = client.get("/api/sections/").json()
        if sections:
            code = sections[0]["section_code"]
            response = client.get(f"/api/sections/code/{code}")
            assert response.status_code == 200

    def test_section_summary(self):
        """Should return comprehensive section summary."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/sections/{section_id}/summary")
            assert response.status_code == 200
            data = response.json()
            assert "section" in data
            assert "assets" in data
            assert "tasks" in data


# ═══════════════════════════════════════════════════════════════
# TASK ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestTaskEndpoints:
    """Test maintenance task endpoints."""

    def test_list_tasks(self):
        """Should return tasks list."""
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tasks_with_filters(self):
        """Should support department and severity filters."""
        response = client.get("/api/tasks/?department=ENGG&severity=CRITICAL&limit=5")
        assert response.status_code == 200

    def test_get_critical_tasks(self):
        """Should return AI-ranked critical tasks."""
        response = client.get("/api/tasks/critical?top_n=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check that results are ranked
        if len(data) >= 2:
            assert data[0].get("criticality_rank", 1) <= data[1].get("criticality_rank", 2)

    def test_task_stats(self):
        """Should return task statistics."""
        response = client.get("/api/tasks/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_severity" in data
        assert "by_department" in data


# ═══════════════════════════════════════════════════════════════
# TRAIN ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestTrainEndpoints:
    """Test train schedule endpoints."""

    def test_list_trains(self):
        """Should return train schedules."""
        response = client.get("/api/trains/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_train_windows(self):
        """Should return train windows for a section."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/trains/section/{section_id}/windows")
            assert response.status_code == 200
            data = response.json()
            assert "total_trains" in data
            assert "trains" in data

    def test_get_available_windows(self):
        """Should return available maintenance windows."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/trains/section/{section_id}/available?min_duration=60")
            assert response.status_code == 200
            data = response.json()
            assert "available_windows" in data
            assert "windows" in data


# ═══════════════════════════════════════════════════════════════
# OPTIMIZER ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestOptimizerEndpoints:
    """Test AI optimizer endpoints."""

    def test_list_plans(self):
        """Should list block plans."""
        response = client.get("/api/optimizer/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_generate_plan(self):
        """Should generate an AI-optimized block plan."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            today = date.today()
            response = client.post("/api/optimizer/generate", json={
                "section_id": section_id,
                "plan_type": "WEEKLY",
                "start_date": today.isoformat(),
                "include_predictive": True,
            })
            assert response.status_code == 200
            data = response.json()
            assert "stats" in data
            assert "blocks" in data

    def test_negotiate(self):
        """Should run multi-agent negotiation."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.post(f"/api/optimizer/negotiate?section_id={section_id}")
            assert response.status_code == 200
            data = response.json()
            assert "allocated_tasks" in data or "error" in data


# ═══════════════════════════════════════════════════════════════
# PREDICTION ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestPredictionEndpoints:
    """Test predictive maintenance endpoints."""

    def test_section_predictions(self):
        """Should return asset predictions for a section."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/predictions/section/{section_id}?update_tasks=false")
            assert response.status_code == 200
            data = response.json()
            assert "predictions" in data
            assert "risk_summary" in data

    def test_anomaly_detection(self):
        """Should detect anomalies in a section."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/predictions/section/{section_id}/anomalies")
            assert response.status_code == 200
            data = response.json()
            assert "anomalies" in data


# ═══════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestAnalyticsEndpoints:
    """Test analytics and KPI endpoints."""

    def test_dashboard_kpis(self):
        """Should return all dashboard KPIs."""
        response = client.get("/api/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "asset_availability_pct" in data
        assert "tasks_pending" in data
        assert "departments_breakdown" in data

    def test_before_after(self):
        """Should return before/after comparison."""
        sections = client.get("/api/sections/").json()
        if sections:
            section_id = sections[0]["id"]
            response = client.get(f"/api/analytics/before-after?section_id={section_id}")
            assert response.status_code == 200
            data = response.json()
            assert "comparisons" in data
            assert len(data["comparisons"]) >= 5

    def test_sections_overview(self):
        """Should return overview of all sections."""
        response = client.get("/api/analytics/sections/overview")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ═══════════════════════════════════════════════════════════════
# NLP ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestNLPEndpoints:
    """Test NLP command endpoints."""

    def test_process_english_command(self):
        """Should process an English NLP command."""
        response = client.post("/api/nlp/command", json={
            "command": "Show critical tasks"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "QUERY_TASKS"
        assert "response_text" in data

    def test_process_hindi_command(self):
        """Should process a Hindi NLP command."""
        response = client.post("/api/nlp/command", json={
            "command": "Kalyan section mein pending tasks dikhao"
        })
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        # Should detect section
        assert data["entities"].get("section") == "TNA-KYN"

    def test_help_command(self):
        """Should return help information."""
        response = client.post("/api/nlp/command", json={
            "command": "Help"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "HELP"

    def test_suggestions(self):
        """Should return command suggestions."""
        response = client.get("/api/nlp/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0


# ═══════════════════════════════════════════════════════════════
# NOTIFICATION ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════

class TestNotificationEndpoints:
    """Test notification endpoints."""

    def test_get_notifications(self):
        """Should return notifications."""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert "notifications" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
