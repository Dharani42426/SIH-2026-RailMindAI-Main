"""
═══════════════════════════════════════════════════════════════
RailMind AI — Approval Safety Gate Test Suite
Tests the safety validation during plan approval.
═══════════════════════════════════════════════════════════════
"""
import os
import sys
import pytest
from datetime import date, time, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.block_plan import BlockPlan, BlockWindow
from models.train_schedule import TrainSchedule
import uuid

client = TestClient(app)

class TestApprovalSafety:
    @classmethod
    def setup_class(cls):
        create_all_tables()
        cls.db = SessionLocal()
        
        # Ensure we have a section
        cls.section = cls.db.query(RailwaySection).first()
        if not cls.section:
            cls.section = RailwaySection(
                section_code="TEST-SEC", section_name="Test Section",
                division="MUM", zone="CR", km_start=0.0, km_end=100.0
            )
            cls.db.add(cls.section)
            cls.db.commit()

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def _create_mock_plan(self, status="DRAFT"):
        """Creates a mock block plan and returns it."""
        unique_id = str(uuid.uuid4())[:8]
        plan = BlockPlan(
            plan_code=f"TEST-PLAN-{unique_id}",
            plan_type="WEEKLY",
            section_id=self.section.id,
            plan_start_date=date.today(),
            plan_end_date=date.today() + timedelta(days=6),
            status=status
        )
        self.db.add(plan)
        self.db.commit()
        return plan

    def _create_mock_block(self, plan_id, start_hr, end_hr):
        unique_id = str(uuid.uuid4())[:8]
        block = BlockWindow(
            plan_id=plan_id,
            block_code=f"TEST-BLK-{unique_id}",
            block_date=date.today(),
            start_time=time(start_hr, 0),
            end_time=time(end_hr, 0),
            duration_hrs=end_hr - start_hr,
            section_id=self.section.id,
            km_from=10.0,
            km_to=20.0,
            block_type="TRAFFIC",
            line_blocked="BOTH"
        )
        self.db.add(block)
        self.db.commit()
        return block

    def _create_mock_train(self, entry_hr, exit_hr):
        unique_id = str(uuid.uuid4())[:4]
        train = TrainSchedule(
            train_no=f"TRN{unique_id}",
            train_name="Test Express",
            train_type="EXPRESS",
            priority=1,
            section_id=self.section.id,
            direction="UP",
            entry_km=0.0,
            exit_km=100.0,
            entry_time=time(entry_hr, 0),
            exit_time=time(exit_hr, 0)
        )
        self.db.add(train)
        self.db.commit()
        return train

    def test_already_approved_cannot_approve_again(self):
        plan = self._create_mock_plan(status="APPROVED")
        response = client.post(f"/api/optimizer/plans/{plan.id}/approve?approved_by=TestUser")
        assert response.status_code == 400
        assert "Plan is already APPROVED" in response.json()["detail"]

    def test_rejected_cannot_approve(self):
        plan = self._create_mock_plan(status="REJECTED")
        response = client.post(f"/api/optimizer/plans/{plan.id}/approve?approved_by=TestUser")
        assert response.status_code == 400
        assert "Plan is already REJECTED" in response.json()["detail"]

    def test_safe_draft_approval_succeeds(self):
        plan = self._create_mock_plan(status="DRAFT")
        self._create_mock_block(plan.id, 10, 12)
        
        # Ensure no conflicting train exists
        # We don't add a train in 10-12
        
        response = client.post(f"/api/optimizer/plans/{plan.id}/approve?approved_by=TestUser")
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"
        
        self.db.refresh(plan)
        assert plan.status == "APPROVED"
        assert plan.approved_by == "TestUser"
        assert plan.approved_at is not None

    def test_unsafe_draft_approval_blocked(self):
        plan = self._create_mock_plan(status="DRAFT")
        # Block from 14:00 to 16:00
        self._create_mock_block(plan.id, 14, 16)
        
        # Conflicting train passes from 14:30 to 15:30
        train = self._create_mock_train(14, 15) # entry 14:00, exit 15:00
        
        response = client.post(f"/api/optimizer/plans/{plan.id}/approve?approved_by=TestUser")
        
        # Should be blocked
        assert response.status_code == 409
        
        data = response.json()
        assert data["status"] == "BLOCKED"
        assert data["safety_report"]["safe"] is False
        assert len(data["safety_report"]["violations"]) > 0
        
        self.db.refresh(plan)
        assert plan.status == "REJECTED"
        assert plan.rejection_reason == "Safety re-validation failed during approval."

        # cleanup train
        self.db.delete(train)
        self.db.commit()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
