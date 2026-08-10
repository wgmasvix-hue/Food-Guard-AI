#!/usr/bin/env bash
# Food Guard AI — installer for a server that ALREADY runs its own nginx
# (or Apache) on ports 80/443 in front of other sites. Unlike install.sh,
# this never starts the dockerized nginx service — it adds a vhost to the
# existing host nginx instead, and runs the app containers on loopback-only
# ports of your choosing.
#
# Usage:
#   sudo DOMAIN=foodguard.example.com EMAIL=you@example.com bash deploy/install-vhost.sh
#
# Optional env vars:
#   INSTALL_DIR    Default /opt/food-guard-ai
#   REPO_URL       Default https://github.com/wgmasvix-hue/food-guard-ai.git
#   BRANCH         Default claude/food-guard-ai-platform-z05ynw
#   API_HOST_PORT  Default 8001 (loopback port the API container publishes to)
#   WEB_HOST_PORT  Default 3000 (loopback port the web container publishes to)
#   SKIP_DNS_CHECK=1   Skip the "does DOMAIN resolve to this server" check
#   SKIP_SEED=1        Skip loading demo data
set -euo pipefail

DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"
INSTALL_DIR="${INSTALL_DIR:-/opt/food-guard-ai}"
REPO_URL="${REPO_URL:-https://github.com/wgmasvix-hue/food-guard-ai.git}"
BRANCH="${BRANCH:-claude/food-guard-ai-platform-z05ynw}"
API_HOST_PORT="${API_HOST_PORT:-8001}"
WEB_HOST_PORT="${WEB_HOST_PORT:-3000}"
WEBROOT="/var/www/foodguard-certbot"

log()  { printf '\033[1;32m[install]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

[[ $EUID -eq 0 ]] || die "Run this as root (sudo)."
[[ -n "$DOMAIN" ]] || die "Set DOMAIN, e.g.: DOMAIN=foodguard.example.com EMAIL=you@example.com bash deploy/install-vhost.sh"
[[ -n "$EMAIL"  ]] || die "Set EMAIL for Let's Encrypt notices, e.g.: EMAIL=you@example.com"

command -v docker >/dev/null || die "Docker is not installed."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin not found (try: apt install docker-compose-plugin)."
command -v nginx >/dev/null || die "nginx is not installed on the host — use deploy/install.sh instead (it runs its own nginx in Docker)."
systemctl is-active --quiet nginx || die "The host nginx service isn't running. Start it first (systemctl start nginx) or use deploy/install.sh."

# ---------- figure out where this nginx wants site configs ----------
if [[ -d /etc/nginx/sites-available && -d /etc/nginx/sites-enabled ]]; then
  NGINX_LAYOUT="sites"
  VHOST_PATH="/etc/nginx/sites-available/${DOMAIN}.conf"
  ENABLE_PATH="/etc/nginx/sites-enabled/${DOMAIN}.conf"
elif [[ -d /etc/nginx/conf.d ]]; then
  NGINX_LAYOUT="confd"
  VHOST_PATH="/etc/nginx/conf.d/${DOMAIN}.conf"
  ENABLE_PATH=""
else
  die "Could not find /etc/nginx/sites-available or /etc/nginx/conf.d — unfamiliar nginx layout, add the vhost manually using nginx/vhost/*.template as a reference."
fi
log "Detected nginx layout: $NGINX_LAYOUT (writing $VHOST_PATH)"

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
# Pin the host ports docker compose will publish to (read automatically from .env).
grep -q '^API_HOST_PORT=' .env && sed -i "s#^API_HOST_PORT=.*#API_HOST_PORT=${API_HOST_PORT}#" .env || echo "API_HOST_PORT=${API_HOST_PORT}" >> .env
grep -q '^WEB_HOST_PORT=' .env && sed -i "s#^WEB_HOST_PORT=.*#WEB_HOST_PORT=${WEB_HOST_PORT}#" .env || echo "WEB_HOST_PORT=${WEB_HOST_PORT}" >> .env

# ---------- start app containers only (no dockerized nginx) ----------
log "Building and starting db, api, web (nginx is the host's, not Docker's)..."
docker compose up -d --build db api web

log "Waiting for the API to become healthy on 127.0.0.1:${API_HOST_PORT}..."
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:${API_HOST_PORT}/health" >/dev/null 2>&1 && break
  sleep 2
  [[ $i -eq 30 ]] && warn "API did not respond within 60s — continuing anyway, check 'docker compose logs api' if the cert step fails."
done

# ---------- bootstrap HTTP vhost for the ACME challenge ----------
mkdir -p "$WEBROOT"
log "Writing bootstrap (HTTP-only) vhost..."
sed -e "s#__DOMAIN__#${DOMAIN}#g" -e "s#__API_PORT__#${API_HOST_PORT}#g" -e "s#__WEB_PORT__#${WEB_HOST_PORT}#g" -e "s#__WEBROOT__#${WEBROOT}#g" \
  nginx/vhost/foodguard.conf.http.template > "$VHOST_PATH"
[[ "$NGINX_LAYOUT" == "sites" ]] && ln -sf "$VHOST_PATH" "$ENABLE_PATH"
nginx -t || die "nginx config test failed for the vhost just written — check $VHOST_PATH"
systemctl reload nginx

# ---------- certificate ----------
command -v certbot >/dev/null || { log "Installing certbot..."; apt-get update -qq && apt-get install -y certbot; }

if [[ -d "/etc/letsencrypt/live/${DOMAIN}" ]]; then
  log "Certificate for $DOMAIN already exists — skipping issuance."
else
  log "Requesting a Let's Encrypt certificate for $DOMAIN..."
  certbot certonly --webroot -w "$WEBROOT" -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email --non-interactive \
    || die "Certificate issuance failed. Check that $DOMAIN really points here and port 80 is reachable from the internet, then re-run this script."
fi

# ---------- switch vhost to HTTPS ----------
log "Switching vhost to the HTTPS config..."
sed -e "s#__DOMAIN__#${DOMAIN}#g" -e "s#__API_PORT__#${API_HOST_PORT}#g" -e "s#__WEB_PORT__#${WEB_HOST_PORT}#g" -e "s#__WEBROOT__#${WEBROOT}#g" \
  nginx/vhost/foodguard.conf.ssl.template > "$VHOST_PATH"
nginx -t || die "nginx config test failed for the vhost just written — check $VHOST_PATH"
systemctl reload nginx

# ---------- renewal ----------
# Standard certbot packages already run renewal via a systemd timer/cron of
# their own (covering every domain on the box, not just this one) — we only
# need to make sure OUR vhost gets reloaded after a renewal. Certbot calls
# every script in this deploy-hook directory after a successful renewal.
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/food-guard-ai-reload-nginx.sh <<'EOF'
#!/bin/sh
systemctl reload nginx
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/food-guard-ai-reload-nginx.sh

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
