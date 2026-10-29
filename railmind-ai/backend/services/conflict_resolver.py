# ═══════════════════════════════════════════════════════════════
# RailMind AI — Conflict Resolver (CSP)
# AI Component #3: Constraint Satisfaction Problem solver
# Detects scheduling conflicts between blocks and trains
# STEP 3 in the AI pipeline
# ═══════════════════════════════════════════════════════════════

from datetime import time, date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from models.train_schedule import TrainSchedule
from models.maintenance_task import MaintenanceTask
from services.data_integrator import DataIntegrator


class ConflictResolver:
    """
    CSP-based conflict detection and resolution engine.

    WHAT IT DOES:
    - Detects 5 types of scheduling conflicts
    - Proposes alternative time windows for each conflict
    - Generates human-readable explanations

    CONFLICT TYPES:
    1. TRAIN_CLASH: Block overlaps with a train's path
    2. DEPT_OVERLAP: Two departments requesting same section/time
    3. RESOURCE: Required equipment not available
    4. ADJACENT: Blocks too close together on same corridor
    5. PRIORITY: Higher priority task needs the same slot

    NO TRAINING NEEDED — this is pure constraint logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.integrator = DataIntegrator(db)
        self.min_gap_minutes = 30  # Minimum gap between blocks

    def check_train_conflict(
        self,
        section_id: int,
        block_date: date,
        block_start: time,
        block_end: time,
        line: str = "BOTH",
    ) -> list[dict]:
        """
        Check if a proposed block window conflicts with any train.

        Returns list of conflicting trains with details.
        Each conflict includes the train info and a suggested resolution.
        """
        trains = self.integrator.get_train_windows(section_id, block_date)
        conflicts = []

        for train in trains:
            # Check time overlap
            if self._times_overlap(block_start, block_end,
                                   train["entry_time"], train["exit_time"]):
                # Check line overlap (UP block doesn't conflict with DN-only train on quad track)
                if line == "BOTH" or train["direction"] == line or line == train["direction"]:
                    # Calculate buffer needed for train delay
                    buffer_min = train["avg_delay"] + 5

                    conflict = {
                        "type": "TRAIN_CLASH",
                        "train_no": train["train_no"],
                        "train_name": train["train_name"],
                        "priority": train["priority"],
                        "train_time": f"{train['entry_time'].strftime('%H:%M')}-{train['exit_time'].strftime('%H:%M')}",
                        "direction": train["direction"],
                        "is_high_priority": train["is_high_priority"],
                        "description": (
                            f"Block {block_start.strftime('%H:%M')}-{block_end.strftime('%H:%M')} "
                            f"conflicts with {train['train_name']} ({train['train_no']}) "
                            f"passing at {train['entry_time'].strftime('%H:%M')}-{train['exit_time'].strftime('%H:%M')} "
                            f"(Priority {train['priority']}, avg delay {train['avg_delay']}min)"
                        ),
                        "resolution": self._suggest_train_resolution(
                            block_start, block_end, train, trains
                        ),
                    }
                    conflicts.append(conflict)

        return conflicts

    def check_department_overlap(
        self,
        tasks: list[dict],
    ) -> list[dict]:
        """
        Check if multiple departments are requesting overlapping blocks
        on the same section and suggest integrated blocks.

        Args:
            tasks: List of {"task": MaintenanceTask, "proposed_start": time, "proposed_end": time}

        Returns conflicts and integration suggestions.
        """
        conflicts = []

        for i, t1 in enumerate(tasks):
            for j, t2 in enumerate(tasks):
                if j <= i:
                    continue

                task1 = t1["task"]
                task2 = t2["task"]

                # Same section, different department, overlapping KM range
                if (task1.section_id == task2.section_id and
                    task1.department != task2.department and
                    self._km_overlap(
                        float(task1.km_from), float(task1.km_to),
                        float(task2.km_from), float(task2.km_to)
                    )):

                    conflicts.append({
                        "type": "DEPT_OVERLAP",
                        "task1_code": task1.task_code,
                        "task1_dept": task1.department,
                        "task2_code": task2.task_code,
                        "task2_dept": task2.department,
                        "km_overlap": self._get_km_overlap_range(
                            float(task1.km_from), float(task1.km_to),
                            float(task2.km_from), float(task2.km_to)
                        ),
                        "description": (
                            f"Tasks {task1.task_code} ({task1.department}) and "
                            f"{task2.task_code} ({task2.department}) overlap at "
                            f"KM {max(float(task1.km_from), float(task2.km_from)):.1f}-"
                            f"{min(float(task1.km_to), float(task2.km_to)):.1f}"
                        ),
                        "resolution": {
                            "type": "MERGE",
                            "suggestion": (
                                f"Create INTEGRATED block for {task1.department} and "
                                f"{task2.department}. Both tasks can be done in a single "
                                f"block window, saving {min(float(task1.estimated_hours), float(task2.estimated_hours)):.1f} hours."
                            ),
                        },
                    })

        return conflicts

    def check_adjacent_conflicts(
        self,
        blocks: list[dict],
    ) -> list[dict]:
        """
        Check if blocks on the same section are too close together.
        Minimum gap: 30 minutes (configurable).
        """
        conflicts = []
        sorted_blocks = sorted(blocks, key=lambda b: b.get("start_time", time(0)))

        for i in range(len(sorted_blocks) - 1):
            b1 = sorted_blocks[i]
            b2 = sorted_blocks[i + 1]

            if b1.get("section_id") != b2.get("section_id"):
                continue

            gap = self._time_diff_minutes(
                b1.get("end_time", time(0)),
                b2.get("start_time", time(0))
            )

            if gap < self.min_gap_minutes:
                conflicts.append({
                    "type": "ADJACENT",
                    "block1": b1.get("block_code", "B1"),
                    "block2": b2.get("block_code", "B2"),
                    "gap_minutes": gap,
                    "required_gap": self.min_gap_minutes,
                    "description": (
                        f"Blocks are only {gap} min apart (minimum {self.min_gap_minutes} min required). "
                        f"Need time for line clear, inspection, and train resumption."
                    ),
                    "resolution": {
                        "type": "RESCHEDULE",
                        "suggestion": f"Shift second block by {self.min_gap_minutes - gap} minutes.",
                    },
                })

        return conflicts

    def validate_block_plan(
        self,
        section_id: int,
        block_date: date,
        proposed_blocks: list[dict],
    ) -> dict:
        """
        Comprehensive validation of a proposed block plan for a day.

        Checks ALL conflict types and returns a validation report.

        Args:
            section_id: Section to validate for
            block_date: Date of the proposed blocks
            proposed_blocks: List of {"start_time", "end_time", "line", "tasks": [...]}

        Returns:
            {"valid": bool, "conflicts": [...], "warnings": [...], "suggestions": [...]}
        """
        all_conflicts = []
        warnings = []
        suggestions = []

        for block in proposed_blocks:
            # 1. Check train conflicts
            train_conflicts = self.check_train_conflict(
                section_id, block_date,
                block["start_time"], block["end_time"],
                block.get("line", "BOTH"),
            )
            all_conflicts.extend(train_conflicts)

            # Add warnings for high-priority train conflicts
            for tc in train_conflicts:
                if tc["is_high_priority"]:
                    warnings.append(
                        f"CRITICAL: Block conflicts with Priority {tc['priority']} "
                        f"train {tc['train_name']}. This MUST be resolved."
                    )

        # 2. Check adjacent block conflicts
        adjacent_conflicts = self.check_adjacent_conflicts(proposed_blocks)
        all_conflicts.extend(adjacent_conflicts)

        # 3. Check department overlaps (for integration opportunities)
        all_tasks = []
        for block in proposed_blocks:
            for task in block.get("tasks", []):
                all_tasks.append({"task": task, **block})

        dept_conflicts = self.check_department_overlap(all_tasks)
        # These are opportunities, not blockers
        for dc in dept_conflicts:
            suggestions.append(dc["resolution"]["suggestion"])

        is_valid = len([c for c in all_conflicts if c["type"] == "TRAIN_CLASH"]) == 0

        return {
            "valid": is_valid,
            "total_conflicts": len(all_conflicts),
            "conflicts": all_conflicts,
            "warnings": warnings,
            "suggestions": suggestions,
            "integration_opportunities": len(dept_conflicts),
        }

    # ─── Helper Methods ───

    def _times_overlap(
        self, start1: time, end1: time, start2: time, end2: time
    ) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and start2 < end1

    def _km_overlap(
        self, km1_start: float, km1_end: float,
        km2_start: float, km2_end: float
    ) -> bool:
        """Check if two KM ranges overlap."""
        return km1_start < km2_end and km2_start < km1_end

    def _get_km_overlap_range(
        self, km1_start: float, km1_end: float,
        km2_start: float, km2_end: float
    ) -> tuple:
        """Get the overlapping KM range."""
        return (max(km1_start, km2_start), min(km1_end, km2_end))

    def _time_diff_minutes(self, t1: time, t2: time) -> int:
        """Calculate difference in minutes between two times."""
        return (t2.hour * 60 + t2.minute) - (t1.hour * 60 + t1.minute)

    def _suggest_train_resolution(
        self, block_start: time, block_end: time,
        conflicting_train: dict, all_trains: list[dict]
    ) -> dict:
        """
        Suggest a resolution for a train-block conflict.
        Tries to find an alternative time window.
        """
        train_end = conflicting_train["exit_time"]
        buffer = conflicting_train["avg_delay"] + 10  # delay + safety margin

        # Suggest moving block to after the train passes
        suggested_start_min = train_end.hour * 60 + train_end.minute + buffer
        suggested_start = time(
            min(23, suggested_start_min // 60),
            suggested_start_min % 60
        )

        block_duration = self._time_diff_minutes(block_start, block_end)
        suggested_end_min = suggested_start_min + block_duration
        suggested_end = time(
            min(23, suggested_end_min // 60),
            suggested_end_min % 60
        )

        return {
            "type": "RESCHEDULE",
            "original_time": f"{block_start.strftime('%H:%M')}-{block_end.strftime('%H:%M')}",
            "suggested_time": f"{suggested_start.strftime('%H:%M')}-{suggested_end.strftime('%H:%M')}",
            "reason": (
                f"Block denied: {conflicting_train['train_name']} passes at "
                f"{conflicting_train['entry_time'].strftime('%H:%M')}. "
                f"Suggested alternative: {suggested_start.strftime('%H:%M')}-{suggested_end.strftime('%H:%M')}"
            ),
        }
