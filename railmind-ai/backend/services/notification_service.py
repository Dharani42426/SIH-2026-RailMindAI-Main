# ═══════════════════════════════════════════════════════════════
# RailMind AI — Notification Service
# Sends alerts for critical events to railway personnel
# ═══════════════════════════════════════════════════════════════

import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from models.maintenance_task import MaintenanceTask
from models.block_plan import BlockPlan, ConflictLog


class NotificationType:
    """Notification type constants."""
    CRITICAL_TASK = "CRITICAL_TASK"
    OVERDUE_TASK = "OVERDUE_TASK"
    PLAN_GENERATED = "PLAN_GENERATED"
    PLAN_APPROVED = "PLAN_APPROVED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    ASSET_CRITICAL = "ASSET_CRITICAL"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    BLOCK_STARTING = "BLOCK_STARTING"
    PREDICTION_ALERT = "PREDICTION_ALERT"


class Notification:
    """Represents a single notification."""

    def __init__(
        self,
        notification_type: str,
        title: str,
        message: str,
        severity: str = "INFO",
        target_roles: list[str] = None,
        target_department: str = None,
        data: dict = None,
    ):
        self.id = None
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.severity = severity  # INFO, WARNING, CRITICAL
        self.target_roles = target_roles or ["CONTROLLER"]
        self.target_department = target_department
        self.data = data or {}
        self.created_at = datetime.now()
        self.read = False

    def to_dict(self) -> dict:
        return {
            "type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "target_roles": self.target_roles,
            "target_department": self.target_department,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "read": self.read,
        }


class NotificationService:
    """
    Manages notifications for the RailMind AI system.

    Notification channels:
    1. In-app notifications (stored in memory / WebSocket)
    2. Email alerts (future implementation)
    3. SMS alerts for critical events (future implementation)

    For SIH demo: all notifications are stored in-memory
    and pushed via WebSocket to the frontend dashboard.
    """

    def __init__(self):
        self.notifications: list[Notification] = []
        self.websocket_connections = []  # Will be set by main.py

    def notify(self, notification: Notification) -> Notification:
        """Send a notification."""
        self.notifications.append(notification)
        print(
            f"[Notification] [{notification.severity}] {notification.title}: "
            f"{notification.message}"
        )

        # Push to WebSocket connections if available
        self._push_websocket(notification)

        return notification

    def _push_websocket(self, notification: Notification):
        """Push notification to connected WebSocket clients."""
        import asyncio
        if not self.websocket_connections:
            return
            
        async def send_to_all():
            disconnected = []
            for ws in self.websocket_connections:
                try:
                    await ws.send_json(notification.to_dict())
                except Exception as e:
                    disconnected.append(ws)
            
            # Remove disconnected clients
            for ws in disconnected:
                if ws in self.websocket_connections:
                    self.websocket_connections.remove(ws)
                    
        # Create an asyncio task in the running event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_to_all())
        except RuntimeError:
            pass # No running event loop (e.g., during tests)

    def get_recent(self, limit: int = 20) -> list[dict]:
        """Get recent notifications."""
        return [n.to_dict() for n in reversed(self.notifications[-limit:])]

    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return sum(1 for n in self.notifications if not n.read)

    def mark_read(self, index: int):
        """Mark a notification as read."""
        if 0 <= index < len(self.notifications):
            self.notifications[index].read = True

    # ─── Pre-built Notification Templates ───

    def alert_critical_task(self, task: MaintenanceTask):
        """Alert when a CRITICAL severity task is detected."""
        self.notify(Notification(
            notification_type=NotificationType.CRITICAL_TASK,
            title="Critical Maintenance Task Detected",
            message=(
                f"Task {task.task_code}: {task.task_type} at "
                f"KM {task.km_from}-{task.km_to}. "
                f"Severity: {task.severity}. "
                f"Due: {task.due_date}. "
                f"Speed restriction: {task.speed_restriction or 'None'} km/h."
            ),
            severity="CRITICAL",
            target_roles=["CONTROLLER", "DEN", "SSE"],
            target_department=task.department,
            data={"task_code": task.task_code, "section_id": task.section_id},
        ))

    def alert_overdue_tasks(self, tasks: list[MaintenanceTask]):
        """Alert about overdue maintenance tasks."""
        if not tasks:
            return
        self.notify(Notification(
            notification_type=NotificationType.OVERDUE_TASK,
            title=f"{len(tasks)} Overdue Maintenance Tasks",
            message=(
                f"The following tasks are past due: "
                + ", ".join(t.task_code for t in tasks[:5])
                + (f" and {len(tasks) - 5} more" if len(tasks) > 5 else "")
            ),
            severity="WARNING",
            target_roles=["CONTROLLER", "DEN"],
            data={"task_codes": [t.task_code for t in tasks]},
        ))

    def alert_plan_generated(self, plan: BlockPlan, stats: dict):
        """Alert when AI generates a new block plan."""
        self.notify(Notification(
            notification_type=NotificationType.PLAN_GENERATED,
            title=f"AI Block Plan Generated: {plan.plan_code}",
            message=(
                f"Plan {plan.plan_code} generated with "
                f"{stats.get('total_blocks', 0)} blocks, "
                f"{stats.get('tasks_scheduled', 0)} tasks scheduled, "
                f"{stats.get('integrated_blocks', 0)} integrated blocks. "
                f"Utilization: {stats.get('utilization_pct', 0):.1f}%. "
                "Awaiting approval."
            ),
            severity="INFO",
            target_roles=["CONTROLLER"],
            data={"plan_code": plan.plan_code, "plan_id": plan.id},
        ))

    def alert_conflict(self, conflict_description: str, severity: str = "WARNING"):
        """Alert about a scheduling conflict."""
        self.notify(Notification(
            notification_type=NotificationType.CONFLICT_DETECTED,
            title="Scheduling Conflict Detected",
            message=conflict_description,
            severity=severity,
            target_roles=["CONTROLLER"],
        ))

    def alert_asset_critical(self, asset_code: str, health: float, prediction: dict):
        """Alert when an asset's health drops to critical level."""
        self.notify(Notification(
            notification_type=NotificationType.ASSET_CRITICAL,
            title=f"Asset {asset_code} Health Critical",
            message=(
                f"Asset {asset_code} health: {health:.1f}%. "
                f"Predicted failure: {prediction.get('predicted_failure_date', 'Unknown')}. "
                f"Risk level: {prediction.get('risk_level', 'HIGH')}. "
                "Recommend immediate inspection."
            ),
            severity="CRITICAL",
            target_roles=["CONTROLLER", "SSE", "PWI"],
            data={"asset_code": asset_code, "health": health},
        ))

    def alert_anomaly(self, anomaly: dict):
        """Alert when an anomaly is detected."""
        self.notify(Notification(
            notification_type=NotificationType.ANOMALY_DETECTED,
            title="Anomalous Pattern Detected",
            message=anomaly.get("description", "Unusual maintenance pattern detected"),
            severity="WARNING",
            target_roles=["CONTROLLER", "DEN"],
            data=anomaly,
        ))


# ─── Singleton instance ───
notification_service = NotificationService()
