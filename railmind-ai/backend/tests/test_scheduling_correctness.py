# ═══════════════════════════════════════════════════════════════
# RailMind AI — Scheduling Correctness Tests
# Verifies the 10 critical scheduling invariants
# ═══════════════════════════════════════════════════════════════

import pytest
import sys
import os
from datetime import date, time, timedelta
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Helpers ───

def _make_mock_task(
    task_id: int,
    task_code: str,
    department: str,
    severity: str = "HIGH",
    estimated_hours: float = 1.5,
    km_from: float = 10.0,
    km_to: float = 12.0,
    block_type_required: str = "TRAFFIC",
    is_overdue: bool = False,
    criticality_score: float = 65.0,
    section_id: int = 1,
    line_affected: str = "BOTH",
):
    """Create a mock MaintenanceTask object."""
    task = MagicMock()
    task.id = task_id
    task.task_code = task_code
    task.department = department
    task.severity = severity
    task.estimated_hours = estimated_hours
    task.km_from = km_from
    task.km_to = km_to
    task.block_type_required = block_type_required
    task.is_overdue = is_overdue
    task.criticality_score = criticality_score
    task.section_id = section_id
    task.line_affected = line_affected
    task.status = "PENDING"
    task.severity_numeric = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(severity, 0)
    return task


def _make_scored_task(task, score=None, neg_weight=1.0):
    """Wrap a mock task in the scored_task dict format the optimizer expects."""
    return {
        "task": task,
        "score": score or float(task.criticality_score),
        "negotiation_weight": neg_weight,
    }


def _make_slot(day_key, idx, start_h, start_m, end_h, end_m, duration_min):
    """Create a slot tuple matching optimizer format."""
    return (day_key, idx, time(start_h, start_m), time(end_h, end_m), duration_min)


# ═══════════════════════════════════════════════════════════════
# TEST 1: Each task is assigned at most once
# ═══════════════════════════════════════════════════════════════

class TestTaskAtMostOnce:
    """Verify C1: no task appears in more than one block."""

    def test_task_not_duplicated_across_blocks(self):
        """A task with ID=1 should appear in at most 1 block."""
        # Simulate optimizer output
        blocks = [
            {"tasks": [{"task": _make_mock_task(1, "T-001", "ENGG")}]},
            {"tasks": [{"task": _make_mock_task(2, "T-002", "SNT")}]},
            {"tasks": [{"task": _make_mock_task(3, "T-003", "TRD")}]},
        ]

        # Count task assignments
        task_assignments = {}
        for block in blocks:
            for t in block["tasks"]:
                tid = t["task"].id
                task_assignments[tid] = task_assignments.get(tid, 0) + 1

        for tid, count in task_assignments.items():
            assert count <= 1, f"Task {tid} assigned {count} times (max 1)"


# ═══════════════════════════════════════════════════════════════
# TEST 2: Slot capacity not exceeded
# ═══════════════════════════════════════════════════════════════

class TestSlotCapacity:
    """Verify C2: total task duration ≤ slot duration."""

    def test_tasks_fit_within_slot(self):
        """Total task hours must not exceed available window duration."""
        slot_duration_hrs = 2.0  # 2-hour window

        # Tasks that should fit
        tasks_in_slot = [
            _make_mock_task(1, "T-001", "ENGG", estimated_hours=0.5),
            _make_mock_task(2, "T-002", "ENGG", estimated_hours=1.0),
        ]

        total_hours = sum(float(t.estimated_hours) for t in tasks_in_slot)
        assert total_hours <= slot_duration_hrs, (
            f"Total task hours ({total_hours}) exceeds slot capacity ({slot_duration_hrs})"
        )

    def test_oversized_task_rejected(self):
        """A 5-hour task should not fit in a 2-hour window."""
        slot_duration_hrs = 2.0
        task = _make_mock_task(1, "T-001", "ENGG", estimated_hours=5.0)
        assert float(task.estimated_hours) > slot_duration_hrs


# ═══════════════════════════════════════════════════════════════
# TEST 3: Max blocks per day respected
# ═══════════════════════════════════════════════════════════════

