from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.models.audit import Audit
from app.models.enums import AuditStatus, CAStatus, ChecklistStatus
from app.models.corrective_action import CorrectiveAction
from app.models.gmp import Checklist
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.compliance import calculate_compliance_score

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    company_id = current_user.company_id
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)

    compliance_score = calculate_compliance_score(db, company_id) if company_id else 100.0

    open_ca_query = db.query(CorrectiveAction).filter(
        CorrectiveAction.company_id == company_id,
        CorrectiveAction.status.in_([CAStatus.OPEN, CAStatus.IN_PROGRESS, CAStatus.PENDING_VERIFICATION]),
    )
    open_cas = open_ca_query.count()
    overdue_cas = open_ca_query.filter(
        CorrectiveAction.deadline.isnot(None), CorrectiveAction.deadline < date.today()
    ).count()

    temp_alerts_today = (
        db.query(TemperatureLog)
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .filter(
            TemperatureUnit.company_id == company_id,
            TemperatureLog.within_limits.is_(False),
            TemperatureLog.recorded_at >= today_start,
        )
        .count()
    )

    upcoming_audits = (
        db.query(Audit)
        .filter(
            Audit.company_id == company_id,
            Audit.status == AuditStatus.SCHEDULED,
            Audit.scheduled_date >= date.today(),
        )
        .order_by(Audit.scheduled_date)
        .limit(5)
        .all()
    )

    recent_inspections = (
        db.query(Checklist)
        .filter(Checklist.company_id == company_id, Checklist.status != ChecklistStatus.IN_PROGRESS)
        .order_by(Checklist.completed_at.desc())
        .limit(5)
        .all()
    )

    recent_alerts = (
        db.query(TemperatureLog)
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .filter(TemperatureUnit.company_id == company_id, TemperatureLog.within_limits.is_(False))
        .order_by(TemperatureLog.recorded_at.desc())
        .limit(5)
        .all()
    )

    today_tasks = []
    if temp_alerts_today:
        today_tasks.append(f"Review {temp_alerts_today} temperature alert(s) recorded today")
    if overdue_cas:
        today_tasks.append(f"Resolve {overdue_cas} overdue corrective action(s)")
    upcoming_soon = [a for a in upcoming_audits if a.scheduled_date and a.scheduled_date <= date.today() + timedelta(days=7)]
    if upcoming_soon:
        today_tasks.append(f"Prepare for {len(upcoming_soon)} audit(s) in the next 7 days")
    if not today_tasks:
        today_tasks.append("No urgent tasks — great job staying on top of compliance!")

    ai_recommendations = []
    if compliance_score < 80:
        ai_recommendations.append("Compliance score is below 80% — review recent GMP failures and open corrective actions.")
    if overdue_cas:
        ai_recommendations.append("Escalate overdue corrective actions to responsible owners before the next audit.")
    if temp_alerts_today:
        ai_recommendations.append("Investigate recurring temperature deviations for possible equipment malfunction.")
    if not ai_recommendations:
        ai_recommendations.append("All key metrics look healthy. Consider scheduling your next internal audit.")

    return DashboardSummary(
        compliance_score=compliance_score,
        open_corrective_actions=open_cas,
        overdue_corrective_actions=overdue_cas,
        temperature_alerts_today=temp_alerts_today,
        upcoming_audits=upcoming_audits,
        recent_inspections=recent_inspections,
        recent_temperature_alerts=recent_alerts,
        today_tasks=today_tasks,
        ai_recommendations=ai_recommendations,
    )
