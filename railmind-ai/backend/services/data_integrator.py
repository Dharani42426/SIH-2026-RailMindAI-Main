# ═══════════════════════════════════════════════════════════════
# RailMind AI — Data Integrator Service
# Merges data from TMS + SMMS + TDMS + COA into unified format
# This is STEP 1 in the AI pipeline
# ═══════════════════════════════════════════════════════════════

from sqlalchemy.orm import Session
from datetime import date, time, timedelta
from typing import Optional

from models.corridor import RailwaySection
from models.asset import RailwayAsset
from models.maintenance_task import MaintenanceTask
from models.train_schedule import TrainSchedule


class DataIntegrator:
    """
    Aggregates and merges data from all 4 source systems into a unified
    format ready for AI processing.

    Pipeline: DataIntegrator → CriticalityScorer → ConflictResolver
              → MultiAgent → BlockOptimizer

    This service provides:
    1. Unified task list with enriched features for ML
    2. Train conflict windows for a section
    3. Available corridor windows (gaps between trains)
    4. Asset health summary for predictive maintenance
    """

    def __init__(self, db: Session):
        self.db = db

    def get_section_by_id(self, section_id: int) -> Optional[RailwaySection]:
        """Get a railway section by ID."""
        return self.db.query(RailwaySection).filter_by(id=section_id).first()

    def get_section_by_code(self, code: str) -> Optional[RailwaySection]:
        """Get a railway section by code (e.g., 'KYN-KAS')."""
        return self.db.query(RailwaySection).filter_by(section_code=code).first()

    # ─── Task Aggregation ───

    def get_pending_tasks(
        self,
        section_id: int,
        include_overdue: bool = True,
        department: Optional[str] = None,
    ) -> list[MaintenanceTask]:
        """
        Get all pending maintenance tasks for a section.
        Optionally filter by department (ENGG/SNT/TRD).
        """
        query = self.db.query(MaintenanceTask).filter(
            MaintenanceTask.section_id == section_id,
            MaintenanceTask.status.in_(["PENDING", "SCHEDULED"]),
        )

        if not include_overdue:
            query = query.filter(MaintenanceTask.is_overdue == False)

        if department:
            query = query.filter(MaintenanceTask.department == department)

        return query.order_by(
            MaintenanceTask.severity.desc(),
            MaintenanceTask.due_date.asc(),
        ).all()

    def get_tasks_by_department(self, section_id: int) -> dict[str, list[MaintenanceTask]]:
        """
        Group pending tasks by department for multi-agent negotiation.
        Returns: {"ENGG": [...], "SNT": [...], "TRD": [...]}
        """
        tasks = self.get_pending_tasks(section_id)
        grouped = {"ENGG": [], "SNT": [], "TRD": []}
        for task in tasks:
            if task.department in grouped:
                grouped[task.department].append(task)
        return grouped

    def enrich_task_features(self, task: MaintenanceTask) -> dict:
        """
        Extract ML features from a maintenance task for the XGBoost model.
        Returns a feature dictionary ready for model input.
        """
        section = self.get_section_by_id(task.section_id)
        today = date.today()
        days_until_due = (task.due_date - today).days
        days_since_detected = (today - task.detected_date).days

        # Safety impact based on task type
        safety_impact_map = {
            "Rail Fracture Repair": 10,
            "Retaining Wall Repair": 9,
            "Catch Siding Inspection": 9,
            "Bridge Inspection & Repair": 8,
            "Embankment Stabilization": 8,
            "Point & Crossing Renewal": 8,
            "Level Crossing Gate Signal Repair": 9,
            "OHE Wire Replacement": 8,
            "Weld Repair": 7,
            "Point Machine Overhaul": 7,
            "Color Light Signal Lamp Replacement": 7,
            "Gauge Correction": 7,
            "Mast Foundation Repair": 7,
            "Insulator Replacement": 6,
            "Track Tamping": 5,
            "Turnout Maintenance": 6,
            "Rail Renewal": 5,
            "Track Circuit Cable Replacement": 6,
            "Booster Transformer Maintenance": 5,
            "Axle Counter Calibration": 5,
            "Sleeper Replacement": 4,
            "Ballast Cleaning": 4,
            "Drainage Repair": 4,
            "Track Realignment": 4,
            "Rail Grinding": 3,
            "Level Crossing Maintenance": 3,
            "Tunnel Inspection": 4,
            "Platform Edge Repair": 2,
            "Fish Plate Tightening": 3,
            "CCTV Camera Installation": 1,
            "Data Logger Repair": 2,
        }

        # Cascading risk: if failure could affect other assets
        cascading_types = {
            "Rail Fracture Repair", "Point & Crossing Renewal", "OHE Wire Replacement",
            "Bridge Inspection & Repair", "Mast Foundation Repair", "Retaining Wall Repair",
            "Embankment Stabilization", "Track Circuit Cable Replacement",
        }

        # Get asset health if linked
        asset_health = 100.0
        asset_age_years = 5.0
        if task.asset_id:
            asset = self.db.query(RailwayAsset).filter_by(id=task.asset_id).first()
            if asset:
                asset_health = float(asset.health_score) if asset.health_score else 100.0
                if asset.install_date:
                    asset_age_years = (today - asset.install_date).days / 365.25

        features = {
            "severity_encoded": task.severity_numeric,
            "days_overdue": max(0, -days_until_due),
            "days_until_due": days_until_due,
            "days_since_detected": days_since_detected,
            "traffic_density": section.trains_per_day if section else 100,
            "safety_impact_score": safety_impact_map.get(task.task_type, 5),
            "cascading_risk": 1 if task.task_type in cascading_types else 0,
            "speed_restriction_impact": (
                (110 - task.speed_restriction) / 110 * 10 if task.speed_restriction else 0
            ),
            "historical_failure_rate": min(10, days_since_detected / 30),
            "asset_remaining_life": max(0, 100 - (asset_age_years / 25 * 100)),
            "asset_health": asset_health,
            "weather_risk_factor": 7 if section and section.is_ghat_section else 3,
            "last_maintenance_gap": 180,  # Default; enriched from asset data
            "estimated_hours": float(task.estimated_hours),
            "is_overdue": 1 if task.is_overdue else 0,
            "is_ghat_section": 1 if section and section.is_ghat_section else 0,
            "km_range_affected": task.affected_km_range,
        }

        # Update maintenance gap from asset
        if task.asset_id:
            asset = self.db.query(RailwayAsset).filter_by(id=task.asset_id).first()
            if asset and asset.last_maintained:
                features["last_maintenance_gap"] = (today - asset.last_maintained).days

        return features

    # ─── Train Schedule Analysis ───

    def get_train_windows(
        self,
        section_id: int,
        target_date: date,
        direction: Optional[str] = None,
    ) -> list[dict]:
        """
        Get all train windows (occupied times) for a section on a given date.
        Returns list of {"train_no", "train_name", "priority", "entry_time",
                         "exit_time", "direction"} sorted by entry_time.
        """
        day_name = target_date.strftime("%A")[:3].upper()

        query = self.db.query(TrainSchedule).filter(
            TrainSchedule.section_id == section_id,
        )

        if direction:
            query = query.filter(TrainSchedule.direction == direction)

        all_trains = query.order_by(TrainSchedule.entry_time).all()

        # Filter by day of run
        active_trains = []
        for train in all_trains:
            if train.runs_on_day(day_name):
                active_trains.append({
                    "train_id": train.id,
                    "train_no": train.train_no,
                    "train_name": train.train_name,
                    "priority": train.priority,
                    "entry_time": train.entry_time,
                    "exit_time": train.exit_time,
                    "direction": train.direction,
                    "avg_delay": train.avg_delay_min,
                    "is_high_priority": train.is_high_priority,
                })

        return active_trains

    def get_available_windows(
        self,
        section_id: int,
        target_date: date,
        min_duration_minutes: int = 60,
        corridor_start: time = time(10, 0),
        corridor_end: time = time(16, 0),
    ) -> list[dict]:
        """
        Find available time windows for block scheduling on a section.

        Looks for gaps between trains within the corridor availability window.
        Default corridor: 10:00 - 16:00 (typical Indian Railways block window).

        Returns list of {"start_time", "end_time", "duration_min", "conflicting_trains"}
        """
        trains = self.get_train_windows(section_id, target_date)

        # Filter trains within corridor window
        corridor_trains = []
        for t in trains:
            # Check if train passes through corridor window
            if t["exit_time"] >= corridor_start and t["entry_time"] <= corridor_end:
                # Add delay buffer
                buffer = timedelta(minutes=max(5, t["avg_delay"]))
                corridor_trains.append(t)

        # Sort by entry time
        corridor_trains.sort(key=lambda x: x["entry_time"])

        # Find gaps
        windows = []
        current_start = corridor_start

        for train in corridor_trains:
            train_start = train["entry_time"]
            # Buffer: add avg_delay + 5 min safety margin before train
            buffer_minutes = train["avg_delay"] + 5

            if train_start > current_start:
                gap_start = current_start
                gap_end = train_start
                duration = (
                    (gap_end.hour * 60 + gap_end.minute) -
                    (gap_start.hour * 60 + gap_start.minute) -
                    buffer_minutes
                )
                if duration >= min_duration_minutes:
                    windows.append({
                        "start_time": gap_start,
                        "end_time": gap_end,
                        "duration_min": duration,
                        "conflicting_trains": [],
                    })

            # Move current_start past the train (with buffer after)
            train_end_minutes = train["exit_time"].hour * 60 + train["exit_time"].minute
            buffer_after = 10  # 10 min buffer after train passes
            new_start_minutes = train_end_minutes + buffer_after
            new_start = time(
                min(23, new_start_minutes // 60),
                new_start_minutes % 60
            )
            if new_start > current_start:
                current_start = new_start

        # Check gap after last train until corridor end
        if current_start < corridor_end:
            duration = (
                (corridor_end.hour * 60 + corridor_end.minute) -
                (current_start.hour * 60 + current_start.minute)
            )
            if duration >= min_duration_minutes:
                windows.append({
                    "start_time": current_start,
                    "end_time": corridor_end,
                    "duration_min": duration,
                    "conflicting_trains": [],
                })

        return windows

    # ─── Asset Health Summary ───

    def get_asset_health_summary(self, section_id: int) -> dict:
        """
        Get asset health summary for a section.
        Used by the predictive maintenance engine and dashboard.
        """
        assets = self.db.query(RailwayAsset).filter_by(section_id=section_id).all()

        if not assets:
            return {"total": 0, "avg_health": 0, "critical": 0, "degraded": 0}

        total = len(assets)
        health_scores = [float(a.health_score) for a in assets if a.health_score]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0

        by_status = {}
        by_type = {}
        for a in assets:
            by_status[a.status] = by_status.get(a.status, 0) + 1
            by_type[a.asset_type] = by_type.get(a.asset_type, 0) + 1

        return {
            "total": total,
            "avg_health": round(avg_health, 2),
            "critical": sum(1 for a in assets if a.is_critical),
            "by_status": by_status,
            "by_type": by_type,
            "lowest_health_assets": sorted(
                [{"code": a.asset_code, "health": float(a.health_score), "type": a.asset_type}
                 for a in assets if a.health_score],
                key=lambda x: x["health"]
            )[:10],
        }

    # ─── Full Pipeline Data Package ───

    def get_optimization_data(
        self,
        section_id: int,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Assemble the complete data package needed by the block optimizer.

        Returns everything the MILP solver needs:
        - Ranked tasks with criticality features
        - Train windows for each day
        - Available corridor windows for each day
        - Asset health data
        - Section metadata
        """
        section = self.get_section_by_id(section_id)
        if not section:
            raise ValueError(f"Section ID {section_id} not found")

        # Get and enrich all pending tasks
        tasks = self.get_pending_tasks(section_id)
        enriched_tasks = []
        for task in tasks:
            features = self.enrich_task_features(task)
            enriched_tasks.append({
                "task": task,
                "features": features,
            })

        # Get train windows and available slots for each day
        daily_data = {}
        current = start_date
        while current <= end_date:
            train_windows = self.get_train_windows(section_id, current)
            available_windows = self.get_available_windows(section_id, current)
            daily_data[current.isoformat()] = {
                "date": current,
                "day_name": current.strftime("%A"),
                "trains": train_windows,
                "available_windows": available_windows,
                "is_sunday": current.weekday() == 6,
            }
            current += timedelta(days=1)

        # Asset health
        asset_health = self.get_asset_health_summary(section_id)

        return {
            "section": section,
            "tasks": enriched_tasks,
            "task_count": len(enriched_tasks),
            "daily_data": daily_data,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": (end_date - start_date).days + 1,
            },
            "asset_health": asset_health,
            "departments": self.get_tasks_by_department(section_id),
        }
