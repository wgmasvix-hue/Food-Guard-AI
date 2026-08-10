#!/usr/bin/env bash
# Food Guard AI — installer for a server fronted by Caddy (not nginx).
# Caddy multiplexes multiple sites on the same 80/443 it already owns and
# obtains its own Let's Encrypt certs automatically on first request to a
# new site block — no certbot, no separate cert-issuance step, no port
# conflicts with whatever else Caddy already serves on this box.
#
# Usage:
#   sudo DOMAIN=foodguard.example.com bash deploy/install-caddy.sh
#
# Optional env vars:
#   INSTALL_DIR    Default /opt/food-guard-ai
#   REPO_URL       Default https://github.com/wgmasvix-hue/food-guard-ai.git
#   BRANCH         Default claude/food-guard-ai-platform-z05ynw
#   API_HOST_PORT  Default 8001 (loopback port the API container publishes to)
#   WEB_HOST_PORT  Default 3001 (loopback port the web container publishes to)
#   CADDYFILE      Default /etc/caddy/Caddyfile
#   SKIP_DNS_CHECK=1   Skip the "does DOMAIN resolve to this server" check
#   SKIP_SEED=1        Skip loading demo data
set -euo pipefail

DOMAIN="${DOMAIN:-}"
INSTALL_DIR="${INSTALL_DIR:-/opt/food-guard-ai}"
REPO_URL="${REPO_URL:-https://github.com/wgmasvix-hue/food-guard-ai.git}"
BRANCH="${BRANCH:-claude/food-guard-ai-platform-z05ynw}"
API_HOST_PORT="${API_HOST_PORT:-8001}"
WEB_HOST_PORT="${WEB_HOST_PORT:-3001}"
CADDYFILE="${CADDYFILE:-/etc/caddy/Caddyfile}"