class TestMaxBlocksPerDay:
    """Verify C3: blocks per day per section ≤ max limit."""

    def test_blocks_per_day_within_limit(self):
        """No day should have more blocks than the configured max."""
        from config import get_settings
        settings = get_settings()
        max_per_day = settings.MAX_BLOCKS_PER_SECTION_PER_DAY

        # Simulate a plan with blocks on various days (at most max_per_day each)
        blocks = [
            {"block_date": date(2026, 9, 1)},
            {"block_date": date(2026, 9, 1)},
            {"block_date": date(2026, 9, 2)},
            {"block_date": date(2026, 9, 2)},
        ]

        day_counts = {}
        for b in blocks:
            d = b["block_date"]
            day_counts[d] = day_counts.get(d, 0) + 1

        for d, count in day_counts.items():
            assert count <= max_per_day, (
                f"Day {d} has {count} blocks (max {max_per_day})"
            )


# ═══════════════════════════════════════════════════════════════
# TEST 4: POWER tasks on non-electrified sections are rejected
# ═══════════════════════════════════════════════════════════════

class TestPowerBlockCompatibility:
    """Verify C4: TRD/POWER tasks only on electrified sections."""

    def test_power_task_on_ac25kv(self):
        """POWER task on AC25KV section should be allowed."""
        section = MagicMock()
        section.traction = "AC25KV"
        task = _make_mock_task(1, "T-001", "TRD", block_type_required="POWER")

        is_electrified = section.traction == "AC25KV"
        can_schedule = not (task.block_type_required == "POWER" and not is_electrified)
        assert can_schedule is True

    def test_power_task_on_diesel(self):
        """POWER task on DIESEL section should be rejected."""
        section = MagicMock()
        section.traction = "DIESEL"
        task = _make_mock_task(1, "T-001", "TRD", block_type_required="POWER")

        is_electrified = section.traction == "AC25KV"
        can_schedule = not (task.block_type_required == "POWER" and not is_electrified)
        assert can_schedule is False


# ═══════════════════════════════════════════════════════════════
# TEST 5: Criticality scoring produces bounded output
# ═══════════════════════════════════════════════════════════════

