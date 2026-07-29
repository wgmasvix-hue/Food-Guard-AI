#!/usr/bin/env bash
# Installed by install*.sh into /usr/local/bin and run every few minutes via
# cron. Checks the app's /health endpoint and emails ALERT_EMAIL (via the
# SMTP_* settings in .env) after repeated consecutive failures, and again
# once it recovers. If SMTP_HOST/ALERT_EMAIL aren't set, it just logs to the
# cron log — wire that log into whatever monitoring you already have.
set -euo pipefail

INSTALL_DIR="__INSTALL_DIR__"
cd "$INSTALL_DIR"

env_var() { grep -E "^$1=" .env 2>/dev/null | head -n1 | cut -d= -f2- || true; }

HEALTHCHECK_URL="$(env_var HEALTHCHECK_URL)"
API_HOST_PORT="$(env_var API_HOST_PORT)"; API_HOST_PORT="${API_HOST_PORT:-8000}"
URL="${HEALTHCHECK_URL:-http://127.0.0.1:${API_HOST_PORT}/health}"

ALERT_EMAIL="$(env_var ALERT_EMAIL)"
SMTP_HOST="$(env_var SMTP_HOST)"
SMTP_PORT="$(env_var SMTP_PORT)"; SMTP_PORT="${SMTP_PORT:-587}"
SMTP_USER="$(env_var SMTP_USER)"
SMTP_PASSWORD="$(env_var SMTP_PASSWORD)"
EMAILS_FROM="$(env_var EMAILS_FROM)"; EMAILS_FROM="${EMAILS_FROM:-noreply@foodguard.ai}"

STATE_FILE="$INSTALL_DIR/.healthcheck-state"
FAIL_COUNT=0
ALERTED=0
if [[ -f "$STATE_FILE" ]]; then
  read -r FAIL_COUNT ALERTED < "$STATE_FILE" || true
fi

FAIL_THRESHOLD=2   # consecutive failures before alerting (avoids noise on transient blips)

send_mail() {  # $1 = subject, $2 = body
  if [[ -z "$ALERT_EMAIL" || -z "$SMTP_HOST" ]]; then
    echo "[healthcheck] ALERT (no SMTP_HOST/ALERT_EMAIL configured, not emailing): $1 — $2"
    return
  fi
  python3 - "$1" "$2" <<'PYEOF' || echo "[healthcheck] Failed to send alert email — check SMTP_* settings."
import smtplib, sys, os
from email.message import EmailMessage

subject, body = sys.argv[1], sys.argv[2]
msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = os.environ["EMAILS_FROM"]
msg["To"] = os.environ["ALERT_EMAIL"]
msg.set_content(body)

with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=15) as s:
    s.starttls()
    if os.environ.get("SMTP_USER"):
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    s.send_message(msg)
PYEOF
}
export ALERT_EMAIL SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD EMAILS_FROM

set +e
BODY="$(curl -fsS --max-time 10 "$URL" 2>&1)"
CURL_OK=$?
set -e
if [[ $CURL_OK -eq 0 ]] && echo "$BODY" | grep -q '"status":"ok"'; then
  if [[ "$ALERTED" == "1" ]]; then
    echo "[healthcheck] Recovered — sending recovery notice."
    send_mail "Food Guard AI: RECOVERED" "The health check at $URL is passing again as of $(date -u +%FT%TZ)."
  fi
  echo "0 0" > "$STATE_FILE"
else
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "[healthcheck] Failed ($FAIL_COUNT consecutive): $URL -> ${BODY:-no response}"
  if [[ $FAIL_COUNT -ge $FAIL_THRESHOLD && "$ALERTED" != "1" ]]; then
    send_mail "Food Guard AI: HEALTH CHECK FAILING" "The health check at $URL has failed $FAIL_COUNT times in a row as of $(date -u +%FT%TZ). Last response: ${BODY:-no response}. Check: docker compose logs api"
    ALERTED=1
  fi
  echo "$FAIL_COUNT $ALERTED" > "$STATE_FILE"
fi
