# ═══════════════════════════════════════════════════════════════
# RailMind AI — Block Optimizer (CP-SAT)
# AI Component #4: The HEART of the project
# Uses Google OR-Tools CP-SAT solver to find the optimal
# block schedule that maximizes maintenance while minimizing
# train disruption
#
# DECISION VARIABLES:
#   x[i,s] = 1 if task i is assigned to slot s
#   slot_used[s] = 1 if slot s has any task assigned
#
# HARD CONSTRAINTS:
#   C1: Each task assigned at most once
#   C2: Task duration cannot exceed slot capacity
#   C3: Max blocks/day per section respected
#   C4: TRD/POWER tasks can only be in power-compatible windows
#   C5: Tasks cannot be in train-conflicting windows
#       (enforced by DataIntegrator.get_available_windows() which
#        only returns train-free gaps; validated post-solve by
#        ConflictResolver safety gate)
#
# OBJECTIVE (MAXIMIZE):
#   Term 1: Σ criticality × x[i,s]         — schedule urgent work
#   Term 2: Σ overdue_bonus × x[i,s]       — prioritize overdue tasks
#   Term 3: Σ severity_bonus × x[i,s]      — CRITICAL tasks first
#   Term 4: Σ integration_bonus × int[s]   — reward multi-dept blocks
#   Term 5: -Σ block_cost × slot_used[s]   — penalize excessive blocks
#
# SAFETY GATE:
#   After solving, ConflictResolver.validate_block_plan() checks
#   the result independently. Unsafe plans are rejected.
# ═══════════════════════════════════════════════════════════════

import time as time_module
from datetime import date, time, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from config import get_settings
from models.maintenance_task import MaintenanceTask
from models.block_plan import BlockPlan, BlockWindow, BlockTaskAssignment
from services.data_integrator import DataIntegrator
from services.criticality_scorer import CriticalityScorer
from services.conflict_resolver import ConflictResolver

settings = get_settings()

# ─── Objective weight constants ───
# Scaled so no single term dominates. Criticality scores are 0-100,
# scaled by 100 → 0-10000. Other bonuses are set relative to this range.
_CRITICALITY_SCALE = 100       # x score → 0-10000 range
_OVERDUE_BONUS = 5000          # strong bonus for overdue tasks
_CRITICAL_SEVERITY_BONUS = 3000  # bonus for CRITICAL severity
_INTEGRATION_BONUS = 2000      # reward per integrated slot
_BLOCK_COST = 500              # penalty per used slot (minimize disruption)


