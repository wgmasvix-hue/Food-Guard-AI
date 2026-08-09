# Operations Runbook

This covers what to do after FoodOS is installed and live: backups,
restores, monitoring, log/resource limits, and updating the deployment.
See `docs/INSTALL.md` for first-time setup.

All commands below assume the standard install path, `/opt/food-guard-ai`
(override with `INSTALL_DIR` if you installed elsewhere).

## What gets installed automatically

Every `deploy/install*.sh` script now installs, in addition to the app
itself:

| What | Runs | Installed as |
|---|---|---|
| Nightly backup | `30 2 * * *` (02:30) | `/usr/local/bin/food-guard-ai-backup.sh` |
| Health-check alert | every 5 minutes | `/usr/local/bin/food-guard-ai-healthcheck.sh` |
| Cert renewal (`install.sh`/`install-vhost.sh` only) | daily, 03:15 | `/usr/local/bin/food-guard-ai-renew.sh` |

All three are registered via `/etc/cron.d/food-guard-ai-ops` (and
`food-guard-ai-renew` for the cert timer), logging to
`/var/log/food-guard-ai-*.log`.

## Backups

`deploy/backup.sh` runs nightly and:
1. `pg_dump`s the database in custom (`-Fc`) format.
2. Archives the uploads volume (evidence photos, attachments) as a tarball.
3. Writes both into `$INSTALL_DIR/backups/`, timestamped.
4. Deletes anything older than `BACKUP_RETENTION_DAYS` (`.env`, default 14).

**These backups live on the same disk as the app.** A disk failure takes
out the app and its backups together — copy `$INSTALL_DIR/backups/`
somewhere else on a schedule. See "Offsite backups" below for the
built-in way to do that automatically.

Run a backup on demand:

```bash
sudo /usr/local/bin/food-guard-ai-backup.sh
```

### Offsite backups

`deploy/backup.sh` can push each night's dump + uploads tarball to any
[rclone](https://rclone.org) remote (S3, Backblaze B2, Google Drive, SFTP,
another server, ...) right after the local backup completes. It's opt-in
and off by default — nothing changes until you configure it, and if the
offsite push ever fails the local backup still succeeds (you get a
warning in the log, not a failed backup job).

To enable it:

1. Install rclone on the server: `curl https://rclone.org/install.sh | sudo bash`
2. Configure a remote interactively: `rclone config` (pick your provider,
   follow the prompts — this stores credentials in
   `~/.config/rclone/rclone.conf` for whichever user cron runs backups as,
   typically root).
3. Set `BACKUP_RCLONE_REMOTE` in `.env` to `<remote-name>:<path>`, e.g.:
   ```bash
   BACKUP_RCLONE_REMOTE=s3-backup:my-bucket/food-guard-ai
   ```
4. Run a backup manually once to confirm the sync works:
   ```bash
   sudo /usr/local/bin/food-guard-ai-backup.sh
   ```
   You should see `[backup] Syncing ... [backup] Offsite sync complete.`
   in the output.

From then on, every nightly backup also syncs to the remote
(`rclone sync`, so deleted/pruned local files are reflected there too —
the remote mirrors `$INSTALL_DIR/backups/`, it isn't a separate
ever-growing archive).

### Restoring

`deploy/restore.sh` is manual and destructive — never cron'd. It stops the
API, restores the database (and optionally the uploads volume), then
starts the API back up:

```bash
cd /opt/food-guard-ai
sudo bash deploy/restore.sh backups/db-20260729-023000.dump backups/uploads-20260729-023000.tar.gz
```

You'll be prompted to type `YES` to confirm (or set `CONFIRM=YES` for
non-interactive use, e.g. scripted disaster recovery). Test this
procedure on a spare box periodically — an untested restore path is not
a backup strategy.

## Health monitoring

