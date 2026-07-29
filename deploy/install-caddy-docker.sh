#!/usr/bin/env bash
# Food Guard AI — installer for a server where Caddy itself runs in a
# Docker container (e.g. the "chengetai-caddy" container from ChengetAi
# Deploy) rather than as a host service. That Caddy reaches other
# containers by container DNS name on a shared Docker network (the same
# way its existing config reverse_proxies to e.g. "dspace:8080") — so
# unlike deploy/install-caddy.sh (host-installed Caddy reaching
# 127.0.0.1:<port>), this script attaches api/web to that same network
# and points Caddy at them by container name instead.
#
# Usage:
#   sudo DOMAIN=foodguard.example.com \
#        CADDY_CONTAINER=chengetai-caddy \
#        CADDY_NETWORK=chengetai-dare_dspacenet \
#        CADDYFILE_HOST_PATH=/opt/chengetai-deploy/deployments/dare/engine/caddy/Caddyfile \
#        bash deploy/install-caddy-docker.sh
#
# Optional env vars:
#   INSTALL_DIR            Default /opt/food-guard-ai
#   REPO_URL                Default https://github.com/wgmasvix-hue/food-guard-ai.git
#   BRANCH                  Default claude/food-guard-ai-platform-z05ynw
#   API_HOST_PORT           Default 8001 (loopback-only, for your own debugging — Caddy doesn't use this)
#   WEB_HOST_PORT           Default 3001 (loopback-only, for your own debugging — Caddy doesn't use this)
#   CADDYFILE_CONTAINER_PATH  Default /etc/caddy/Caddyfile (path INSIDE the Caddy container)
#   SKIP_DNS_CHECK=1        Skip the "does DOMAIN resolve to this server" check
#   SKIP_SEED=1             Skip loading demo data
set -euo pipefail

DOMAIN="${DOMAIN:-}"
CADDY_CONTAINER="${CADDY_CONTAINER:-}"
CADDY_NETWORK="${CADDY_NETWORK:-}"
CADDYFILE_HOST_PATH="${CADDYFILE_HOST_PATH:-}"
CADDYFILE_CONTAINER_PATH="${CADDYFILE_CONTAINER_PATH:-/etc/caddy/Caddyfile}"
INSTALL_DIR="${INSTALL_DIR:-/opt/food-guard-ai}"
REPO_URL="${REPO_URL:-https://github.com/wgmasvix-hue/food-guard-ai.git}"
BRANCH="${BRANCH:-claude/food-guard-ai-platform-z05ynw}"
API_HOST_PORT="${API_HOST_PORT:-8001}"
WEB_HOST_PORT="${WEB_HOST_PORT:-3001}"

