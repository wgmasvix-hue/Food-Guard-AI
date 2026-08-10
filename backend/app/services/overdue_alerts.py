"""Finds corrective actions that have just become overdue (deadline
passed, still open) and alerts each affected company once per
transition. Meant to run periodically (see app/scripts/check_overdue.py
and its cron entry in deploy/install*.sh) — there's no in-process
scheduler in this app, so this is invoked the same way deploy/backup.sh
and healthcheck-alert.sh are: a script cron runs on the server.

Idempotent by design: a corrective action only gets picked up here once,
because finding it also flips its status to CAStatus.OVERDUE — the next
run's WHERE clause (status in OPEN/IN_PROGRESS/PENDING_VERIFICATION)
no longer matches it, so it won't be re-alerted every run.
"""
from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.models.corrective_action import CorrectiveAction
from app.models.enums import CAStatus, NotificationLevel
from app.services.alerts import notify_company


def check_and_alert_overdue_corrective_actions(db: Session) -> int:
    """Returns the number of corrective actions newly marked overdue."""
    newly_overdue = (
        db.query(CorrectiveAction)
        .filter(
            CorrectiveAction.status.in_([CAStatus.OPEN, CAStatus.IN_PROGRESS, CAStatus.PENDING_VERIFICATION]),
            CorrectiveAction.deadline.isnot(None),
            CorrectiveAction.deadline < date.today(),
        )
        .all()
    )
    if not newly_overdue:
        return 0

    by_company: dict[str, list[CorrectiveAction]] = defaultdict(list)
    for ca in newly_overdue:
        ca.status = CAStatus.OVERDUE
        by_company[ca.company_id].append(ca)

    for company_id, cas in by_company.items():
        titles = "\n".join(f"• {ca.title} (was due {ca.deadline})" for ca in cas[:10])
        more = f"\n…and {len(cas) - 10} more." if len(cas) > 10 else ""
        notify_company(
            db,
            company_id=company_id,
            level=NotificationLevel.WARNING,
            title=f"{len(cas)} corrective action(s) overdue",
            message=f"{titles}{more}",
            link="/corrective-actions",
        )

    db.commit()
    return len(newly_overdue)
