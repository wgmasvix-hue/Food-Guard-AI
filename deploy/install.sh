#!/usr/bin/env bash
# Food Guard AI — turnkey installer for a Docker-Compose-ready Linux server.
#
# Safe to run alongside other Docker workloads on the same host: everything
# here is namespaced under the "food-guard-ai" Compose project (its own
# network/volumes), the database is never published to the host, and the
# app/web containers bind to 127.0.0.1 only — the only ports touched on the
# public interface are 80 and 443 (nginx).
#
# Usage:
#   sudo DOMAIN=foodguard.example.com EMAIL=you@example.com bash install.sh
#
# Optional env vars:
#   INSTALL_DIR   Default /opt/food-guard-ai
#   REPO_URL      Default https://github.com/wgmasvix-hue/food-guard-ai.git
#   BRANCH        Default claude/food-guard-ai-platform-z05ynw
#   SKIP_DNS_CHECK=1   Skip the "does DOMAIN resolve to this server" check
#   SKIP_SEED=1        Skip loading demo data
set -euo pipefail

# ---------- config ----------
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"
INSTALL_DIR="${INSTALL_DIR:-/opt/food-guard-ai}"
REPO_URL="${REPO_URL:-https://github.com/wgmasvix-hue/food-guard-ai.git}"
BRANCH="${BRANCH:-claude/food-guard-ai-platform-z05ynw}"

log()  { printf '\033[1;32m[install]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

[[ $EUID -eq 0 ]] || die "Run this as root (sudo)."
[[ -n "$DOMAIN" ]] || die "Set DOMAIN, e.g.: DOMAIN=foodguard.example.com EMAIL=you@example.com bash install.sh"
[[ -n "$EMAIL"  ]] || die "Set EMAIL for Let's Encrypt notices, e.g.: EMAIL=you@example.com"

command -v docker >/dev/null || die "Docker is not installed. Install Docker Engine + the compose plugin first."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin not found (try: apt install docker-compose-plugin)."

# ---------- port sanity check ----------
log "Checking that ports 80/443 are free on the host..."
for port in 80 443; do
  if ss -ltn "( sport = :$port )" | grep -q LISTEN; then
    die "Port $port is already in use by another process. Free it (or point that process's own reverse proxy at this app instead) before re-running."
  fi
done

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
    warn "Let's Encrypt will fail if that mismatch is real. Continuing in 10s (Ctrl+C to abort) — set SKIP_DNS_CHECK=1 to silence this."
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
  log "Wrote .env with generated SECRET_KEY / POSTGRES_PASSWORD."
else
  log ".env already exists — leaving it as-is. Delete it first if you want fresh secrets."
fi

# ---------- bootstrap nginx (HTTP only, for the ACME challenge) ----------
log "Rendering bootstrap (HTTP-only) nginx config..."
sed "s#__DOMAIN__#${DOMAIN}#g" nginx/conf.d/default.conf.http.template > nginx/conf.d/default.conf

log "Building and starting db, api, web, nginx..."
docker compose up -d --build db api web nginx

log "Waiting for the API to become healthy..."
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:8000/health" >/dev/null 2>&1 && break
  sleep 2
  [[ $i -eq 30 ]] && warn "API did not respond within 60s — continuing anyway, check 'docker compose logs api' if the cert step fails."
done

# ---------- TLS via Let's Encrypt ----------
if docker run --rm -v food-guard-ai_certbot-etc:/etc/letsencrypt certbot/certbot certificates 2>/dev/null | grep -q "Domains: ${DOMAIN}"; then
  log "Certificate for $DOMAIN already exists — skipping issuance."
else
  log "Requesting a Let's Encrypt certificate for $DOMAIN..."
  docker run --rm \
    -v food-guard-ai_certbot-webroot:/var/www/certbot \
    -v food-guard-ai_certbot-etc:/etc/letsencrypt \
    certbot/certbot certonly --webroot -w /var/www/certbot \
    -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email --non-interactive \
    || die "Certificate issuance failed. Check that $DOMAIN really points here and port 80 is reachable from the internet, then re-run this script."
fi

# ---------- switch nginx to HTTPS ----------
log "Switching nginx to the HTTPS config..."
sed "s#__DOMAIN__#${DOMAIN}#g" nginx/conf.d/default.conf.ssl.template > nginx/conf.d/default.conf
docker compose exec nginx nginx -s reload || docker compose restart nginx

# ---------- renewal ----------
log "Installing certbot auto-renewal (daily cron, 03:15)..."
install -m 755 deploy/renew.sh /usr/local/bin/food-guard-ai-renew.sh
sed -i "s#__INSTALL_DIR__#${INSTALL_DIR}#g" /usr/local/bin/food-guard-ai-renew.sh
cat > /etc/cron.d/food-guard-ai-renew <<EOF
15 3 * * * root /usr/local/bin/food-guard-ai-renew.sh >> /var/log/food-guard-ai-renew.log 2>&1
EOF

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
log "API docs: https://${DOMAIN}/api/v1/docs"
log ""
log "IMPORTANT: this deployed the '${BRANCH}' branch directly (not yet merged to main)."
log "Review it and merge to main via a PR when you're ready to treat it as the production baseline."
