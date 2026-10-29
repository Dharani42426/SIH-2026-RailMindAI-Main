"""
═══════════════════════════════════════════════════════════════
RailMind AI — CriticalityScorer Test Suite
Tests XGBoost/GBR criticality scoring model
═══════════════════════════════════════════════════════════════
"""
import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.maintenance_task import MaintenanceTask


class TestCriticalityScorer:
    """Test the XGBoost/GBR CriticalityScorer service."""

    @classmethod
    def setup_class(cls):
        """Initialize DB and scorer."""
        create_all_tables()
        cls.db = SessionLocal()
        cls.section = cls.db.query(RailwaySection).first()

    @classmethod
    def teardown_class(cls):
        cls.db.close()

    def _get_scorer(self):
        from services.criticality_scorer import CriticalityScorer
        return CriticalityScorer()

    def _get_integrator(self):
        from services.data_integrator import DataIntegrator
        return DataIntegrator(self.db)

    # ─── Model Loading/Training ───

    def test_model_loads_or_trains(self):
        """Model should either load from disk or train successfully."""
        scorer = self._get_scorer()
        assert scorer.model is not None, "Model failed to load or train"

    def test_model_is_gradient_boosting(self):
        """Should use GradientBoostingRegressor."""
        scorer = self._get_scorer()
        model_type = type(scorer.model).__name__
        assert "GradientBoosting" in model_type, f"Expected GradientBoosting, got {model_type}"

    # ─── Feature Importance ───

    def test_feature_importance_available(self):
        """Should return feature importance rankings."""
        scorer = self._get_scorer()
        importances = scorer.get_feature_importance()

        assert len(importances) > 0, "No feature importances returned"
        assert len(importances) == 15, f"Expected 15 features, got {len(importances)}"

    def test_feature_importance_structure(self):
        """Each importance entry should have feature name and importance value."""
        scorer = self._get_scorer()
        importances = scorer.get_feature_importance()

        for fi in importances:
            assert "feature" in fi, "Missing 'feature' key"
            assert "importance" in fi, "Missing 'importance' key"
            assert isinstance(fi["importance"], float)
            assert fi["importance"] >= 0

    def test_feature_importance_sums_to_one(self):
        """Feature importances should sum to approximately 1.0."""
        scorer = self._get_scorer()
        importances = scorer.get_feature_importance()
        total = sum(fi["importance"] for fi in importances)
        assert abs(total - 1.0) < 0.01, f"Importances sum to {total}, expected ~1.0"

    def test_severity_is_top_feature(self):
        """Severity should be among the top 5 most important features."""
        scorer = self._get_scorer()
        importances = scorer.get_feature_importance()
        top_5_features = [fi["feature"] for fi in importances[:5]]
        assert "severity_encoded" in top_5_features, (
            f"'severity_encoded' not in top 5: {top_5_features}"
        )

    # ─── Single Prediction ───

    def test_predict_single_task(self):
        """Should predict a score for a single task."""
        if not self.section:
            pytest.skip("No sections in database")

        scorer = self._get_scorer()
        integrator = self._get_integrator()

        tasks = integrator.get_pending_tasks(self.section.id)
        if not tasks:
            pytest.skip("No pending tasks")

        features = integrator.enrich_task_features(tasks[0])
        score = scorer.predict_score(features)

        assert isinstance(score, float)
        assert 0 <= score <= 100, f"Score {score} out of range [0, 100]"

    def test_predict_with_synthetic_features(self):
        """Should handle synthetic feature vectors."""
        scorer = self._get_scorer()

        # High criticality features
        high_features = {
            "severity_encoded": 4,     # CRITICAL
            "days_overdue": 20,
            "days_until_due": -20,
            "traffic_density": 350,
            "safety_impact_score": 10,
            "cascading_risk": 1,
            "speed_restriction_impact": 8,
            "asset_remaining_life": 10,
            "asset_health": 25,
            "weather_risk_factor": 9,
            "last_maintenance_gap": 600,
            "estimated_hours": 3.0,
            "is_overdue": 1,
            "is_ghat_section": 1,
            "km_range_affected": 3.0,
        }
        high_score = scorer.predict_score(high_features)

        # Low criticality features
        low_features = {
            "severity_encoded": 1,     # LOW
            "days_overdue": 0,
            "days_until_due": 45,
            "traffic_density": 50,
            "safety_impact_score": 1,
            "cascading_risk": 0,
            "speed_restriction_impact": 0,
            "asset_remaining_life": 90,
            "asset_health": 95,
            "weather_risk_factor": 3,
            "last_maintenance_gap": 30,
            "estimated_hours": 1.0,
            "is_overdue": 0,
            "is_ghat_section": 0,
            "km_range_affected": 0.5,
        }
        low_score = scorer.predict_score(low_features)

        assert high_score > low_score, (
            f"CRITICAL score ({high_score}) should be > LOW score ({low_score})"
        )

    # ─── Batch Scoring ───

    def test_score_all_tasks(self):
        """Should score all pending tasks for a section."""
        if not self.section:
            pytest.skip("No sections in database")

        scorer = self._get_scorer()
        scored = scorer.score_all_tasks(self.db, self.section.id, update_db=False)

        assert len(scored) >= 0, "Should return a list (may be empty)"

        if scored:
            # Check structure
            assert "task" in scored[0]
            assert "score" in scored[0]
            assert "rank" in scored[0]

            # Check all scores are valid
            for s in scored:
                assert 0 <= s["score"] <= 100, f"Score {s['score']} out of range"

    def test_scores_are_ranked(self):
        """Scored tasks should be in descending order."""
        if not self.section:
            pytest.skip("No sections in database")

        scorer = self._get_scorer()
        scored = scorer.score_all_tasks(self.db, self.section.id, update_db=False)

        if len(scored) >= 2:
            scores = [s["score"] for s in scored]
            assert scores == sorted(scores, reverse=True), "Scores not properly ranked"

    def test_ranks_are_sequential(self):
        """Ranks should be sequential starting from 1."""
        if not self.section:
            pytest.skip("No sections in database")

        scorer = self._get_scorer()
        scored = scorer.score_all_tasks(self.db, self.section.id, update_db=False)

        if scored:
            ranks = [s["rank"] for s in scored]
            expected = list(range(1, len(scored) + 1))
            assert ranks == expected, f"Ranks {ranks} should be {expected}"

    def test_critical_tasks_score_higher_than_low(self):
        """CRITICAL severity tasks should have higher avg score than LOW."""
        if not self.section:
            pytest.skip("No sections in database")

        scorer = self._get_scorer()
        scored = scorer.score_all_tasks(self.db, self.section.id, update_db=False)

        critical_scores = [s["score"] for s in scored if s["task"].severity == "CRITICAL"]
        low_scores = [s["score"] for s in scored if s["task"].severity == "LOW"]

        if critical_scores and low_scores:
            avg_critical = np.mean(critical_scores)
            avg_low = np.mean(low_scores)
            assert avg_critical > avg_low, (
                f"CRITICAL avg ({avg_critical:.1f}) should be > LOW avg ({avg_low:.1f})"
            )

    # ─── Training Data Generation ───

    def test_training_data_generation(self):
        """Should generate valid synthetic training data."""
        scorer = self._get_scorer()
        X, y = scorer._generate_training_data(n_samples=100)

        assert X.shape == (100, 15), f"Expected shape (100, 15), got {X.shape}"
        assert y.shape == (100,), f"Expected shape (100,), got {y.shape}"
        assert np.all(y >= 0), "All labels should be >= 0"
        assert np.all(y <= 100), "All labels should be <= 100"

    def test_criticality_labels_formula(self):
        """Domain formula should produce valid criticality scores."""
        scorer = self._get_scorer()
        X, y = scorer._generate_training_data(n_samples=500)

        # Check distribution
        assert np.mean(y) > 20, f"Mean score {np.mean(y):.1f} is too low"
        assert np.mean(y) < 80, f"Mean score {np.mean(y):.1f} is too high"
        assert np.std(y) > 5, f"Std dev {np.std(y):.1f} is too low (no variation)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