`deploy/healthcheck-alert.sh` checks `/health` (which itself verifies
database connectivity, not just that the process is up) every 5 minutes.
After 2 consecutive failures it emails `ALERT_EMAIL` using the `SMTP_*`
settings in `.env`, and sends a follow-up when it recovers. If
`ALERT_EMAIL`/`SMTP_HOST` aren't set, failures are still logged to
`/var/log/food-guard-ai-healthcheck.log` — worth wiring into whatever
monitoring (Uptime Kuma, Healthchecks.io, Nagios, etc.) you already run
elsewhere on the box, since this script is a minimum-viable safety net,
not a full monitoring stack.

Check current status by hand:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
# {"status": "ok", "service": "FoodOS", "database": "ok"}
```

## Logs and disk usage

All containers use the `json-file` driver capped at 10 MB × 3 files
each (`docker-compose.yml`), so container logs can't silently fill the
disk. View them with the usual:

```bash
docker compose logs -f api
docker compose logs -f --tail 200 web
```

Cron job logs (`/var/log/food-guard-ai-*.log`) are **not** rotated by
this repo — add them to `logrotate` if they're not already covered by
your distro's default `/var/log` rotation:

```bash
cat > /etc/logrotate.d/food-guard-ai <<'EOF'
/var/log/food-guard-ai-*.log {
  weekly
  rotate 8
  compress
  missingok
  notifempty
}
EOF
```

## Resource limits

Each container has a memory/CPU cap (`docker-compose.yml`, tunable via
`.env`) so nothing here can starve other workloads on a shared host, or
each other:

| Service | Default memory | Default CPU |
|---|---|---|
| `db` | 1g | 1.0 |
| `api` | 1g | 1.0 |
| `web` | 512m | 0.5 |
| `nginx` | 128m | 0.5 |
| `ollama` | 4g | 2.0 |

If a container gets OOM-killed (`docker compose logs <service>` will show
it exiting with no obvious error, and `docker inspect <container> --format
'{{.State.OOMKilled}}'` confirms it), raise the matching `*_MEM_LIMIT` in
`.env` and `docker compose up -d` to apply. On a dedicated box with spare
RAM/CPU, raising these (especially `OLLAMA_MEM_LIMIT` if you're running
larger models) is safe and expected.

`API_WORKERS` (default 1) controls uvicorn worker processes — raise it on
a dedicated box with spare CPU (roughly 2× vCPU cores), keep it at 1 on a
shared host running other services.

## Updating / redeploying

Re-run whichever installer you used originally — all four are safe to
re-run and will pull the latest commit of `BRANCH`, rebuild changed
images, and restart:

```bash
cd /opt/food-guard-ai
sudo DOMAIN=foodguard.example.com bash deploy/install-caddy.sh   # or install.sh / install-vhost.sh / install-caddy-docker.sh
```

To roll back, check out an earlier commit before re-running:

```bash
cd /opt/food-guard-ai
git log --oneline -10
git checkout <earlier-commit-sha>
docker compose up -d --build db api web
```

## Certificate renewal

Handled automatically:
- `install.sh`: dockerized certbot, renewed via cron (`food-guard-ai-renew.sh`, daily 03:15).
- `install-vhost.sh`: host certbot's own timer/cron renews it (covers every vhost on the box), with a deploy-hook reloading nginx after renewal.
- `install-caddy.sh` / `install-caddy-docker.sh`: Caddy renews its own certs automatically, no cron needed.

## Multi-tenancy and data isolation

Every domain model that stores company-specific data is scoped by
`company_id`, and API queries filter on it — verify this holds for any
new endpoint you add before treating it as safe for multiple companies
on one instance. There is currently no cross-tenant admin view; a Super
Admin account can see across companies by design (see `docs/ARCHITECTURE.md`).

## Incident checklist

1. Check `docker compose ps` — is anything restarting in a loop?
2. `docker compose logs --tail 100 <service>` for the failing one.
3. `curl http://127.0.0.1:8000/health` — is the database reachable?
4. Check `/var/log/food-guard-ai-healthcheck.log` for when it started failing.
5. If it's a bad deploy: roll back (see above).
6. If it's data corruption/loss: restore from the most recent backup (see above).
