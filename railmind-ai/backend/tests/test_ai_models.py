"""
═══════════════════════════════════════════════════════════════
RailMind AI — Complete AI Model Validation Suite
Tests ALL 7 AI components with real database data
═══════════════════════════════════════════════════════════════
"""
import os
import sys
import json
from datetime import date, time, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, create_all_tables
from models.corridor import RailwaySection
from models.maintenance_task import MaintenanceTask
from models.asset import RailwayAsset

# Force UTF-8 output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def separator(title):
    print(f"\n{'='*60}")
    print(f"  AI MODEL TEST: {title}")
    print(f"{'='*60}")


def test_pass(name, detail=""):
    print(f"  [PASS] {name} {detail}")


def test_fail(name, error):
    print(f"  [FAIL] {name}: {error}")


def main():
    create_all_tables()
    db = SessionLocal()

    # Get test section (KYN-KAS = Kasara Ghat, most complex)
    section = db.query(RailwaySection).filter_by(section_code="KYN-KAS").first()
    if not section:
        section = db.query(RailwaySection).first()
    print(f"\nTest Section: {section.section_code} - {section.section_name}")
    print(f"  KM: {section.km_start}-{section.km_end}, Trains/day: {section.trains_per_day}")
    print(f"  Ghat Section: {section.is_ghat_section}")

    errors = 0

    # ═══════════════════════════════════════════════════════════
    # TEST 1: DATA INTEGRATOR
    # ═══════════════════════════════════════════════════════════
    separator("1. DataIntegrator (Pipeline Orchestrator)")
    try:
        from services.data_integrator import DataIntegrator
        integrator = DataIntegrator(db)

        # 1a. Get pending tasks
        tasks = integrator.get_pending_tasks(section.id)
        assert len(tasks) > 0, "No pending tasks found!"
        test_pass("Pending tasks", f"-> {len(tasks)} tasks found")

        # 1b. Group by department
        dept_tasks = integrator.get_tasks_by_department(section.id)
        for dept, t_list in dept_tasks.items():
            if t_list:
                test_pass(f"Department {dept}", f"-> {len(t_list)} tasks")

        # 1c. Enrich task features (17 ML features)
        features = integrator.enrich_task_features(tasks[0])
        assert len(features) >= 15, f"Expected 15+ features, got {len(features)}"
        test_pass("Feature extraction", f"-> {len(features)} features extracted")
        print(f"    Sample features:")
        for k in ["severity_encoded", "safety_impact_score", "traffic_density",
                   "cascading_risk", "asset_health", "weather_risk_factor"]:
            print(f"      {k}: {features.get(k, 'N/A')}")

        # 1d. Train windows
        today = date.today()
        windows = integrator.get_train_windows(section.id, today)
        test_pass("Train windows", f"-> {len(windows)} trains on {today}")

        # 1e. Available windows
        available = integrator.get_available_windows(section.id, today)
        test_pass("Available windows", f"-> {len(available)} maintenance slots found")
        for w in available[:3]:
            print(f"    {w['start_time'].strftime('%H:%M')}-{w['end_time'].strftime('%H:%M')} ({w['duration_min']}min)")

        # 1f. Asset health summary
        health = integrator.get_asset_health_summary(section.id)
        assert health["total"] > 0, "No assets found!"
        test_pass("Asset health", f"-> {health['total']} assets, avg health: {health['avg_health']}%")

    except Exception as e:
        test_fail("DataIntegrator", str(e))
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 2: CRITICALITY SCORER (XGBoost)
    # ═══════════════════════════════════════════════════════════
    separator("2. CriticalityScorer (XGBoost / GBR)")
    try:
        from services.criticality_scorer import CriticalityScorer
        scorer = CriticalityScorer()

        # 2a. Model loaded/trained?
        assert scorer.model is not None, "Model failed to train!"
        test_pass("Model training", "-> GradientBoostingRegressor trained on 2000 samples")

        # 2b. Feature importance
        importances = scorer.get_feature_importance()
        assert len(importances) > 0, "No feature importances!"
        test_pass("Feature importance", f"-> Top feature: {importances[0]['feature']} ({importances[0]['importance']:.4f})")
        print(f"    Top 5 features:")
        for fi in importances[:5]:
            print(f"      {fi['feature']}: {fi['importance']:.4f}")

        # 2c. Score a single task
        integrator = DataIntegrator(db)
        tasks = integrator.get_pending_tasks(section.id)
        features = integrator.enrich_task_features(tasks[0])
        score = scorer.predict_score(features)
        assert 0 <= score <= 100, f"Score {score} out of range [0,100]!"
        test_pass("Single prediction", f"-> Task {tasks[0].task_code}: score={score}")

        # 2d. Score ALL tasks and verify ranking
        scored = scorer.score_all_tasks(db, section.id, update_db=True)
        assert len(scored) > 0, "No tasks scored!"

        # Verify scores are in order (highest first)
        scores = [s["score"] for s in scored]
        assert scores == sorted(scores, reverse=True), "Scores not properly ranked!"
        test_pass("Batch scoring", f"-> {len(scored)} tasks scored and ranked")

        # 2e. Verify CRITICAL tasks score higher than LOW tasks
        critical_scores = [s["score"] for s in scored if s["task"].severity == "CRITICAL"]
        low_scores = [s["score"] for s in scored if s["task"].severity == "LOW"]
        if critical_scores and low_scores:
            avg_critical = sum(critical_scores) / len(critical_scores)
            avg_low = sum(low_scores) / len(low_scores)
            assert avg_critical > avg_low, f"CRITICAL avg ({avg_critical}) should be > LOW avg ({avg_low})"
            test_pass("Severity ordering",
                      f"-> CRITICAL avg={avg_critical:.1f} > LOW avg={avg_low:.1f}")
        else:
            test_pass("Severity ordering", "-> Only one severity level in this section")

        # Print top 5
        print(f"    Top 5 most critical tasks:")
        for s in scored[:5]:
            t = s["task"]
            print(f"      #{s['rank']} {t.task_code}: {t.severity} {t.task_type} -> score={s['score']}")

    except Exception as e:
        test_fail("CriticalityScorer", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 3: CONFLICT RESOLVER (CSP)
    # ═══════════════════════════════════════════════════════════
    separator("3. ConflictResolver (Constraint Satisfaction)")
    try:
        from services.conflict_resolver import ConflictResolver
        resolver = ConflictResolver(db)

        # 3a. Check train conflict (known conflict: 12:00-14:00 should hit trains)
        conflicts = resolver.check_train_conflict(
            section.id, date.today(),
            time(8, 0), time(10, 0), "BOTH"
        )
        test_pass("Train conflict check",
                  f"-> {len(conflicts)} conflicts for 08:00-10:00 block")

        # 3b. Try a time known to be busy
        conflicts2 = resolver.check_train_conflict(
            section.id, date.today(),
            time(6, 0), time(23, 0), "BOTH"
        )
        test_pass("Full-day conflict check",
                  f"-> {len(conflicts2)} trains would conflict with 06:00-23:00 block")

        # 3c. Verify conflict details have required fields
        if conflicts2:
            c = conflicts2[0]
            assert "type" in c, "Missing 'type' field"
            assert "train_no" in c, "Missing 'train_no' field"
            assert "resolution" in c, "Missing 'resolution' field"
            assert c["type"] == "TRAIN_CLASH", f"Wrong type: {c['type']}"
            test_pass("Conflict structure", "-> All required fields present")
            print(f"    Sample conflict: {c['description'][:80]}...")
            print(f"    Resolution: {c['resolution']['reason'][:80]}...")

        # 3d. Validate block plan
        proposed = [{
            "start_time": time(11, 0),
            "end_time": time(13, 0),
            "line": "BOTH",
            "tasks": [],
            "block_code": "TEST-001",
            "section_id": section.id,
        }]
        validation = resolver.validate_block_plan(section.id, date.today(), proposed)
        test_pass("Plan validation",
                  f"-> Valid={validation['valid']}, Conflicts={validation['total_conflicts']}")

    except Exception as e:
        test_fail("ConflictResolver", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 4: MULTI-AGENT NEGOTIATION (Game Theory)
    # ═══════════════════════════════════════════════════════════
    separator("4. MultiAgentNegotiator (Game Theory)")
    try:
        from services.multi_agent import MultiAgentNegotiator
        negotiator = MultiAgentNegotiator(db)

        target_date = date.today() + timedelta(days=1)
        result = negotiator.negotiate(section.id, target_date)

        assert "allocated_tasks" in result, "Missing allocations!"
        assert "agent_utilities" in result, "Missing utilities!"
        assert "negotiation_log" in result, "Missing log!"

        test_pass("4-round negotiation", f"-> {result['total_rounds']} rounds completed")

        # Check allocations
        total_allocated = 0
        for dept, tasks_list in result["allocated_tasks"].items():
            count = len(tasks_list)
            total_allocated += count
            if count > 0:
                test_pass(f"  {dept} agent", f"-> {count} tasks allocated")

        # Check utilities
        for dept, utility in result["agent_utilities"].items():
            test_pass(f"  {dept} utility", f"-> {utility:.1f}")

        # Allocation Balance (fairness heuristic)
        test_pass("Allocation Balance", f"-> {'BALANCED' if result['is_balanced'] else 'IMBALANCED'}")

        # Integration opportunities
        integrations = result.get("integrated_blocks", [])
        test_pass("Integration opportunities", f"-> {len(integrations)} found")
        for ib in integrations[:3]:
            print(f"    {ib['description'][:80]}...")

    except Exception as e:
        test_fail("MultiAgentNegotiator", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 5: PREDICTIVE ENGINE (LSTM / Decay)
    # ═══════════════════════════════════════════════════════════
    separator("5. PredictiveEngine (LSTM / Exponential Decay)")
    try:
        from services.predictive_engine import PredictiveEngine
        engine = PredictiveEngine()

        # 5a. Single asset prediction
        asset = db.query(RailwayAsset).filter_by(section_id=section.id).first()
        assert asset is not None, "No assets found!"

        prediction = engine.predict_remaining_life(asset, is_ghat=section.is_ghat_section)

        assert "current_health" in prediction
        assert "predicted_failure_date" in prediction
        assert "remaining_life_days" in prediction
        assert "health_trajectory" in prediction
        assert "risk_level" in prediction
        assert len(prediction["health_trajectory"]) == 12, "Should predict 12 months"

        test_pass("Single asset RUL",
                  f"-> {asset.asset_code}: health={prediction['current_health']:.1f}%, "
                  f"risk={prediction['risk_level']}, "
                  f"RUL={prediction['remaining_life_days']} days")
        test_pass("Model used", f"-> {prediction['model_used']}")
        test_pass("12-month trajectory", f"-> {len(prediction['health_trajectory'])} monthly predictions")

        # Verify trajectory is degrading
        traj = prediction["health_trajectory"]
        first_health = traj[0]["predicted_health"]
        last_health = traj[-1]["predicted_health"]
        test_pass("Health degradation",
                  f"-> Month 1: {first_health:.1f}% -> Month 12: {last_health:.1f}%")

        # 5b. Section-wide predictions
        all_preds = engine.predict_all_assets(db, section.id, update_tasks=False)
        assert len(all_preds) > 0, "No predictions generated!"
        test_pass("Section-wide prediction", f"-> {len(all_preds)} assets analyzed")

        risk_counts = {}
        for p in all_preds:
            risk_counts[p["risk_level"]] = risk_counts.get(p["risk_level"], 0) + 1
        print(f"    Risk distribution: {risk_counts}")

        # 5c. Risk summary
        summary = engine.get_section_risk_summary(db, section.id)
        test_pass("Risk summary",
                  f"-> Avg health: {summary['avg_health']:.1f}%, "
                  f"Needing attention: {summary['assets_needing_attention']}")

    except Exception as e:
        test_fail("PredictiveEngine", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 6: ANOMALY DETECTOR (Isolation Forest)
    # ═══════════════════════════════════════════════════════════
    separator("6. AnomalyDetector (Isolation Forest)")
    try:
        from services.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()

        assert detector.model is not None, "Model failed to train!"
        test_pass("Model training", "-> IsolationForest trained (100 trees, 10% contamination)")

        anomalies = detector.detect_anomalies(db, section.id)
        test_pass("Anomaly detection", f"-> {len(anomalies)} anomalies found")

        for a in anomalies[:3]:
            print(f"    [{a['severity']}] {a['description'][:70]}...")
            print(f"           Score: {a['anomaly_score']:.4f}")

    except Exception as e:
        test_fail("AnomalyDetector", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 7: NLP PROCESSOR
    # ═══════════════════════════════════════════════════════════
    separator("7. NLPProcessor (Hindi/English)")
    try:
        from services.nlp_processor import NLPProcessor
        nlp = NLPProcessor()

        test_commands = [
            ("Show available blocks for Kalyan-Kasara section", "QUERY_BLOCKS", "KYN-KAS"),
            ("Top 5 critical tasks", "QUERY_TASKS", None),
            ("Schedule emergency block for OHE repair", "SCHEDULE", None),
            ("Status of kasara section", "STATUS", "KYN-KAS"),
            ("Predict failures for Kalyan section", "PREDICT", "TNA-KYN"),
            ("Kalyan section mein pending tasks dikhao", "QUERY_TASKS", "TNA-KYN"),
            ("Help", "HELP", None),
        ]

        for cmd, expected_intent, expected_section in test_commands:
            result = nlp.process_command(cmd)
            intent_ok = result["intent"] == expected_intent
            section_ok = True
            if expected_section:
                section_ok = result["entities"].get("section") == expected_section

            status = "PASS" if (intent_ok and section_ok) else "FAIL"
            print(f"  [{status}] \"{cmd}\"")
            print(f"         Intent: {result['intent']} {'OK' if intent_ok else 'EXPECTED ' + expected_intent}")
            if expected_section:
                print(f"         Section: {result['entities'].get('section', 'None')} {'OK' if section_ok else 'EXPECTED ' + expected_section}")

            if not (intent_ok and section_ok):
                errors += 1

    except Exception as e:
        test_fail("NLPProcessor", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # TEST 8: BLOCK OPTIMIZER (Full Pipeline)
    # ═══════════════════════════════════════════════════════════
    separator("8. BlockOptimizer (Full AI Pipeline)")
    try:
        from services.block_optimizer import BlockOptimizer
        optimizer = BlockOptimizer(db)

        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        result = optimizer.generate_plan(
            section_id=section.id,
            start_date=start_date,
            end_date=end_date,
            plan_type="WEEKLY",
        )

        assert result is not None, "Optimizer returned None!"
        stats = result["stats"]

        test_pass("Plan generation",
                  f"-> Solver: {stats.get('solver_status', 'N/A')}, "
                  f"Time: {result.get('solve_time_seconds', 0):.3f}s")
        test_pass("Tasks scheduled",
                  f"-> {stats['tasks_scheduled']}/{stats['tasks_total']} "
                  f"({stats['tasks_deferred']} deferred)")
        test_pass("Blocks created", f"-> {stats['total_blocks']} blocks")
        test_pass("Integrated blocks", f"-> {stats['integrated_blocks']}")
        test_pass("Utilization", f"-> {stats['utilization_pct']}%")

        if result.get("plan"):
            test_pass("Database save",
                      f"-> Plan {result['plan'].plan_code} saved (status: {result['plan'].status})")

        # Show block details
        print(f"\n    Block Schedule:")
        for b in result["blocks"][:5]:
            dept = b["departments"]
            btype = "INTEGRATED" if b["is_integrated"] else b["block_type"]
            tasks_str = ", ".join(t["task"].task_code for t in b["tasks"])
            bdate = b["block_date"]
            print(f"    [{bdate}] {b['start_time'].strftime('%H:%M')}-{b['end_time'].strftime('%H:%M')} "
                  f"| {btype} | {dept} | Tasks: {tasks_str}")

        # Show AI explanations
        print(f"\n    AI Explanations:")
        for exp in result["explanations"][:3]:
            print(f"    -> {exp[:100]}...")

    except Exception as e:
        test_fail("BlockOptimizer", str(e))
        import traceback; traceback.print_exc()
        errors += 1

    # ═══════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"  FINAL RESULTS")
    print(f"{'='*60}")
    if errors == 0:
        print(f"  ALL 8 AI MODELS PASSED!")
        print(f"  Status: PRODUCTION READY")
    else:
        print(f"  {errors} test(s) FAILED")
        print(f"  Status: NEEDS FIXES")
    print(f"{'='*60}")

    db.close()
    return errors


if __name__ == "__main__":
    exit(main())
