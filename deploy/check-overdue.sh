#!/usr/bin/env bash
# Installed by install*.sh into /usr/local/bin and run hourly via cron.
# Finds corrective actions that just passed their deadline, marks them
# overdue, and alerts the company's QA/food-safety staff (in-app +
# WhatsApp if configured — see app/services/alerts.py and
# app/services/whatsapp/). Safe to run manually too; it's idempotent
# (each corrective action only triggers an alert once, the run after it
# no longer matches the "not yet overdue" query).
set -euo pipefail

INSTALL_DIR="__INSTALL_DIR__"
cd "$INSTALL_DIR"

docker compose exec -T api python -m app.scripts.check_overdue
