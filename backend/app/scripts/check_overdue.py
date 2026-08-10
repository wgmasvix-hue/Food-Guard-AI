"""CLI entrypoint for the overdue-corrective-action alert check. Run
periodically via cron (see deploy/install*.sh):

    docker compose exec -T api python -m app.scripts.check_overdue
"""
from app.db.session import SessionLocal
from app.services.overdue_alerts import check_and_alert_overdue_corrective_actions


def main() -> None:
    db = SessionLocal()
    try:
        count = check_and_alert_overdue_corrective_actions(db)
        print(f"Checked for overdue corrective actions: {count} newly marked overdue.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
