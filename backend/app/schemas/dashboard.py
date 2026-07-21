from datetime import date

from pydantic import BaseModel

from app.schemas.audit import AuditRead
from app.schemas.corrective_action import CorrectiveActionRead
from app.schemas.gmp import ChecklistRead
from app.schemas.temperature import TemperatureLogRead


class DashboardSummary(BaseModel):
    compliance_score: float
    open_corrective_actions: int
    overdue_corrective_actions: int
    temperature_alerts_today: int
    upcoming_audits: list[AuditRead]
    recent_inspections: list[ChecklistRead]
    recent_temperature_alerts: list[TemperatureLogRead]
    today_tasks: list[str]
    ai_recommendations: list[str]