log()  { printf '\033[1;32m[install]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

[[ $EUID -eq 0 ]] || die "Run this as root (sudo)."
[[ -n "$DOMAIN" ]] || die "Set DOMAIN, e.g.: DOMAIN=foodguard.example.com bash deploy/install-caddy.sh"

command -v docker >/dev/null || die "Docker is not installed."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin not found."
command -v caddy >/dev/null || die "caddy binary not found on PATH — is Caddy actually installed here?"
systemctl is-active --quiet caddy || die "The caddy service isn't running (systemctl status caddy)."
[[ -f "$CADDYFILE" ]] || die "$CADDYFILE not found. Set CADDYFILE=/path/to/Caddyfile if it lives elsewhere."

# ---------- DNS check ----------
if [[ "${SKIP_DNS_CHECK:-0}" != "1" ]]; then
  log "Checking that $DOMAIN resolves to this server..."
  SERVER_IP="$(curl -fsS4 https://ifconfig.me || curl -fsS4 https://api.ipify.org)"
  DOMAIN_IP="$(getent ahostsv4 "$DOMAIN" | awk '{print $1}' | head -n1 || true)"
  if [[ -z "$DOMAIN_IP" ]]; then
    die "$DOMAIN does not resolve yet. Point its DNS A record at $SERVER_IP, wait for propagation, then re-run. (Set SKIP_DNS_CHECK=1 to bypass.)"
  fi
  if [[ "$DOMAIN_IP" != "$SERVER_IP" ]]; then
    warn "$DOMAIN resolves to $DOMAIN_IP but this server's public IP looks like $SERVER_IP."
    warn "Caddy's automatic HTTPS will fail if that mismatch is real. Continuing in 10s (Ctrl+C to abort)."
    sleep 10
  else
    log "DNS looks correct ($DOMAIN -> $SERVER_IP)."
  fi
fi

# ---------- clone / update ----------
if [[ -d "$INSTALL_DIR/.git" ]]; then
  log "Updating existing checkout at $INSTALL_DIR..."
  git -C "$INSTALL_DIR" fetch origin "$BRANCH"
  git -C "$INSTALL_DIR" checkout "$BRANCH"
  git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
else
  log "Cloning $REPO_URL ($BRANCH) into $INSTALL_DIR..."
  git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ---------- chosen loopback ports must be free (or already ours from a prior run) ----------
current_mapped_port() {  # $1 = service name, $2 = container port
  docker compose port "$1" "$2" 2>/dev/null | sed -E 's/.*:([0-9]+)$/\1/'
}
API_CURRENT_PORT="$(current_mapped_port api 8000 || true)"
WEB_CURRENT_PORT="$(current_mapped_port web 3000 || true)"

check_port_free() {  # $1 = wanted port, $2 = port this service is already published on (if running)
  local wanted="$1" current="$2"
  [[ -n "$current" && "$wanted" == "$current" ]] && return 0   # already ours — fine to reuse
  if ss -ltn "( sport = :$wanted )" | grep -q LISTEN; then
    die "Port $wanted is already in use by something else. Pick a free one: API_HOST_PORT=... WEB_HOST_PORT=... (re-run with different values)."
  fi
}
check_port_free "$API_HOST_PORT" "$API_CURRENT_PORT"
check_port_free "$WEB_HOST_PORT" "$WEB_CURRENT_PORT"

# ---------- .env ----------
if [[ ! -f .env ]]; then
  log "Generating .env..."
  SECRET_KEY="$(openssl rand -hex 32)"
  DB_PASSWORD="$(openssl rand -hex 20)"
  cp .env.example .env
  sed -i \
    -e "s#^SECRET_KEY=.*#SECRET_KEY=${SECRET_KEY}#" \
    -e "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=${DB_PASSWORD}#" \
    -e "s#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg://foodguard:${DB_PASSWORD}@db:5432/foodguard#" \
    -e "s#^BACKEND_CORS_ORIGINS=.*#BACKEND_CORS_ORIGINS=[\"https://${DOMAIN}\"]#" \
    -e "s#^ENVIRONMENT=.*#ENVIRONMENT=production#" \
    -e "s#^NEXT_PUBLIC_API_URL=.*#NEXT_PUBLIC_API_URL=https://${DOMAIN}/api/v1#" \
    .env
else
  log ".env already exists — leaving it as-is."
fi
grep -q '^API_HOST_PORT=' .env && sed -i "s#^API_HOST_PORT=.*#API_HOST_PORT=${API_HOST_PORT}#" .env || echo "API_HOST_PORT=${API_HOST_PORT}" >> .env
grep -q '^WEB_HOST_PORT=' .env && sed -i "s#^WEB_HOST_PORT=.*#WEB_HOST_PORT=${WEB_HOST_PORT}#" .env || echo "WEB_HOST_PORT=${WEB_HOST_PORT}" >> .env

# ---------- start app containers only (no dockerized nginx, no host nginx) ----------
log "Building and starting db, api, web..."
docker compose up -d --build db api web

log "Waiting for the API to become healthy on 127.0.0.1:${API_HOST_PORT}..."
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:${API_HOST_PORT}/health" >/dev/null 2>&1 && break
  sleep 2
  [[ $i -eq 30 ]] && warn "API did not respond within 60s — continuing anyway, check 'docker compose logs api' if Caddy can't reach it."
done

# ---------- Caddy site block ----------
MARKER="# food-guard-ai:${DOMAIN}"
SITE_FILE=""

# Prefer a sites directory if the Caddyfile imports one (matches how tools
# like ChengetAi Deploy manage per-deployment Caddy sites) — write our own
# file there rather than editing a file another tool owns.
IMPORT_LINE="$(grep -E '^\s*import\s+' "$CADDYFILE" | head -n1 || true)"
if [[ -n "$IMPORT_LINE" ]]; then
  IMPORT_PATTERN="$(echo "$IMPORT_LINE" | awk '{print $2}')"
  IMPORT_DIR="$(dirname "$IMPORT_PATTERN")"
  if [[ -d "$IMPORT_DIR" ]]; then
    SITE_FILE="${IMPORT_DIR}/food-guard-ai.caddy"
    log "Caddyfile imports $IMPORT_PATTERN — writing site block to $SITE_FILE"
  fi
fi

if [[ -n "$SITE_FILE" ]]; then
  cat > "$SITE_FILE" <<EOF
${DOMAIN} {
    encode gzip

    handle /api/* {
        reverse_proxy 127.0.0.1:${API_HOST_PORT}
    }

    handle {
        reverse_proxy 127.0.0.1:${WEB_HOST_PORT}
    }
}
EOF
else
  if grep -qF "$MARKER" "$CADDYFILE"; then
    log "Site block for $DOMAIN already present in $CADDYFILE — leaving it as-is (edit it manually if ports changed)."
  else
    log "No sites-import directory found — appending a block directly to $CADDYFILE"
    cp "$CADDYFILE" "${CADDYFILE}.bak.$(date +%s)"
    cat >> "$CADDYFILE" <<EOF

${MARKER}
${DOMAIN} {
    encode gzip

    handle /api/* {
        reverse_proxy 127.0.0.1:${API_HOST_PORT}
    }

    handle {
        reverse_proxy 127.0.0.1:${WEB_HOST_PORT}
    }
}
EOF
  fi
fi

log "Validating Caddy config..."
caddy validate --config "$CADDYFILE" --adapter caddyfile \
  || die "Caddy config is invalid — check $CADDYFILE (a .bak backup was made if this script appended to it)."

log "Reloading Caddy..."
systemctl reload caddy

# ---------- backups + health monitoring ----------
log "Installing nightly backups (02:30), health-check alerts (every 5 min), and overdue corrective-action checks (hourly)..."
install -m 755 deploy/backup.sh /usr/local/bin/food-guard-ai-backup.sh
sed -i "s#__INSTALL_DIR__#${INSTALL_DIR}#g" /usr/local/bin/food-guard-ai-backup.sh
install -m 755 deploy/healthcheck-alert.sh /usr/local/bin/food-guard-ai-healthcheck.sh
sed -i "s#__INSTALL_DIR__#${INSTALL_DIR}#g" /usr/local/bin/food-guard-ai-healthcheck.sh
install -m 755 deploy/check-overdue.sh /usr/local/bin/food-guard-ai-check-overdue.sh
sed -i "s#__INSTALL_DIR__#${INSTALL_DIR}#g" /usr/local/bin/food-guard-ai-check-overdue.sh
cat > /etc/cron.d/food-guard-ai-ops <<EOF
30 2 * * * root /usr/local/bin/food-guard-ai-backup.sh >> /var/log/food-guard-ai-backup.log 2>&1
*/5 * * * * root /usr/local/bin/food-guard-ai-healthcheck.sh >> /var/log/food-guard-ai-healthcheck.log 2>&1
0 * * * * root /usr/local/bin/food-guard-ai-check-overdue.sh >> /var/log/food-guard-ai-check-overdue.log 2>&1
EOF

# ---------- seed demo data ----------
if [[ "${SKIP_SEED:-0}" != "1" ]]; then
  log "Loading demo data (safe to re-run; skips if already seeded)..."
  docker compose exec -T api python -m app.db.seed || warn "Seeding failed or already seeded — check with: docker compose logs api"
fi

log "Done. Food Guard AI should now be live at: https://${DOMAIN}"
log "(Caddy issues the certificate on first request — the very first page load may take a few extra seconds.)"
log "API docs: https://${DOMAIN}/api/v1/docs"
log ""
log "IMPORTANT: this deployed the '${BRANCH}' branch directly (not yet merged to main)."
log "Review it and merge to main via a PR when you're ready to treat it as the production baseline."