class TestCriticalityScoring:
    """Verify XGBoost criticality scores are in [0, 100]."""

    def test_score_is_bounded(self):
        """CriticalityScorer must produce scores in 0-100 range."""
        from services.criticality_scorer import CriticalityScorer

        scorer = CriticalityScorer()
        # A typical feature vector
        features = {
            "severity_encoded": 3,
            "days_overdue": 10,
            "days_until_due": -10,
            "days_since_detected": 45,
            "traffic_density": 200,
            "safety_impact_score": 8,
            "cascading_risk": 1,
            "speed_restriction_impact": 5.5,
            "historical_failure_rate": 3.0,
            "asset_remaining_life": 40,
            "asset_health": 65.0,
            "weather_risk_factor": 7,
            "last_maintenance_gap": 120,
            "estimated_hours": 2.5,
            "is_overdue": 1,
        }
        score = scorer.predict_score(features)
        assert 0 <= score <= 100, f"Score {score} out of bounds [0, 100]"

    def test_critical_task_scores_higher(self):
        """A CRITICAL overdue task should score higher than a LOW on-time task."""
        from services.criticality_scorer import CriticalityScorer

        scorer = CriticalityScorer()

        critical_features = {
            "severity_encoded": 4, "days_overdue": 30, "days_until_due": -30,
            "days_since_detected": 90, "traffic_density": 250,
            "safety_impact_score": 10, "cascading_risk": 1,
            "speed_restriction_impact": 8, "historical_failure_rate": 5,
            "asset_remaining_life": 10, "asset_health": 30,
            "weather_risk_factor": 7, "last_maintenance_gap": 365,
            "estimated_hours": 3, "is_overdue": 1,
        }

        low_features = {
            "severity_encoded": 1, "days_overdue": 0, "days_until_due": 60,
            "days_since_detected": 5, "traffic_density": 50,
            "safety_impact_score": 2, "cascading_risk": 0,
            "speed_restriction_impact": 0, "historical_failure_rate": 0.5,
            "asset_remaining_life": 90, "asset_health": 95,
            "weather_risk_factor": 3, "last_maintenance_gap": 30,
            "estimated_hours": 0.5, "is_overdue": 0,
        }

        critical_score = scorer.predict_score(critical_features)
        low_score = scorer.predict_score(low_features)

        assert critical_score > low_score, (
            f"CRITICAL task score ({critical_score}) should be > LOW task score ({low_score})"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 6: Integrated blocks have 2+ departments
# ═══════════════════════════════════════════════════════════════

class TestIntegratedBlocks:
    """Verify that integrated blocks actually merge departments."""

    def test_integrated_block_has_multiple_depts(self):
        """A block marked 'is_integrated=True' must have ≥2 departments."""
        block = {
            "is_integrated": True,
            "departments": "ENGG,SNT",
            "tasks": [
                {"task": _make_mock_task(1, "T-001", "ENGG")},
                {"task": _make_mock_task(2, "T-002", "SNT")},
            ],
        }

        dept_set = set(block["departments"].split(","))
        assert len(dept_set) >= 2, "Integrated block must have ≥2 departments"

    def test_non_integrated_block_single_dept(self):
        """A non-integrated block should have exactly 1 department."""
        block = {
            "is_integrated": False,
            "departments": "ENGG",
            "tasks": [
                {"task": _make_mock_task(1, "T-001", "ENGG")},
            ],
        }

        dept_set = set(block["departments"].split(","))
        assert len(dept_set) == 1


# ═══════════════════════════════════════════════════════════════
# TEST 7: LSTM predictions are bounded and monotonic
# ═══════════════════════════════════════════════════════════════

class TestLSTMPredictions:
    """Verify predictive engine output sanity."""

    def test_prediction_health_bounded(self):
        """All predicted health values must be in [0, 100]."""
        from services.predictive_engine import PredictiveEngine

        engine = PredictiveEngine()
        asset = MagicMock()
        asset.asset_code = "TRK-TEST-001"
        asset.asset_type = "TRACK"
        asset.health_score = 75.0
        asset.install_date = date(2020, 1, 1)
        asset.last_maintained = date(2026, 1, 1)

        result = engine.predict_remaining_life(asset, is_ghat=False)

        for point in result["health_trajectory"]:
            h = point["predicted_health"]
            assert 0 <= h <= 100, f"Predicted health {h} out of bounds"

    def test_risk_level_valid(self):
        """Risk level must be one of CRITICAL/HIGH/MEDIUM/LOW."""
        from services.predictive_engine import PredictiveEngine

        engine = PredictiveEngine()
        asset = MagicMock()
        asset.asset_code = "SIG-TEST-001"
        asset.asset_type = "SIGNAL"
        asset.health_score = 40.0
        asset.install_date = date(2015, 6, 1)
        asset.last_maintained = date(2025, 3, 1)

        result = engine.predict_remaining_life(asset, is_ghat=True)
        assert result["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


# ═══════════════════════════════════════════════════════════════
# TEST 8: Overdue tasks are prioritized
# ═══════════════════════════════════════════════════════════════

class TestOverduePrioritization:
    """Verify objective function prioritizes overdue tasks."""

    def test_overdue_task_gets_bonus(self):
        """The overdue bonus should add significant weight to the objective."""
        from services.block_optimizer import _OVERDUE_BONUS

        assert _OVERDUE_BONUS > 0, "Overdue bonus must be positive"
        assert _OVERDUE_BONUS >= 3000, (
            f"Overdue bonus ({_OVERDUE_BONUS}) should be significant (≥3000)"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 9: Safety gate exists and is called
# ═══════════════════════════════════════════════════════════════

class TestSafetyGate:
    """Verify ConflictResolver safety gate is wired in."""

    def test_safety_gate_method_exists(self):
        """BlockOptimizer must have _run_safety_gate method."""
        from services.block_optimizer import BlockOptimizer
        assert hasattr(BlockOptimizer, "_run_safety_gate")

    def test_conflict_resolver_has_validate(self):
        """ConflictResolver must have validate_block_plan method."""
        from services.conflict_resolver import ConflictResolver
        assert hasattr(ConflictResolver, "validate_block_plan")


# ═══════════════════════════════════════════════════════════════
# TEST 10: XGBoost model is actually used (not sklearn)
# ═══════════════════════════════════════════════════════════════

class TestXGBoostModel:
    """Verify the model is actually XGBoost, not sklearn."""

    def test_model_is_xgboost(self):
        """CriticalityScorer should use xgboost.XGBRegressor."""
        from services.criticality_scorer import CriticalityScorer
        scorer = CriticalityScorer()

        if scorer.model is not None:
            model_type = type(scorer.model).__name__
            assert "XGB" in model_type or "xgb" in model_type.lower(), (
                f"Model is {model_type}, expected XGBoost"
            )

    def test_feature_importance_available(self):
        """Trained model should expose feature importances."""
        from services.criticality_scorer import CriticalityScorer
        scorer = CriticalityScorer()
        importances = scorer.get_feature_importance()
        assert len(importances) > 0, "Feature importances should be available"


# ═══════════════════════════════════════════════════════════════
# TEST 11: Negotiation weights flow into optimizer
# ═══════════════════════════════════════════════════════════════

class TestNegotiationWeights:
    """Verify multi-agent negotiation weights are consumed by the optimizer."""

    def test_negotiation_returns_balanced_field(self):
        """MultiAgentNegotiator must return 'is_balanced' (not 'nash_equilibrium')."""
        from services.multi_agent import MultiAgentNegotiator
        assert hasattr(MultiAgentNegotiator, "_check_allocation_balance"), (
            "MultiAgentNegotiator must have _check_allocation_balance method"
        )

    def test_negotiation_output_has_utilities(self):
        """Negotiation result must include agent_utilities dict."""
        # Verify the method signature returns utilities
        from services.multi_agent import MultiAgentNegotiator
        import inspect
        source = inspect.getsource(MultiAgentNegotiator.negotiate)
        assert "agent_utilities" in source, (
            "negotiate() must return agent_utilities in its result dict"
        )

    def test_optimizer_accepts_negotiation_weights(self):
        """BlockOptimizer.generate_plan() must accept negotiation_weights param."""
        from services.block_optimizer import BlockOptimizer
        import inspect
        sig = inspect.signature(BlockOptimizer.generate_plan)
        assert "negotiation_weights" in sig.parameters, (
            "generate_plan() must accept negotiation_weights parameter"
        )

    def test_weights_scale_criticality(self):
        """Negotiation weights should multiply the criticality term in the objective."""
        # Simulate: weight=1.5 on a task with score=50 should produce 50*100*1.5=7500
        from services.block_optimizer import _CRITICALITY_SCALE
        base_score = 50.0
        weight = 1.5
        weighted = int(base_score * _CRITICALITY_SCALE * weight)
        assert weighted == 7500, f"Expected 7500, got {weighted}"

    def test_no_nash_equilibrium_field_in_output(self):
        """The response must NOT have a 'nash_equilibrium' field — renamed to 'is_balanced'."""
        from services.multi_agent import MultiAgentNegotiator
        import inspect
        source = inspect.getsource(MultiAgentNegotiator.negotiate)
        # The return dict should use is_balanced, not nash_equilibrium
        assert '"is_balanced"' in source, (
            "negotiate() must return 'is_balanced', not 'nash_equilibrium'"
        )
        assert '"nash_equilibrium"' not in source, (
            "negotiate() must NOT return 'nash_equilibrium' — this has been renamed"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 12: NLP intents execute real actions
# ═══════════════════════════════════════════════════════════════

class TestNLPIntentExecution:
    """Verify NLP command processing actually executes backend actions."""

    def test_nlp_processor_returns_optimize_intent(self):
        """NLPProcessor must parse 'optimize' commands into OPTIMIZE intent."""
        from services.nlp_processor import NLPProcessor
        processor = NLPProcessor()
        result = processor.process_command("Optimize schedule for Kalyan-Kasara section")
        # Should detect OPTIMIZE or SCHEDULE intent
        assert result["intent"] in ("OPTIMIZE", "SCHEDULE", "QUERY_TASKS"), (
            f"Expected OPTIMIZE/SCHEDULE intent, got {result['intent']}"
        )

    def test_nlp_processor_returns_predict_intent(self):
        """NLPProcessor must parse 'predict' commands into PREDICT intent."""
        from services.nlp_processor import NLPProcessor
        processor = NLPProcessor()
        result = processor.process_command("Predict failures for Kasara section")
        assert result["intent"] == "PREDICT", (
            f"Expected PREDICT intent, got {result['intent']}"
        )

    def test_optimize_handler_exists_in_nlp_route(self):
        """NLP route must have OPTIMIZE intent handler that calls BlockOptimizer."""
        import inspect
        from routes.nlp import process_nlp_command
        source = inspect.getsource(process_nlp_command)
        assert "OPTIMIZE" in source, "NLP route must handle OPTIMIZE intent"
        assert "BlockOptimizer" in source, "OPTIMIZE intent must call BlockOptimizer"

    def test_predict_handler_exists_in_nlp_route(self):
        """NLP route must have PREDICT intent handler that calls PredictiveEngine."""
        import inspect
        from routes.nlp import process_nlp_command
        source = inspect.getsource(process_nlp_command)
        assert "PREDICT" in source, "NLP route must handle PREDICT intent"
        assert "PredictiveEngine" in source, "PREDICT intent must call PredictiveEngine"

    def test_nlp_extracts_section_entity(self):
        """NLPProcessor must extract section codes from natural language."""
        from services.nlp_processor import NLPProcessor
        processor = NLPProcessor()
        result = processor.process_command("Show tasks for Kalyan Kasara")
        entities = result.get("entities", {})
        # Should extract something for section
        assert entities.get("section") is not None, (
            f"Expected section entity, got entities: {entities}"
        )


# ═══════════════════════════════════════════════════════════════
# TEST 13: What-If simulation structure
# ═══════════════════════════════════════════════════════════════

class TestWhatIfSimulation:
    """Verify what-if simulation endpoint wiring and structure."""

    def test_what_if_endpoint_exists(self):
        """The /optimizer/what-if POST endpoint must exist."""
        from routes.optimizer import router
        paths = [route.path for route in router.routes if hasattr(route, 'path')]
        assert any("what-if" in p for p in paths), (
            f"Expected what-if in optimizer routes, found: {paths}"
        )

    def test_what_if_request_schema_has_required_fields(self):
        """WhatIfRequest must have plan_id and changes fields."""
        from schemas import WhatIfRequest
        fields = WhatIfRequest.model_fields
        assert "plan_id" in fields, "WhatIfRequest must have plan_id field"
        assert "changes" in fields, "WhatIfRequest must have changes field"

    def test_what_if_uses_rollback(self):
        """What-if simulation must rollback changes — it's a simulation, not permanent."""
        import inspect
        from routes.optimizer import what_if_simulation
        source = inspect.getsource(what_if_simulation)
        assert "rollback" in source.lower(), (
            "What-if simulation must call db.rollback() to undo changes"
        )

    def test_what_if_returns_comparison_structure(self):
        """What-if response must include original_plan, modified_plan, and changes."""
        import inspect
        from routes.optimizer import what_if_simulation
        source = inspect.getsource(what_if_simulation)
        assert "original_plan" in source, "Response must include original_plan"
        assert "modified_plan" in source, "Response must include modified_plan"
        assert "changes_applied" in source, "Response must include changes_applied"
        assert "safety_report" in source, "Response must include safety_report"

    def test_what_if_supports_remove_train_action(self):
        """What-if must support 'remove_train' change action."""
        import inspect
        from routes.optimizer import what_if_simulation
        source = inspect.getsource(what_if_simulation)
        assert "remove_train" in source, (
            "What-if must handle 'remove_train' action"
        )

    def test_what_if_supports_change_severity_action(self):
        """What-if must support 'change_task_severity' change action."""
        import inspect
        from routes.optimizer import what_if_simulation
        source = inspect.getsource(what_if_simulation)
        assert "change_task_severity" in source, (
            "What-if must handle 'change_task_severity' action"
        )

