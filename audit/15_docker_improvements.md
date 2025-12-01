```markdown
**TL;DR (deutsch)**
- Diese Datei fasst konkrete Verbesserungen an `backend/Dockerfile`, `backend/entrypoint.sh`, `frontend/Dockerfile`, `docker-compose.yml` und `docker-compose.dev.yml` zusammen.
- Ziel: geringerer Image‑Footprint, weniger RAM/Swap‑Verbrauch in Produktion, bessere startup‑/shutdown‑Signale, sichere migration/entrypoint‑praxis, zuverlässigere healthchecks und produktionsgeeignete Compose‑Konfiguration.

Hinweis: Viele `deploy:`-Ressourcen‑Blöcke in `docker-compose.yml` wirken nur unter Swarm/Kubernetes; wenn ihr docker‑compose (lokal/host) verwendet, gelten andere Felder (`mem_limit`, `cpus`) oder ein orchestrator ist zu bevorzugen.

1) Kurzbefund — was ich in den Dateien gesehen habe
- Backend `Dockerfile`:
  - Multi‑stage vorhanden (good). Base stage installiert build‑tools (`gcc`) und python deps in same stage used for runtime → image kann groß sein.
  - Development target uses `pip install` in base stage and copies full repo into image; both dev and prod stages reuse same base with system build deps installed.
  - Healthcheck + non‑root user present (good).
  - Production CMD uses `uvicorn ... --workers 4` which spawns multiple processes and increases memory footprint.
- `backend/entrypoint.sh`:
  - Runs migrations automatically on each start without concurrency protection; runs `sqlite3` `PRAGMA integrity_check` on every start which can be expensive.
  - Uses `set -e` but not `set -uo pipefail`; uses `exec "$@"` at end (good) so signals are forwarded.
- Frontend `Dockerfile`:
  - Multi‑stage: base (node:20-alpine), development, builder, production (nginx). Good split.
  - `builder` stage runs `npm ci` but `base` stage earlier copied package*.json once so caching ok.
  - Production stage uses `nginx:alpine` and copies built artifacts — no pruning of default files, no explicit gzip/brotli or cache headers.
- `docker-compose.yml` (prod):
  - Uses `deploy.resources` blocks (only effective in swarm). Restart and volumes configured.
  - Stores SQLite as local volume (warning: sqlite in multi‑container/replicated env is not safe; suitable only for single‑node deployments).
- `docker-compose.dev.yml` (dev):
  - Uses bind mounts for code and node_modules; good for dev but watch out for mixing file modes on different hosts.


2) Konkrete Verbesserungen – Backend Dockerfile (Ziel: kleineres Image, weniger RAM/Startkosten)

A. Multi‑stage optimieren (Build-time deps nur in Builder)
- Aktuell: `base` installiert `gcc` und pip deps and is reused as runtime image. Besser:
  - Stage `builder`: install build deps (gcc, libpq-dev / build-base), run `pip wheel -r requirements.txt -w /wheels` or `pip wheel` to create wheels.
  - Stage `runtime`: start from `python:3.11-slim` (or `python:3.11-slim-bullseye`), copy only wheels and `requirements.txt`, `pip install --no-cache-dir /wheels/*` and remove apt caches. So runtime does NOT contain build tools.

Beispiel (sketch):
```dockerfile
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y build-essential gcc libffi-dev musl-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt
COPY . .

FROM python:3.11-slim AS runtime
WORKDIR /app
# create non-root user, create app dir
RUN useradd -m appuser && mkdir -p /app && chown appuser:appuser /app
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/*
COPY --chown=appuser:appuser . /app
USER appuser
```

Vorteile: deutlich kleinere Produktions‑Image, keine build‑tool‑overhead im finalen Image.

B. PIP Optimierungen
- Verwende `pip install --no-cache-dir` und setze ENV `PIP_NO_CACHE_DIR=1` und `PYTHONUNBUFFERED=1` / `PYTHONDONTWRITEBYTECODE=1` für deterministisches Verhalten.
- Nutze `requirements.txt` mit pinned versions to improve cache/predictability.

C. Start‑Command & worker sizing
- `uvicorn --workers 4` startet mehrere processes; reduziert memory under container constraints by tuning workers to CPU. Use formula:
  - `WEB_CONCURRENCY=${WEB_CONCURRENCY:-$(expr $(nproc) \* 2 + 1)}` or environment-based value.
- Consider running Gunicorn with Uvicorn workers to manage worker lifecycle: e.g.
```sh
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:8000 --log-level info
```
- For IO‑bound apps (FastAPI mostly IO) a smaller number of workers may be fine — benchmark.

D. Reduce memory per worker
- Avoid many workers in low‑memory containers. If memory limit is 512MB set in compose, choose `WEB_CONCURRENCY=1-2`.

E. Use smaller base image with precautions
- `python:3.11-slim` is good. `alpine` is smaller but many Python wheels are not musl‑compatible; prefer slim unless you manage build dependencies.

F. Healthchecks & readiness
- Keep healthchecks but use lightweight endpoints (e.g., `/health/ready`) that check only liveness or quick DB ping instead of expensive integrity checks.


3) Konkrete Verbesserungen – `entrypoint.sh` (Start/Init behaviour)

A. Robustere shell flags & safe defaults
- Use `set -euo pipefail` to fail on unset vars and errors in pipelines.
- Validate `$DATABASE_URL` exists and fail fast with clear message.

B. Avoid heavy checks every start
- Integrity checks and full migrations on each start can be slow. Suggestions:
  - Only run migrations automatically with an opt‑in env var `AUTO_MIGRATE=true` (default false in production). Require operator to run migrations in controlled window.
  - If auto‑migration is enabled, acquire a lock to avoid race conditions when multiple replicas start (use `flock` on a lockfile or rely on DB advisory locks if using Postgres).

C. SQLite specific notes
- SQLite is not recommended for production with concurrent containers. If you must keep sqlite:
  - Enable WAL mode and suitable pragmas to improve concurrency:
    ```sql
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    PRAGMA temp_store=MEMORY;
    ```
  - But still prefer Postgres for production.

D. Avoid integrity_check on every start
- `PRAGMA integrity_check` can be expensive for large DB files. Run it as part of scheduled maintenance, not on each container boot.

E. Proper signal forwarding & PID 1 behavior
- The script executes `exec "$@"` — good. Ensure `entrypoint.sh` doesn’t trap signals inadvertently. Use `exec` to run the server as PID 1 (already done) so signals reach the process.

F. Example safer header for entrypoint:
```bash
#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"
: "${AUTO_MIGRATE:=false}"

# create dir only when necessary
# acquire lock if migrating
if [ "$AUTO_MIGRATE" = "true" ]; then
  # use flock or run migration command guarded
  if command -v flock >/dev/null 2>&1; then
    exec 9>/var/lock/moneytracker-migrate.lock
    flock -n 9 || { echo "Another migration is running"; exit 0; }
    python "$MIGRATION_RUNNER"
  else
    python "$MIGRATION_RUNNER"
  fi
fi

exec "$@"
```


4) SQLite vs production DB
- Recommendation: switch to Postgres or MySQL for production for concurrency/backup/restore and smaller memory/lock surprises.
- If switching to Postgres, use a managed DB or a separate container/service; mount proper credentials, use connection pooling (pgbouncer) to limit DB connection count.


5) Frontend Dockerfile – Verbesserungen (Build/Runtime Größe & Performance)

A. Keep multi‑stage but ensure caching and small final image
- You're already doing multi‑stage. Ensure `COPY package*.json` prior to `npm ci` to leverage cache.
- Use `npm ci --production` in final stage if possible; but builder should run `npm ci` (dev deps) then final copy only `dist` files into nginx image.

B. Use `npm ci` not `npm install` in development for reproducible installs.
- In dev stage they used `npm install` — that's fine for dev, but `npm ci` is preferable if lockfile exists.

C. Optimize Nginx for static hosting
- Enable gzip and brotli compression, add cache headers, set `etag` and `expires` for static assets.
- Example nginx snippet:
```nginx
location / {
  try_files $uri /index.html;
  gzip on;
  gzip_types text/plain application/javascript text/css application/json;
  add_header Cache-Control "public, max-age=31536000, immutable";
}
```
- Consider precompressing assets at build time (brotli/gzip) and configure nginx to serve them.

D. Reduce final image size
- Use `nginx:alpine` (already used) but make sure to remove default files if not needed.


6) docker-compose.yml & docker-compose.dev.yml – Verbesserungen für Memory / Performance

A. `deploy.resources` is ignored by local `docker-compose`
- Note: `deploy` is for swarm. For docker-compose v2 behavior use `mem_limit` / `cpus` (compose v2) or run under a proper orchestrator.
- Example for local compose (older formats):
```yaml
services:
  backend:
    mem_limit: 512m
    cpus: 0.5
    ulimits:
      nproc: 65535
```
B. Logging and disk limits
- Add `logging` options to avoid unbounded logs filling disk:
```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```
C. Healthcheck & depends_on
- Use `depends_on: condition: service_healthy` in Compose v2.1 if you want Compose to wait for healthcheck.
D. Restart & update policies
- Keep `restart: unless-stopped` for prod. For rolling updates use orchestrator.

E. Volume considerations for sqlite
- If you must keep sqlite, ensure volume is on fast disk and backup schedule exists. Don't use bind mount for production DB.

F. Example snippet adding limits & logging
```yaml
services:
  backend:
    image: ...
    mem_limit: 512m
    cpus: 0.75
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
```


7) Runtime tips to minimize RAM usage
- Lower `WEB_CONCURRENCY` / workers to match memory budget; choose 1–2 workers for small nodes.
- Use async I/O (FastAPI is async): prefer fewer workers and rely on asyncio concurrency for many simultaneous connections.
- Configure GC on Python if you observe memory growth (e.g., `PYTHONMALLOC` or `gc` tuning) — but profile first.
- Avoid running heavy batch work in the same container as the API (use background worker processes / separate containers with controlled memory).


8) Security & best practices (short)
- Run non‑root (already present) and minimize SUID programs.
- Drop capabilities where possible and run containers read‑only (`read_only: true`) with explicit writable volumes.
- Ensure `.env` is not committed; use secrets managers in production.


9) Checklist / Quick PRs you can apply immediately (ranked)
- [P0] Move build‑tools into a builder stage and produce a lean runtime image (see snippet above).
- [P0] Add `PIP_NO_CACHE_DIR=1`, `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1` envs in Dockerfile.
- [P0] Add `AUTO_MIGRATE=false` and gate migration run in `entrypoint.sh` behind this env; use `flock` if enabled.
- [P0] Replace `uvicorn --workers 4` with a `WEB_CONCURRENCY` env var and default to a small worker count.
- [P1] Add `logging` options and `mem_limit` / `cpus` in `docker-compose.yml` (or run with an orchestrator that supports `deploy.resources`).
- [P1] Add nginx cache headers and compression for frontend and optionally precompress assets.
- [P2] Replace sqlite with Postgres for production deployments; add migration and backup plan.


10) Weiteres / Monitoring
- Add metrics (Prometheus) for job durations, job failures and import durations.
- Monitor container memory usage (cAdvisor) and set alerts for OOM kills.


Anhang — quick example patches (copy‑paste friendly)

A) Minimal change to backend CMD to use env var workers:
```dockerfile
ENV WEB_CONCURRENCY=2
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "${WEB_CONCURRENCY}", "-b", "0.0.0.0:8000", "app.main:app"]
```

B) Compose logging + mem_limit snippet:
```yaml
services:
  backend:
    image: ...
    mem_limit: 512m
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```