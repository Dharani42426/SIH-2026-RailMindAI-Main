# ═══════════════════════════════════════════════════════════════
# RailMind AI — Criticality Scorer (XGBoost)
# AI Component #2: Classical ML model that ranks maintenance
# tasks by urgency (0-100 criticality score)
# STEP 2 in the AI pipeline
# ═══════════════════════════════════════════════════════════════

import numpy as np
import os
import joblib
from typing import Optional
from sqlalchemy.orm import Session

from config import get_settings
from models.maintenance_task import MaintenanceTask
from services.data_integrator import DataIntegrator

settings = get_settings()

# Feature names used by the model (must match training order)
FEATURE_NAMES = [
    "severity_encoded",
    "days_overdue",
    "days_until_due",
    "traffic_density",
    "safety_impact_score",
    "cascading_risk",
    "speed_restriction_impact",
    "asset_remaining_life",
    "asset_health",
    "weather_risk_factor",
    "last_maintenance_gap",
    "estimated_hours",
    "is_overdue",
    "is_ghat_section",
    "km_range_affected",
]


class CriticalityScorer:
    """
    XGBoost-based criticality scoring model for maintenance tasks.

    WHAT IT DOES:
    - Takes 15 features from each maintenance task
    - Predicts a criticality score from 0-100
    - Higher score = more urgent = schedule first

    HOW IT WORKS:
    - Uses a Gradient Boosted Decision Tree (XGBoost)
    - Trained on synthetic labeled data (generated from domain rules)
    - Features include: severity, overdue days, traffic density,
      safety impact, cascading risk, asset health, weather risk

    TRAINING APPROACH:
    Since we don't have real labeled data, we use a domain-expert
    rule-based formula to generate training labels, then train
    XGBoost to learn the pattern. This is valid because:
    1. The model can generalize to unseen combinations
    2. It's faster than computing rules at inference time
    3. It can be retrained on real data when available
    """

    def __init__(self):
        self.model = None
        self.model_path = settings.CRITICALITY_MODEL_PATH
        self._load_or_train()

    def _load_or_train(self):
        """Load existing model or train a new one."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("[CriticalityScorer] Loaded existing model")
                return
            except Exception as e:
                print(f"[CriticalityScorer] Error loading model: {e}")

        print("[CriticalityScorer] Training new model...")
        self._train_model()

    def _generate_training_data(self, n_samples: int = 2000) -> tuple:
        """
        Generate synthetic training data using domain-expert rules.
        Returns (X, y) where X is features and y is criticality scores.
        """
        np.random.seed(42)
        X = np.zeros((n_samples, len(FEATURE_NAMES)))

        for i in range(n_samples):
            X[i, 0] = np.random.choice([1, 2, 3, 4])           # severity_encoded
            X[i, 1] = np.random.exponential(10)                  # days_overdue (0+)
            X[i, 2] = np.random.randint(-30, 60)                 # days_until_due
            X[i, 3] = np.random.randint(30, 400)                 # traffic_density
            X[i, 4] = np.random.randint(1, 11)                   # safety_impact_score
            X[i, 5] = np.random.choice([0, 1], p=[0.6, 0.4])    # cascading_risk
            X[i, 6] = np.random.uniform(0, 10)                   # speed_restriction_impact
            X[i, 7] = np.random.uniform(0, 100)                  # asset_remaining_life
            X[i, 8] = np.random.uniform(10, 100)                 # asset_health
            X[i, 9] = np.random.choice([3, 5, 7, 9])             # weather_risk_factor
            X[i, 10] = np.random.randint(30, 730)                # last_maintenance_gap
            X[i, 11] = np.random.uniform(0.5, 8.0)              # estimated_hours
            X[i, 12] = np.random.choice([0, 1], p=[0.7, 0.3])   # is_overdue
            X[i, 13] = np.random.choice([0, 1], p=[0.7, 0.3])   # is_ghat_section
            X[i, 14] = np.random.uniform(0.5, 5.0)              # km_range_affected

        # Generate labels using domain-expert weighted formula
        y = self._compute_criticality_labels(X)

        return X, y

    def _compute_criticality_labels(self, X: np.ndarray) -> np.ndarray:
        """
        Domain-expert formula to compute criticality scores.
        This encodes railway engineering knowledge:
        - Critical severity + overdue = highest score
        - High traffic + safety impact = elevated score
        - Ghat section + monsoon = additional risk
        """
        scores = np.zeros(X.shape[0])

        # Weighted components (total weights = ~100)
        scores += X[:, 0] * 12          # severity (4 * 12 = 48 max)
        scores += np.clip(X[:, 1], 0, 30) * 0.8  # days_overdue (24 max)
        scores += np.clip(-X[:, 2], -10, 30) * 0.3  # urgency from due date
        scores += X[:, 3] / 400 * 8     # traffic_density normalized (8 max)
        scores += X[:, 4] * 2.5         # safety_impact (25 max)
        scores += X[:, 5] * 8           # cascading_risk (8 max)
        scores += X[:, 6] * 1.5         # speed_restriction (15 max)
        scores += (100 - X[:, 7]) / 100 * 5  # inverse asset life (5 max)
        scores += (100 - X[:, 8]) / 100 * 5  # inverse asset health (5 max)
        scores += X[:, 9] / 9 * 4       # weather_risk (4 max)
        scores += np.clip(X[:, 10], 0, 365) / 365 * 3  # maintenance_gap (3 max)
        scores += X[:, 12] * 10          # is_overdue bonus (10 max)
        scores += X[:, 13] * 3           # is_ghat_section bonus (3 max)

        # Normalize to 0-100 range
        scores = np.clip(scores, 0, None)
        if scores.max() > 0:
            scores = scores / scores.max() * 100

        # Add slight noise for realism
        noise = np.random.normal(0, 2, scores.shape)
        scores = np.clip(scores + noise, 0, 100)

        return np.round(scores, 2)

    def _train_model(self):
        """Train the XGBoost model on synthetic data."""
        try:
            from xgboost import XGBRegressor
        except ImportError:
            print("[CriticalityScorer] xgboost not available, using rule-based scoring")
            self.model = None
            return

        X, y = self._generate_training_data(n_samples=2000)

        # XGBRegressor — the actual model claimed in the strategy
        self.model = XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            min_child_weight=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        self.model.fit(X, y)

        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"[CriticalityScorer] XGBoost model trained and saved to {self.model_path}")

        # Print feature importances
        importances = sorted(
            zip(FEATURE_NAMES, self.model.feature_importances_),
            key=lambda x: x[1], reverse=True
        )
        print("[CriticalityScorer] Feature importances:")
        for name, imp in importances[:10]:
            print(f"  {name}: {imp:.4f}")

    def predict_score(self, features: dict) -> float:
        """
        Predict criticality score for a single task.

        Args:
            features: Dictionary from DataIntegrator.enrich_task_features()

        Returns:
            Criticality score (0-100). Higher = more critical.
        """
        feature_vector = np.array([
            [features.get(name, 0) for name in FEATURE_NAMES]
        ])

        if self.model is not None:
            score = self.model.predict(feature_vector)[0]
        else:
            # Fallback: rule-based scoring
            score = self._compute_criticality_labels(feature_vector)[0]

        return round(float(np.clip(score, 0, 100)), 2)

    def score_all_tasks(
        self,
        db: Session,
        section_id: int,
        update_db: bool = True,
    ) -> list[dict]:
        """
        Score ALL pending tasks for a section and optionally update the database.

        Returns list of {task, score, rank} sorted by criticality (highest first).
        """
        integrator = DataIntegrator(db)
        tasks = integrator.get_pending_tasks(section_id)

        scored = []
        for task in tasks:
            features = integrator.enrich_task_features(task)
            score = self.predict_score(features)
            scored.append({
                "task": task,
                "score": score,
                "features": features,
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Assign ranks
        for rank, item in enumerate(scored, 1):
            item["rank"] = rank

            # Update database if requested
            if update_db:
                item["task"].criticality_score = item["score"]

        if update_db:
            db.commit()
            print(f"[CriticalityScorer] Updated {len(scored)} tasks in database")

        return scored

    def get_feature_importance(self) -> list[dict]:
        """Get feature importances from the trained model."""
        if self.model is None:
            return []

        return sorted(
            [{"feature": name, "importance": float(imp)}
             for name, imp in zip(FEATURE_NAMES, self.model.feature_importances_)],
            key=lambda x: x["importance"],
            reverse=True
        )
