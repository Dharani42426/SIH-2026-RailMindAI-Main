"""
═══════════════════════════════════════════════════════════════
RailMind AI — Conflict Resolver Test Suite
Tests CSP-based conflict detection and resolution
═══════════════════════════════════════════════════════════════
"""
import os
import sys
import pytest
from datetime import date, time, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.maintenance_task import MaintenanceTask


class TestConflictResolver:
    """Test the CSP-based ConflictResolver service."""

    @classmethod
    def setup_class(cls):
        """Initialize DB and get test data."""
        create_all_tables()
        cls.db = SessionLocal()
        cls.section = cls.db.query(RailwaySection).first()

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def _get_resolver(self):
        from services.conflict_resolver import ConflictResolver
        return ConflictResolver(self.db)

    # ─── Train Conflict Detection ───

    def test_train_conflict_check_basic(self):
        """Should detect train conflicts in a broad time window."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()
        conflicts = resolver.check_train_conflict(
            self.section.id,
            date.today(),
            time(6, 0),   # 6 AM
            time(23, 0),   # 11 PM
            "BOTH"
        )
        # Full-day block should conflict with most trains
        assert isinstance(conflicts, list)

    def test_train_conflict_check_narrow_window(self):
        """Should check conflicts in a narrow window."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()
        conflicts = resolver.check_train_conflict(
            self.section.id,
            date.today(),
            time(8, 0),
            time(10, 0),
            "BOTH"
        )
        assert isinstance(conflicts, list)

    def test_conflict_has_required_fields(self):
        """Each conflict should have type, train info, and resolution."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()
        conflicts = resolver.check_train_conflict(
            self.section.id,
            date.today(),
            time(6, 0),
            time(23, 0),
            "BOTH"
        )

        if conflicts:
            c = conflicts[0]
            assert "type" in c, "Missing 'type' field"
            assert c["type"] == "TRAIN_CLASH"
            assert "train_no" in c, "Missing 'train_no'"
            assert "train_name" in c, "Missing 'train_name'"
            assert "priority" in c, "Missing 'priority'"
            assert "description" in c, "Missing 'description'"
            assert "resolution" in c, "Missing 'resolution'"
            assert "type" in c["resolution"]
            assert "suggested_time" in c["resolution"]

    def test_conflict_resolution_suggests_alternative(self):
        """Resolution should suggest an alternative time."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()
        conflicts = resolver.check_train_conflict(
            self.section.id,
            date.today(),
            time(6, 0),
            time(23, 0),
            "BOTH"
        )

        if conflicts:
            resolution = conflicts[0]["resolution"]
            assert resolution["type"] == "RESCHEDULE"
            assert ":" in resolution["suggested_time"]  # Should be HH:MM format
            assert len(resolution["reason"]) > 10  # Should be descriptive

    def test_high_priority_conflict_flag(self):
        """Should flag high-priority train conflicts."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()
        conflicts = resolver.check_train_conflict(
            self.section.id,
            date.today(),
            time(6, 0),
            time(23, 0),
            "BOTH"
        )

        for c in conflicts:
            assert "is_high_priority" in c
            assert isinstance(c["is_high_priority"], bool)

    # ─── Department Overlap Detection ───

    def test_department_overlap_detection(self):
        """Should detect department overlap opportunities."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()
        tasks = self.db.query(MaintenanceTask).filter_by(
            section_id=self.section.id,
        ).limit(10).all()

        if len(tasks) < 2:
            pytest.skip("Not enough tasks for overlap test")

        task_list = [{"task": t} for t in tasks]
        overlaps = resolver.check_department_overlap(task_list)

        assert isinstance(overlaps, list)
        for overlap in overlaps:
            assert overlap["type"] == "DEPT_OVERLAP"
            assert "task1_dept" in overlap
            assert "task2_dept" in overlap
            assert overlap["task1_dept"] != overlap["task2_dept"]
            assert "resolution" in overlap
            assert overlap["resolution"]["type"] == "MERGE"

    # ─── Adjacent Block Checks ───

    def test_adjacent_block_gap_check(self):
        """Should detect blocks that are too close together."""
        resolver = self._get_resolver()

        blocks = [
            {"block_code": "B1", "start_time": time(10, 0), "end_time": time(11, 0), "section_id": 1},
            {"block_code": "B2", "start_time": time(11, 10), "end_time": time(12, 0), "section_id": 1},
        ]

        conflicts = resolver.check_adjacent_conflicts(blocks)
        # 10-minute gap is less than 30-minute minimum
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "ADJACENT"
        assert conflicts[0]["gap_minutes"] < 30

    def test_adjacent_blocks_sufficient_gap(self):
        """Should NOT flag blocks with sufficient gap."""
        resolver = self._get_resolver()

        blocks = [
            {"block_code": "B1", "start_time": time(10, 0), "end_time": time(11, 0), "section_id": 1},
            {"block_code": "B2", "start_time": time(11, 45), "end_time": time(12, 30), "section_id": 1},
        ]

        conflicts = resolver.check_adjacent_conflicts(blocks)
        # 45-minute gap exceeds 30-minute minimum
        assert len(conflicts) == 0

    # ─── Plan Validation ───

    def test_validate_block_plan(self):
        """Should validate a proposed block plan comprehensively."""
        if not self.section:
            pytest.skip("No sections in database")

        resolver = self._get_resolver()

        proposed = [
            {
                "start_time": time(11, 0),
                "end_time": time(13, 0),
                "line": "BOTH",
                "tasks": [],
                "block_code": "TEST-001",
                "section_id": self.section.id,
            }
        ]

        validation = resolver.validate_block_plan(self.section.id, date.today(), proposed)

        assert "valid" in validation
        assert "total_conflicts" in validation
        assert "conflicts" in validation
        assert "warnings" in validation
        assert "suggestions" in validation
        assert isinstance(validation["valid"], bool)
        assert isinstance(validation["total_conflicts"], int)

    # ─── Time Overlap Helper ───

    def test_time_overlap_detection(self):
        """Should correctly detect time overlaps."""
        resolver = self._get_resolver()

        # Overlapping times
        assert resolver._times_overlap(
            time(10, 0), time(12, 0),
            time(11, 0), time(13, 0)
        ) is True

        # Non-overlapping times
        assert resolver._times_overlap(
            time(10, 0), time(11, 0),
            time(12, 0), time(13, 0)
        ) is False

        # Adjacent times (touching but not overlapping)
        assert resolver._times_overlap(
            time(10, 0), time(11, 0),
            time(11, 0), time(12, 0)
        ) is False

    def test_km_overlap_detection(self):
        """Should correctly detect KM range overlaps."""
        resolver = self._get_resolver()

        assert resolver._km_overlap(0, 10, 5, 15) is True   # Overlapping
        assert resolver._km_overlap(0, 10, 10, 20) is False  # Touching
        assert resolver._km_overlap(0, 10, 15, 25) is False  # Separate


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
