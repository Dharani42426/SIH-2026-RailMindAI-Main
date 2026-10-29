"""
═══════════════════════════════════════════════════════════════
RailMind AI — BlockOptimizer Test Suite
Tests the MILP/CP-SAT block optimization pipeline
═══════════════════════════════════════════════════════════════
"""
import os
import sys
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.block_plan import BlockPlan, BlockWindow
from models.maintenance_task import MaintenanceTask


class TestBlockOptimizer:
    """Test the BlockOptimizer (MILP / Greedy) service."""

    @classmethod
    def setup_class(cls):
        """Initialize DB and get test section."""
        create_all_tables()
        cls.db = SessionLocal()
        cls.section = cls.db.query(RailwaySection).first()

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def _get_optimizer(self):
        from services.block_optimizer import BlockOptimizer
        return BlockOptimizer(self.db)

    # ─── Plan Generation ───

    def test_generate_weekly_plan(self):
        """Should generate a weekly block plan."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        today = date.today()

        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=today,
            end_date=today + timedelta(days=6),
            plan_type="WEEKLY",
        )

        assert result is not None
        assert "plan" in result
        assert "blocks" in result
        assert "stats" in result
        assert "solve_time_seconds" in result
        assert "explanations" in result

    def test_plan_stats_structure(self):
        """Stats should have all required fields."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        today = date.today()

        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=today,
            plan_type="WEEKLY",
        )

        stats = result["stats"]
        required_keys = [
            "tasks_total", "tasks_scheduled", "tasks_deferred",
            "total_blocks", "total_block_hours", "utilization_pct",
            "integrated_blocks", "solver_status"
        ]
        for key in required_keys:
            assert key in stats, f"Missing stat: {key}"

    def test_plan_solve_time_reasonable(self):
        """Plan should solve within reasonable time."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        today = date.today()

        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=today,
            plan_type="WEEKLY",
        )

        assert result["solve_time_seconds"] < 30, (
            f"Solve time {result['solve_time_seconds']}s exceeds 30s limit"
        )

    def test_solver_status_valid(self):
        """Solver should return a valid status."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        valid_statuses = {"OPTIMAL", "FEASIBLE", "GREEDY", "NO_TASKS"}
        assert result["stats"]["solver_status"] in valid_statuses, (
            f"Unknown solver status: {result['stats']['solver_status']}"
        )

    # ─── Block Structure ───

    def test_block_structure(self):
        """Each block should have all required fields."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        for block in result["blocks"]:
            assert "block_code" in block
            assert "block_date" in block
            assert "start_time" in block
            assert "end_time" in block
            assert "duration_hrs" in block
            assert "block_type" in block
            assert "is_integrated" in block
            assert "departments" in block
            assert "tasks" in block
            assert "task_count" in block
            assert block["duration_hrs"] > 0

    def test_integrated_blocks_have_multiple_departments(self):
        """Integrated blocks should have tasks from multiple departments."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        for block in result["blocks"]:
            if block["is_integrated"]:
                depts = block["departments"].split(",")
                assert len(depts) >= 2, (
                    f"Integrated block {block['block_code']} has only {len(depts)} department(s)"
                )

    # ─── AI Explanations ───

    def test_explanations_generated(self):
        """Should generate AI explanations for each block."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        if result["blocks"]:
            assert len(result["explanations"]) > 0, "No explanations generated"
            for exp in result["explanations"]:
                assert len(exp) > 20, f"Explanation too short: '{exp}'"

    # ─── Database Persistence ───

    def test_plan_saved_to_database(self):
        """Plan should be saved to the database."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        if result.get("plan"):
            plan = result["plan"]
            assert plan.id is not None, "Plan should have an ID"
            assert plan.plan_code is not None, "Plan should have a code"
            assert plan.status == "DRAFT", f"New plan should be DRAFT, got {plan.status}"

            # Verify it exists in DB
            db_plan = self.db.query(BlockPlan).filter_by(id=plan.id).first()
            assert db_plan is not None, "Plan not found in database"

    def test_block_windows_saved(self):
        """Block windows should be saved to the database."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        if result.get("plan"):
            windows = self.db.query(BlockWindow).filter_by(
                plan_id=result["plan"].id
            ).all()
            assert len(windows) == len(result["blocks"]), (
                f"DB has {len(windows)} windows but result has {len(result['blocks'])} blocks"
            )

    def test_scheduled_tasks_updated(self):
        """Scheduled tasks should have status = SCHEDULED."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=date.today(),
            plan_type="WEEKLY",
        )

        for block in result["blocks"]:
            for task_info in block["tasks"]:
                task = task_info["task"]
                assert task.status == "SCHEDULED", (
                    f"Task {task.task_code} should be SCHEDULED, got {task.status}"
                )

    # ─── Edge Cases ───

    def test_empty_section_handling(self):
        """Should handle sections with no pending tasks gracefully."""
        optimizer = self._get_optimizer()

        # Use a non-existent section ID (or one with no tasks)
        result = optimizer._empty_result(
            section_id=99999,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            plan_type="WEEKLY",
        )

        assert result["plan"] is None
        assert result["blocks"] == []
        assert result["stats"]["tasks_total"] == 0
        assert result["stats"]["solver_status"] == "NO_TASKS"

    def test_default_end_date_weekly(self):
        """Should auto-calculate end date for weekly plans."""
        if not self.section:
            pytest.skip("No sections in database")

        optimizer = self._get_optimizer()
        today = date.today()

        result = optimizer.generate_plan(
            section_id=self.section.id,
            start_date=today,
            plan_type="WEEKLY",
            # end_date not provided — should auto-calculate
        )

        assert result is not None

    # ─── Greedy Fallback ───

    def test_greedy_fallback_works(self):
        """Greedy algorithm should produce valid results."""
        if not self.section:
            pytest.skip("No sections in database")

        from services.criticality_scorer import CriticalityScorer
        from services.data_integrator import DataIntegrator

        optimizer = self._get_optimizer()
        integrator = DataIntegrator(self.db)
        scorer = CriticalityScorer()

        today = date.today()
        end_date = today + timedelta(days=6)

        scored_tasks = scorer.score_all_tasks(self.db, self.section.id, update_db=False)
        opt_data = integrator.get_optimization_data(self.section.id, today, end_date)

        if scored_tasks and opt_data["tasks"]:
            result = optimizer._solve_greedy(
                scored_tasks, opt_data, self.section, today, end_date
            )

            assert "blocks" in result
            assert "stats" in result
            assert result["stats"]["solver_status"] == "GREEDY"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
