#!/usr/bin/env bash
# Installed by install.sh into /usr/local/bin and run daily via cron.
# Renews the Let's Encrypt cert (no-op if not due yet) and reloads nginx if renewed.
set -euo pipefail

INSTALL_DIR="__INSTALL_DIR__"
cd "$INSTALL_DIR"

docker run --rm \
  -v food-guard-ai_certbot-webroot:/var/www/certbot \
  -v food-guard-ai_certbot-etc:/etc/letsencrypt \
  certbot/certbot renew --webroot -w /var/www/certbot --quiet

docker compose exec -T nginx nginx -s reload
