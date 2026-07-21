from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.models.audit import Audit
from app.models.company import Company
from app.models.corrective_action import CorrectiveAction
from app.models.gmp import Checklist
from app.models.haccp import CCP, HaccpPlan, MonitoringRecord
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.models.user import User
from app.services import reports as report_service
from app.services.compliance import calculate_compliance_score

router = APIRouter()


def _pdf_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _company_name(db: Session, company_id: str) -> str:
    company = db.get(Company, company_id)
    return company.name if company else "Food Guard AI"


@router.get("/temperature-logs")
def temperature_logs_report(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    logs = (
        db.query(TemperatureLog)
        .join(TemperatureUnit, TemperatureLog.unit_id == TemperatureUnit.id)
        .filter(TemperatureUnit.company_id == current_user.company_id, TemperatureLog.recorded_at >= since)
        .order_by(TemperatureLog.recorded_at.desc())
        .all()
    )
    rows = [
        {
            "unit_name": log.unit.name,
            "unit_type": log.unit.unit_type,
            "temperature": log.temperature,
            "within_limits": log.within_limits,
            "recorded_at": log.recorded_at.strftime("%Y-%m-%d %H:%M"),
        }
        for log in logs
    ]
    pdf = report_service.temperature_log_report(_company_name(db, current_user.company_id), rows)
    return _pdf_response(pdf, "temperature-log-report.pdf")


@router.get("/inspections/{checklist_id}")
def inspection_report(
    checklist_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    checklist = db.get(Checklist, checklist_id)
    if not checklist or checklist.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist not found")
    data = {
        "template_name": checklist.template.name,
        "category": checklist.template.category,
        "facility_name": checklist.facility.name if checklist.facility else None,
        "inspector_name": checklist.inspector.full_name if checklist.inspector else None,
        "score": checklist.score,
        "items": [
            {"question": i.question, "result": i.result, "comment": i.comment} for i in checklist.items
        ],
    }
    pdf = report_service.inspection_report(_company_name(db, current_user.company_id), data)
    return _pdf_response(pdf, "inspection-report.pdf")


@router.get("/haccp/{plan_id}")
def haccp_monitoring_report(
    plan_id: str,
    days: int = Query(default=30, ge=1, le=180),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    plan = db.get(HaccpPlan, plan_id)
    if not plan or plan.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HACCP plan not found")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    records = (
        db.query(MonitoringRecord)
        .join(CCP, MonitoringRecord.ccp_id == CCP.id)
        .filter(CCP.plan_id == plan_id, MonitoringRecord.recorded_at >= since)
        .order_by(MonitoringRecord.recorded_at.desc())
        .all()
    )
    rows = [
        {
            "ccp_number": r.ccp.number,
            "ccp_name": r.ccp.name,
            "measured_value": r.measured_value,
            "unit": r.unit,
            "within_limits": r.within_limits,
            "recorded_at": r.recorded_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in records
    ]
    pdf = report_service.haccp_monitoring_report(_company_name(db, current_user.company_id), plan.name, rows)
    return _pdf_response(pdf, "haccp-monitoring-report.pdf")


@router.get("/corrective-actions")
def corrective_actions_report(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    cas = (
        db.query(CorrectiveAction)
        .filter(CorrectiveAction.company_id == current_user.company_id)
        .order_by(CorrectiveAction.created_at.desc())
        .all()
    )
    rows = [
        {
            "title": ca.title,
            "status": ca.status,
            "responsible_name": ca.responsible.full_name if ca.responsible else None,
            "deadline": ca.deadline,
            "source": ca.source,
        }
        for ca in cas
    ]
    pdf = report_service.corrective_actions_report(_company_name(db, current_user.company_id), rows)
    return _pdf_response(pdf, "corrective-actions-report.pdf")


@router.get("/audits/{audit_id}")
def audit_report(
    audit_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    audit = db.get(Audit, audit_id)
    if not audit or audit.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    data = {
        "title": audit.title,
        "audit_type": audit.audit_type,
        "standard": audit.standard,
        "status": audit.status,
        "score": audit.score,
        "summary": audit.summary,
        "findings": [
            {"clause": f.clause, "severity": f.severity, "description": f.description, "status": f.status}
            for f in audit.findings
        ],
    }
    pdf = report_service.audit_report(_company_name(db, current_user.company_id), data)
    return _pdf_response(pdf, "audit-report.pdf")


@router.get("/compliance-summary")
def compliance_summary_report(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.api.v1.endpoints.dashboard import get_summary  # local import avoids circular ref at module load

    summary = get_summary(current_user=current_user, db=db)
    pdf = report_service.compliance_summary_report(_company_name(db, current_user.company_id), summary.model_dump())
    return _pdf_response(pdf, "compliance-summary-report.pdf")