log()  { printf '\033[1;32m[install]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$1"; exit 1; }

[[ $EUID -eq 0 ]] || die "Run this as root (sudo)."
[[ -n "$DOMAIN" ]] || die "Set DOMAIN, e.g.: DOMAIN=foodguard.example.com"
[[ -n "$CADDY_CONTAINER" ]] || die "Set CADDY_CONTAINER to the name of your running Caddy container (docker ps to find it)."
[[ -n "$CADDY_NETWORK" ]] || die "Set CADDY_NETWORK to the Docker network that container is on (docker inspect \$CADDY_CONTAINER --format '{{range \$k,\$v := .NetworkSettings.Networks}}{{\$k}}{{\"\\n\"}}{{end}}')."
[[ -n "$CADDYFILE_HOST_PATH" ]] || die "Set CADDYFILE_HOST_PATH to the Caddyfile's path on the HOST (docker inspect \$CADDY_CONTAINER --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{\"\\n\"}}{{end}}')."
[[ -f "$CADDYFILE_HOST_PATH" ]] || die "$CADDYFILE_HOST_PATH does not exist."

command -v docker >/dev/null || die "Docker is not installed."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin not found."
[[ "$(docker inspect -f '{{.State.Running}}' "$CADDY_CONTAINER" 2>/dev/null)" == "true" ]] \
  || die "Container '$CADDY_CONTAINER' is not running (docker ps to check)."
docker network inspect "$CADDY_NETWORK" >/dev/null 2>&1 \
  || die "Docker network '$CADDY_NETWORK' not found (docker network ls to check)."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.caddy-network.yml"

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
# These are only for your own host-side debugging (curl localhost:...) —
# Caddy talks to the containers over $CADDY_NETWORK by name, not via these.
current_mapped_port() {  # $1 = service name, $2 = container port
  $COMPOSE port "$1" "$2" 2>/dev/null | sed -E 's/.*:([0-9]+)$/\1/'
}
API_CURRENT_PORT="$(current_mapped_port api 8000 || true)"
WEB_CURRENT_PORT="$(current_mapped_port web 3000 || true)"

check_port_free() {
  local wanted="$1" current="$2"
  [[ -n "$current" && "$wanted" == "$current" ]] && return 0
  if ss -ltn "( sport = :$wanted )" | grep -q LISTEN; then
    die "Port $wanted is already in use. Pick a free one: API_HOST_PORT=... WEB_HOST_PORT=... (re-run with different values)."
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

# ---------- start app containers, attached to Caddy's network ----------
log "Building and starting db, api, web (attached to $CADDY_NETWORK for Caddy to reach)..."
CADDY_NETWORK="$CADDY_NETWORK" $COMPOSE up -d --build db api web

log "Waiting for the API to become healthy on 127.0.0.1:${API_HOST_PORT}..."
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:${API_HOST_PORT}/health" >/dev/null 2>&1 && break
  sleep 2
  [[ $i -eq 30 ]] && warn "API did not respond within 60s — continuing anyway, check 'docker compose logs api'."
done

# ---------- Caddy site block (container names, container-internal ports) ----------
MARKER="# food-guard-ai:${DOMAIN}"
if grep -qF "$MARKER" "$CADDYFILE_HOST_PATH"; then
  log "Site block for $DOMAIN already present — leaving it as-is (edit $CADDYFILE_HOST_PATH manually if anything changed)."
else
  log "Appending site block to $CADDYFILE_HOST_PATH..."
  cp "$CADDYFILE_HOST_PATH" "${CADDYFILE_HOST_PATH}.bak.$(date +%s)"
  cat >> "$CADDYFILE_HOST_PATH" <<EOF

${MARKER}
${DOMAIN} {
    encode gzip

    handle /api/* {
        reverse_proxy food-guard-ai-api:8000
    }

    handle {
        reverse_proxy food-guard-ai-web:3000
    }
}
EOF
fi

log "Validating Caddy config..."
docker exec "$CADDY_CONTAINER" caddy validate --config "$CADDYFILE_CONTAINER_PATH" --adapter caddyfile \
  || die "Caddy config is invalid — check $CADDYFILE_HOST_PATH (a .bak backup was made before appending)."

log "Reloading Caddy..."
docker exec "$CADDY_CONTAINER" caddy reload --config "$CADDYFILE_CONTAINER_PATH" --adapter caddyfile

# ---------- backups + health monitoring ----------
log "Installing nightly backups (02:30) and health-check alerts (every 5 min)..."
install -m 755 deploy/backup.sh /usr/local/bin/food-guard-ai-backup.sh
sed -i "s#__INSTALL_DIR__#${INSTALL_DIR}#g" /usr/local/bin/food-guard-ai-backup.sh
install -m 755 deploy/healthcheck-alert.sh /usr/local/bin/food-guard-ai-healthcheck.sh
sed -i "s#__INSTALL_DIR__#${INSTALL_DIR}#g" /usr/local/bin/food-guard-ai-healthcheck.sh
cat > /etc/cron.d/food-guard-ai-ops <<EOF
30 2 * * * root /usr/local/bin/food-guard-ai-backup.sh >> /var/log/food-guard-ai-backup.log 2>&1
*/5 * * * * root /usr/local/bin/food-guard-ai-healthcheck.sh >> /var/log/food-guard-ai-healthcheck.log 2>&1
EOF

# ---------- seed demo data ----------
if [[ "${SKIP_SEED:-0}" != "1" ]]; then
  log "Loading demo data (safe to re-run; skips if already seeded)..."
  $COMPOSE exec -T api python -m app.db.seed || warn "Seeding failed or already seeded — check with: docker compose logs api"
fi

log "Done. Food Guard AI should now be live at: https://${DOMAIN}"
log "(Caddy issues the certificate on first request — the very first page load may take a few extra seconds.)"
log "API docs: https://${DOMAIN}/api/v1/docs"
log ""
log "IMPORTANT: this deployed the '${BRANCH}' branch directly (not yet merged to main)."
log "Review it and merge to main via a PR when you're ready to treat it as the production baseline."
