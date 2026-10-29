# ═══════════════════════════════════════════════════════════════
# RailMind AI — Anomaly Detector (Isolation Forest)
# AI Component #7: Detects unusual maintenance patterns
# ═══════════════════════════════════════════════════════════════

import numpy as np
import os
import joblib
from typing import Optional
from sqlalchemy.orm import Session

from config import get_settings
from models.maintenance_task import MaintenanceTask
from models.asset import RailwayAsset
from services.data_integrator import DataIntegrator

settings = get_settings()


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detection for maintenance patterns.

    WHAT IT DETECTS:
    - Unusually frequent defects on the same asset
    - Sudden health score drops
    - Abnormal maintenance request patterns
    - Suspect speed restriction patterns

    HOW IT WORKS:
    - Isolation Forest isolates anomalies by randomly partitioning data
    - Anomalies are isolated in fewer partitions (short path length)
    - No labeled data needed (unsupervised learning)
    """

    def __init__(self):
        self.model = None
        self.model_path = settings.ANOMALY_MODEL_PATH
        self._load_or_train()

    def _load_or_train(self):
        """Load existing model or train a new one."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("[AnomalyDetector] Loaded existing model")
                return
            except Exception:
                pass

        self._train_model()

    def _train_model(self):
        """Train Isolation Forest on synthetic normal patterns."""
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            print("[AnomalyDetector] scikit-learn not available")
            self.model = None
            return

        # Generate synthetic "normal" maintenance patterns
        np.random.seed(42)
        n_normal = 500

        # Features: [defect_frequency, health_drop_rate, days_between_defects,
        #            speed_restriction_count, km_range, severity_avg]
        X_normal = np.column_stack([
            np.random.exponential(2, n_normal),          # defect_frequency (per month)
            np.random.normal(3, 1.5, n_normal),           # health_drop_rate (%/month)
            np.random.exponential(45, n_normal),           # days_between_defects
            np.random.poisson(1, n_normal),                # speed_restriction_count
            np.random.uniform(0.5, 3.0, n_normal),        # km_range
            np.random.uniform(1.5, 3.0, n_normal),        # severity_avg (1-4)
        ])

        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
        )
        self.model.fit(X_normal)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print("[AnomalyDetector] Model trained and saved")

    def detect_anomalies(
        self, db: Session, section_id: int
    ) -> list[dict]:
        """
        Detect anomalous maintenance patterns for a section.
        Returns list of anomaly reports.
        """
        if self.model is None:
            return []

        integrator = DataIntegrator(db)
        tasks = integrator.get_pending_tasks(section_id)
        assets = db.query(RailwayAsset).filter_by(section_id=section_id).all()

        anomalies = []

        # Group tasks by asset to compute patterns
        asset_tasks = {}
        for task in tasks:
            key = task.asset_id or f"km_{task.km_from}"
            if key not in asset_tasks:
                asset_tasks[key] = []
            asset_tasks[key].append(task)

        for asset_key, task_group in asset_tasks.items():
            if len(task_group) < 1:
                continue

            # Extract features
            features = self._extract_pattern_features(task_group)
            feature_vector = np.array([features])

            # Predict (-1 = anomaly, 1 = normal)
            prediction = self.model.predict(feature_vector)[0]
            anomaly_score = self.model.decision_function(feature_vector)[0]

            if prediction == -1:
                # This pattern is anomalous
                anomalies.append({
                    "asset_key": str(asset_key),
                    "task_codes": [t.task_code for t in task_group],
                    "anomaly_score": round(float(anomaly_score), 4),
                    "pattern_features": {
                        "defect_frequency": features[0],
                        "health_drop_rate": features[1],
                        "days_between_defects": features[2],
                        "speed_restrictions": features[3],
                    },
                    "description": self._generate_anomaly_description(features, task_group),
                    "severity": "HIGH" if anomaly_score < -0.3 else "MEDIUM",
                })

        # Sort by anomaly score (most anomalous first)
        anomalies.sort(key=lambda a: a["anomaly_score"])
        return anomalies

    def _extract_pattern_features(self, tasks: list[MaintenanceTask]) -> list[float]:
        """Extract 6 features from a group of tasks for anomaly detection."""
        from datetime import date
        today = date.today()

        defect_freq = len(tasks)
        severities = [t.severity_numeric for t in tasks]
        severity_avg = np.mean(severities) if severities else 2.0

        # Calculate days between defects
        dates = sorted([t.detected_date for t in tasks if t.detected_date])
        if len(dates) >= 2:
            gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_gap = np.mean(gaps)
        else:
            avg_gap = 45.0

        speed_restrictions = sum(1 for t in tasks if t.speed_restriction)
        km_range = max(
            float(t.km_to) - float(t.km_from)
            for t in tasks
        ) if tasks else 1.0

        health_drop = defect_freq * severity_avg * 0.5  # Estimated

        return [defect_freq, health_drop, avg_gap, speed_restrictions, km_range, severity_avg]

    def _generate_anomaly_description(
        self, features: list[float], tasks: list[MaintenanceTask]
    ) -> str:
        """Generate human-readable anomaly description."""
        descriptions = []

        if features[0] > 3:
            descriptions.append(
                f"Unusually high defect frequency ({features[0]:.0f} defects)")

        if features[2] < 15:
            descriptions.append(
                f"Defects recurring very quickly (every {features[2]:.0f} days)")

        if features[3] >= 2:
            descriptions.append(
                f"Multiple speed restrictions ({int(features[3])}) in same area")

        if features[5] >= 3.5:
            descriptions.append("Consistently high severity defects")

        if not descriptions:
            descriptions.append("Unusual maintenance pattern detected")

        task_area = tasks[0].task_code.split("-")[1] if tasks else "Unknown"
        return f"ANOMALY at {task_area}: " + "; ".join(descriptions)