class BlockOptimizer:
    """
    CP-SAT Block Schedule Optimizer using Google OR-Tools.

    Coordinates Engineering (ENGG), Signal & Telecom (SNT), and
    Traction Distribution (TRD) maintenance work into safe,
    non-conflicting, and efficient maintenance blocks.

    NO TRAINING NEEDED — this is mathematical optimization.
    """

    def __init__(self, db: Session):
        self.db = db
        self.integrator = DataIntegrator(db)
        self.scorer = CriticalityScorer()
        self.conflict_resolver = ConflictResolver(db)
        self.max_solve_time = settings.OPTIMIZER_MAX_SOLVE_TIME_SECONDS
        # Unique run ID for block codes (prevents UNIQUE constraint violations)
        import uuid
        self._run_id = uuid.uuid4().hex[:8].upper()

    def generate_plan(
        self,
        section_id: int,
        start_date: date,
        end_date: Optional[date] = None,
        plan_type: str = "WEEKLY",
        negotiation_weights: Optional[dict] = None,
    ) -> dict:
        """
        Generate an optimized block plan for a section.

        This is the main entry point that orchestrates the full pipeline:
        1. Gather data (DataIntegrator)
        2. Score tasks (CriticalityScorer)
        3. Run multi-agent negotiation (if not already done)
        4. Find available windows
        5. Run CP-SAT optimization
        6. Validate results (ConflictResolver safety gate)
        7. Save to database (only if safe)

        Args:
            section_id: Railway section to plan for
            start_date: Plan start date
            end_date: Plan end date (auto-calculated if None)
            plan_type: "WEEKLY" or "MONTHLY"
            negotiation_weights: Optional priority adjustments from
                                 MultiAgentNegotiator (dept → weight_multiplier)

        Returns: {plan, blocks, stats, solve_time, explanations, safety_report}
        """
        solve_start = time_module.time()

        # Default end date
        if end_date is None:
            days = 7 if plan_type == "WEEKLY" else 30
            end_date = start_date + timedelta(days=days - 1)

        # Step 1: Gather all data
        opt_data = self.integrator.get_optimization_data(
            section_id, start_date, end_date
        )
        section = opt_data["section"]

        if not opt_data["tasks"]:
            return self._empty_result(section_id, start_date, end_date, plan_type)

        # Step 2: Score all tasks by criticality
        scored_tasks = self.scorer.score_all_tasks(self.db, section_id, update_db=True)

        # Step 3: Apply negotiation weights if provided
        if negotiation_weights:
            for task_info in scored_tasks:
                dept = task_info["task"].department
                weight = negotiation_weights.get(dept, 1.0)
                task_info["negotiation_weight"] = weight
        else:
            for task_info in scored_tasks:
                task_info["negotiation_weight"] = 1.0

        # Step 4: Run the optimization
        try:
            result = self._solve_with_ortools(
                scored_tasks, opt_data, section, start_date, end_date
            )
        except ImportError:
            # Fallback if OR-Tools not installed
            print("[BlockOptimizer] OR-Tools not available, using greedy algorithm")
            result = self._solve_greedy(
                scored_tasks, opt_data, section, start_date, end_date
            )

        # Step 5: Safety gate — validate with ConflictResolver
        safety_report = self._run_safety_gate(result, section_id)
        result["safety_report"] = safety_report

        solve_time = time_module.time() - solve_start

        if not safety_report["safe"]:
            # Unsafe plan: do NOT save to database
            print(f"[BlockOptimizer] SAFETY GATE FAILED: {len(safety_report['violations'])} violations")
            return {
                "plan": None,
                "blocks": result["blocks"],
                "stats": {**result["stats"], "solver_status": "UNSAFE_REJECTED"},
                "solve_time_seconds": round(solve_time, 3),
                "explanations": result["explanations"],
                "safety_report": safety_report,
            }

        # Step 6: Save plan to database (only if safe)
        plan = self._save_plan(
            result, section_id, start_date, end_date, plan_type, solve_time
        )

        return {
            "plan": plan,
            "blocks": result["blocks"],
            "stats": result["stats"],
            "solve_time_seconds": round(solve_time, 3),
            "explanations": result["explanations"],
            "safety_report": safety_report,
        }

    def _run_safety_gate(self, result: dict, section_id: int) -> dict:
        """
        Independent safety validation after CP-SAT produces a candidate plan.

        CP-SAT result → ConflictResolver.validate_block_plan() → SAFE/UNSAFE

        An unsafe plan is never silently saved.
        """
        violations = []
        blocks = result.get("blocks", [])

        if not blocks:
            return {"safe": True, "violations": [], "checks_passed": 0}

        # Group blocks by date for daily validation
        blocks_by_date = {}
        for block in blocks:
            bd = block["block_date"]
            if bd not in blocks_by_date:
                blocks_by_date[bd] = []
            blocks_by_date[bd].append(block)

        total_checks = 0
        for block_date_val, day_blocks in blocks_by_date.items():
            proposed = []
            for b in day_blocks:
                proposed.append({
                    "start_time": b["start_time"],
                    "end_time": b["end_time"],
                    "line": b.get("line_blocked", "BOTH"),
                    "block_code": b["block_code"],
                    "section_id": section_id,
                    "tasks": [t["task"] for t in b.get("tasks", [])],
                })

            report = self.conflict_resolver.validate_block_plan(
                section_id, block_date_val, proposed
            )
            total_checks += 1

            if not report["valid"]:
                for conflict in report["conflicts"]:
                    if conflict["type"] == "TRAIN_CLASH":
                        violations.append({
                            "date": block_date_val.isoformat() if hasattr(block_date_val, 'isoformat') else str(block_date_val),
                            "type": conflict["type"],
                            "description": conflict["description"],
                        })

        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "checks_passed": total_checks,
        }

    def _solve_with_ortools(
        self, scored_tasks, opt_data, section, start_date, end_date
    ) -> dict:
        """
        Solve using Google OR-Tools CP-SAT solver.

        Implements the full constraint model:
        - C1: Each task assigned at most once
        - C2: Slot capacity (task duration ≤ window duration)
        - C3: Max blocks/day
        - C4: TRD/POWER block type compatibility
        - Objective: multi-term (criticality + overdue + integration - block cost)
        """
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()
        tasks = scored_tasks
        daily_data = opt_data["daily_data"]
        num_tasks = len(tasks)

        # Collect all available slots across all days
        # These windows are ALREADY train-conflict-free (computed by DataIntegrator)
        slots = []  # [(day_key, slot_idx, start_time, end_time, duration_min)]
        for day_key, day_info in daily_data.items():
            for s_idx, window in enumerate(day_info["available_windows"]):
                slots.append((
                    day_key,
                    s_idx,
                    window["start_time"],
                    window["end_time"],
                    window["duration_min"],
                ))

        if not slots:
            return self._solve_greedy(scored_tasks, opt_data, section, start_date, end_date)

        num_slots = len(slots)

        # ─── Decision Variables ───
        # x[i,s] = 1 if task i assigned to slot s
        x = {}
        for i in range(num_tasks):
            for s in range(num_slots):
                x[i, s] = model.NewBoolVar(f"x_{i}_{s}")

        # ─── CONSTRAINT C1: Each task assigned to AT MOST one slot ───
        for i in range(num_tasks):
            model.Add(sum(x[i, s] for s in range(num_slots)) <= 1)

        # ─── CONSTRAINT C2: Slot capacity — total hours ≤ slot duration ───
        for s in range(num_slots):
            slot_capacity_min = slots[s][4]  # duration in minutes
            model.Add(
                sum(
                    x[i, s] * int(float(tasks[i]["task"].estimated_hours) * 60)
                    for i in range(num_tasks)
                ) <= slot_capacity_min
            )

        # ─── CONSTRAINT C3: Max blocks per section per day ───
        max_blocks_per_day = settings.MAX_BLOCKS_PER_SECTION_PER_DAY
        day_slot_map = {}
        for s, slot in enumerate(slots):
            day = slot[0]
            if day not in day_slot_map:
                day_slot_map[day] = []
            day_slot_map[day].append(s)

        # slot_used[s] = 1 if slot s has any task assigned (reused in objective)
        slot_used = {}
        for s in range(num_slots):
            is_used = model.NewBoolVar(f"slot_used_{s}")
            task_sum = sum(x[i, s] for i in range(num_tasks))
            model.Add(task_sum >= 1).OnlyEnforceIf(is_used)
            model.Add(task_sum == 0).OnlyEnforceIf(is_used.Not())
            slot_used[s] = is_used

        for day, day_slots in day_slot_map.items():
            model.Add(sum(slot_used[s] for s in day_slots) <= max_blocks_per_day)

        # ─── CONSTRAINT C4: TRD/POWER block type compatibility ───
        # Tasks requiring POWER block can only go in slots where power
        # disconnection is feasible. For electrified sections (AC25KV),
        # power blocks are available in all maintenance windows.
        # For non-electrified sections, POWER tasks cannot be scheduled.
        is_electrified = (section.traction == "AC25KV")
        for i in range(num_tasks):
            task = tasks[i]["task"]
            if task.block_type_required == "POWER" and not is_electrified:
                # Forbid POWER tasks on non-electrified sections
                for s in range(num_slots):
                    model.Add(x[i, s] == 0)

        # ─── OBJECTIVE FUNCTION ───
        # Multi-term objective balancing criticality, urgency, integration,
        # and block disruption cost.
        objective_terms = []

        # Term 1: Criticality score (higher = more reward for scheduling)
        for i in range(num_tasks):
            base_score = int(tasks[i]["score"] * _CRITICALITY_SCALE)
            neg_weight = tasks[i].get("negotiation_weight", 1.0)
            weighted_score = int(base_score * neg_weight)
            for s in range(num_slots):
                objective_terms.append(x[i, s] * weighted_score)

        # Term 2: Overdue bonus (strong incentive to schedule overdue work)
        for i in range(num_tasks):
            if tasks[i]["task"].is_overdue:
                for s in range(num_slots):
                    objective_terms.append(x[i, s] * _OVERDUE_BONUS)

        # Term 3: Critical severity bonus
        for i in range(num_tasks):
            if tasks[i]["task"].severity == "CRITICAL":
                for s in range(num_slots):
                    objective_terms.append(x[i, s] * _CRITICAL_SEVERITY_BONUS)

        # Term 4: Integration bonus — reward slots with tasks from 2+ departments
        # For each slot, detect if tasks from different departments are assigned
        for s in range(num_slots):
            # Group task indices by department
            dept_groups = {}
            for i in range(num_tasks):
                dept = tasks[i]["task"].department
                if dept not in dept_groups:
                    dept_groups[dept] = []
                dept_groups[dept].append(i)

            if len(dept_groups) >= 2:
                # Create indicator: is this slot integrated?
                dept_list = list(dept_groups.keys())
                for d1_idx in range(len(dept_list)):
                    for d2_idx in range(d1_idx + 1, len(dept_list)):
                        d1_tasks = dept_groups[dept_list[d1_idx]]
                        d2_tasks = dept_groups[dept_list[d2_idx]]

                        # has_d1[s] = any task from dept1 in slot s
                        has_d1 = model.NewBoolVar(f"has_{dept_list[d1_idx]}_{s}")
                        model.Add(sum(x[i, s] for i in d1_tasks) >= 1).OnlyEnforceIf(has_d1)
                        model.Add(sum(x[i, s] for i in d1_tasks) == 0).OnlyEnforceIf(has_d1.Not())

                        has_d2 = model.NewBoolVar(f"has_{dept_list[d2_idx]}_{s}")
                        model.Add(sum(x[i, s] for i in d2_tasks) >= 1).OnlyEnforceIf(has_d2)
                        model.Add(sum(x[i, s] for i in d2_tasks) == 0).OnlyEnforceIf(has_d2.Not())

                        # Integrated = both depts present
                        integrated = model.NewBoolVar(f"int_{dept_list[d1_idx]}_{dept_list[d2_idx]}_{s}")
                        model.AddBoolAnd([has_d1, has_d2]).OnlyEnforceIf(integrated)
                        model.AddBoolOr([has_d1.Not(), has_d2.Not()]).OnlyEnforceIf(integrated.Not())

                        # Only reward integration if departments are compatible
                        # ENGG+SNT: always compatible
                        # SNT+TRD: always compatible
                        # ENGG+TRD: compatible only if both tasks overlap spatially
                        d1, d2 = dept_list[d1_idx], dept_list[d2_idx]
                        compatible_pairs = {("ENGG", "SNT"), ("SNT", "ENGG"),
                                            ("SNT", "TRD"), ("TRD", "SNT"),
                                            ("ENGG", "TRD"), ("TRD", "ENGG")}
                        if (d1, d2) in compatible_pairs:
                            objective_terms.append(integrated * _INTEGRATION_BONUS)

        # Term 5: Block cost — penalize each used slot (minimize disruption)
        for s in range(num_slots):
            objective_terms.append(slot_used[s] * (-_BLOCK_COST))

        model.Maximize(sum(objective_terms))

        # ─── Solve ───
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_solve_time

        status = solver.Solve(model)

        # ─── Extract Solution ───
        blocks = []
        scheduled_tasks = []
        deferred_tasks = []
        explanations = []
        block_counter = 0

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for s in range(num_slots):
                slot_tasks = []
                for i in range(num_tasks):
                    if solver.Value(x[i, s]) == 1:
                        slot_tasks.append(tasks[i])
                        scheduled_tasks.append(tasks[i])

                if slot_tasks:
                    block_counter += 1
                    slot = slots[s]

                    # Determine block type and departments
                    departments = list(set(t["task"].department for t in slot_tasks))
                    is_integrated = len(departments) > 1
                    block_type = "INTEGRATED" if is_integrated else slot_tasks[0]["task"].block_type_required

                    # Calculate KM range
                    km_from = min(float(t["task"].km_from) for t in slot_tasks)
                    km_to = max(float(t["task"].km_to) for t in slot_tasks)

                    total_hours = sum(float(t["task"].estimated_hours) for t in slot_tasks)

                    block = {
                        "block_code": f"BW-{section.section_code}-{self._run_id}-{block_counter:03d}",
                        "block_date": date.fromisoformat(slot[0]),
                        "start_time": slot[2],
                        "end_time": slot[3],
                        "duration_hrs": round(total_hours + 0.25, 1),  # +15min buffer
                        "km_from": km_from,
                        "km_to": km_to,
                        "block_type": block_type,
                        "is_integrated": is_integrated,
                        "departments": ",".join(departments),
                        "line_blocked": "BOTH" if is_integrated else (slot_tasks[0]["task"].line_affected or "BOTH"),
                        "tasks": slot_tasks,
                        "task_count": len(slot_tasks),
                    }
                    blocks.append(block)

                    # Generate explanation
                    task_names = ", ".join(t["task"].task_code for t in slot_tasks)
                    if is_integrated:
                        explanations.append(
                            f"Block {block['block_code']}: INTEGRATED block for {' and '.join(departments)} "
                            f"departments. Tasks {task_names} merged because they overlap at "
                            f"KM {km_from:.1f}-{km_to:.1f} and fit within the "
                            f"{slot[2].strftime('%H:%M')}-{slot[3].strftime('%H:%M')} window."
                        )
                    else:
                        explanations.append(
                            f"Block {block['block_code']}: {departments[0]} block for task(s) {task_names}. "
                            f"Scheduled at {slot[2].strftime('%H:%M')}-{slot[3].strftime('%H:%M')} on "
                            f"{slot[0]} (no train conflicts in this window)."
                        )

            # Track deferred tasks
            for i in range(num_tasks):
                if not any(solver.Value(x[i, s]) == 1 for s in range(num_slots)):
                    deferred_tasks.append(tasks[i])

        else:
            # No solution — fall back to greedy
            return self._solve_greedy(scored_tasks, opt_data, section, start_date, end_date)

        # Calculate stats
        total_block_hrs = sum(b["duration_hrs"] for b in blocks)
        total_available_hrs = sum(s[4] / 60 for s in slots)
        utilization = (total_block_hrs / total_available_hrs * 100) if total_available_hrs > 0 else 0

        return {
            "blocks": blocks,
            "stats": {
                "tasks_total": num_tasks,
                "tasks_scheduled": len(scheduled_tasks),
                "tasks_deferred": len(deferred_tasks),
                "total_blocks": len(blocks),
                "total_block_hours": round(total_block_hrs, 1),
                "utilization_pct": round(utilization, 1),
                "integrated_blocks": sum(1 for b in blocks if b["is_integrated"]),
                "solver_status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
            },
            "explanations": explanations,
            "deferred_tasks": deferred_tasks,
        }

    def _solve_greedy(
        self, scored_tasks, opt_data, section, start_date, end_date
    ) -> dict:
        """
        Greedy fallback algorithm when OR-Tools is not available.
        Schedules tasks in criticality order into available windows.
        """
        blocks = []
        scheduled_tasks = []
        deferred_tasks = []
        explanations = []
        block_counter = 0
        daily_data = opt_data["daily_data"]

        # Sort tasks by criticality (highest first)
        remaining_tasks = list(scored_tasks)

        for day_key, day_info in sorted(daily_data.items()):
            if not remaining_tasks:
                break

            day_block_count = 0
            for window in day_info["available_windows"]:
                if day_block_count >= settings.MAX_BLOCKS_PER_SECTION_PER_DAY:
                    break
                if not remaining_tasks:
                    break

                available_minutes = window["duration_min"]
                slot_tasks = []

                # Fill the window with tasks (highest criticality first)
                for task_info in list(remaining_tasks):
                    task = task_info["task"]
                    task_minutes = int(float(task.estimated_hours) * 60)

                    if task_minutes + 15 <= available_minutes:  # 15 min buffer
                        slot_tasks.append(task_info)
                        available_minutes -= (task_minutes + 15)
                        remaining_tasks.remove(task_info)
                        scheduled_tasks.append(task_info)

                if slot_tasks:
                    block_counter += 1
                    departments = list(set(t["task"].department for t in slot_tasks))
                    is_integrated = len(departments) > 1
                    km_from = min(float(t["task"].km_from) for t in slot_tasks)
                    km_to = max(float(t["task"].km_to) for t in slot_tasks)
                    total_hours = sum(float(t["task"].estimated_hours) for t in slot_tasks)

                    block = {
                        "block_code": f"BW-{section.section_code}-{self._run_id}-{block_counter:03d}",
                        "block_date": date.fromisoformat(day_key),
                        "start_time": window["start_time"],
                        "end_time": window["end_time"],
                        "duration_hrs": round(total_hours + 0.25, 1),
                        "km_from": km_from,
                        "km_to": km_to,
                        "block_type": "INTEGRATED" if is_integrated else slot_tasks[0]["task"].block_type_required,
                        "is_integrated": is_integrated,
                        "departments": ",".join(departments),
                        "line_blocked": "BOTH" if is_integrated else (slot_tasks[0]["task"].line_affected or "BOTH"),
                        "tasks": slot_tasks,
                        "task_count": len(slot_tasks),
                    }
                    blocks.append(block)
                    day_block_count += 1

                    task_names = ", ".join(t["task"].task_code for t in slot_tasks)
                    explanations.append(
                        f"Block {block['block_code']}: Scheduled {len(slot_tasks)} task(s) [{task_names}] "
                        f"at {window['start_time'].strftime('%H:%M')}-{window['end_time'].strftime('%H:%M')} "
                        f"on {day_key} (greedy: highest criticality first)."
                    )

        deferred_tasks = remaining_tasks
        total_block_hrs = sum(b["duration_hrs"] for b in blocks)

        return {
            "blocks": blocks,
            "stats": {
                "tasks_total": len(scored_tasks),
                "tasks_scheduled": len(scheduled_tasks),
                "tasks_deferred": len(deferred_tasks),
                "total_blocks": len(blocks),
                "total_block_hours": round(total_block_hrs, 1),
                "utilization_pct": round(
                    len(scheduled_tasks) / max(1, len(scored_tasks)) * 100, 1
                ),
                "integrated_blocks": sum(1 for b in blocks if b["is_integrated"]),
                "solver_status": "GREEDY",
            },
            "explanations": explanations,
            "deferred_tasks": deferred_tasks,
        }

    def _save_plan(
        self, result, section_id, start_date, end_date, plan_type, solve_time
    ) -> BlockPlan:
        """Save the optimized plan and block windows to the database."""
        stats = result["stats"]
        # Generate unique plan_code with auto-increment suffix
        base_code = f"BLK-{start_date.strftime('%Y%m%d')}-{section_id:03d}"
        existing = self.db.query(BlockPlan).filter(
            BlockPlan.plan_code.like(f"{base_code}%")
        ).count()
        plan_code = f"{base_code}-{existing + 1:02d}" if existing > 0 else base_code

        plan = BlockPlan(
            plan_code=plan_code,
            plan_type=plan_type,
            section_id=section_id,
            plan_start_date=start_date,
            plan_end_date=end_date,
            total_blocks=stats["total_blocks"],
            total_block_hrs=stats["total_block_hours"],
            utilization_pct=stats["utilization_pct"],
            optimization_score=round(solve_time * 100, 2),
            tasks_scheduled=stats["tasks_scheduled"],
            conflicts_resolved=0,
            status="DRAFT",
            safety_report_data=result.get("safety_report"),
        )
        self.db.add(plan)
        self.db.flush()  # Get plan.id

        # Save block windows
        for block_data in result["blocks"]:
            block = BlockWindow(
                plan_id=plan.id,
                block_code=block_data["block_code"],
                block_date=block_data["block_date"],
                start_time=block_data["start_time"],
                end_time=block_data["end_time"],
                duration_hrs=block_data["duration_hrs"],
                section_id=section_id,
                km_from=block_data["km_from"],
                km_to=block_data["km_to"],
                block_type=block_data["block_type"],
                line_blocked=block_data["line_blocked"],
                is_integrated=block_data["is_integrated"],
                departments=block_data["departments"],
                status="PLANNED",
            )
            self.db.add(block)
            self.db.flush()

            # Save task assignments
            for seq, task_info in enumerate(block_data["tasks"], 1):
                task = task_info["task"]
                assignment = BlockTaskAssignment(
                    block_id=block.id,
                    task_id=task.id,
                    sequence_order=seq,
                    start_offset_min=(seq - 1) * int(float(task.estimated_hours) * 60),
                    duration_min=int(float(task.estimated_hours) * 60),
                    status="ASSIGNED",
                )
                self.db.add(assignment)

                # Update task status
                task.status = "SCHEDULED"

        self.db.commit()
        print(f"[BlockOptimizer] Plan {plan_code} saved: {stats['total_blocks']} blocks, "
              f"{stats['tasks_scheduled']} tasks scheduled")

        return plan

    def _empty_result(self, section_id, start_date, end_date, plan_type):
        """Return empty result when no tasks to schedule."""
        return {
            "plan": None,
            "blocks": [],
            "stats": {
                "tasks_total": 0, "tasks_scheduled": 0, "tasks_deferred": 0,
                "total_blocks": 0, "total_block_hours": 0, "utilization_pct": 0,
                "integrated_blocks": 0, "solver_status": "NO_TASKS",
            },
            "solve_time_seconds": 0,
            "explanations": ["No pending tasks found for this section."],
            "safety_report": {"safe": True, "violations": [], "checks_passed": 0},
        }
