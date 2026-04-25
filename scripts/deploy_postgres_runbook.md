# Deploy to 52.88.255.208 (skills.sclr.ac) — Postgres + Docker Hub Runbook

This is the multi-user prod deployment. SQLite → Postgres on the remote +
Docker Hub image push + IP-based learner URL.

**Per CLAUDE.md**: 52.88.255.208 IS skills.sclr.ac (shared with external team).
This deployment is the explicit user-greenlight v8 milestone.

---

## What this deploys

1. **Backend code changes** — most already in main (`DATABASE_URL` env override
   already exists in `backend/database.py`). New: `asyncpg` in
   `requirements.txt`; `tools/migrate_courses_to_target_db.py`.
2. **Postgres on the remote** — fresh install via apt, db + user created,
   schema bootstrapped via `backend.database.create_tables()`.
3. **Course content migration** — Kimi (`created-698e6399e3ca`) + Claude-Code
   (`created-7fee8b78c742`) only. Modules + steps cascade.
4. **Docker Hub image** — `skillslab:latest` (2.87 GB) pushed under the user's
   Docker Hub account; remote `cli/docker-compose.yml` updated to pull instead
   of build.
5. **Env config on the remote** — `DATABASE_URL`, `SKILLSLAB_API_URL`,
   `SKILLSLAB_WEB_URL`, `ANTHROPIC_BUDGET_USD` all set in `~/skills-lab-v2/.env`.

---

## Prereqs (USER provides)

| What | Why | How |
|---|---|---|
| SSH access to `ubuntu@52.88.255.208` | rsync code, run psql, restart service | `ssh-add ~/.ssh/sclr.pem` (or whatever the keyfile is) — verify with `ssh ubuntu@skills.sclr.ac hostname` |
| Docker Hub login | push image | `docker login` from your terminal once — saves auth to `~/.docker/config.json` |
| Docker Hub repo path | image tag target | e.g. `tusharbisht/skillslab` (image tag will be `tusharbisht/skillslab:terminal-first-2026-04-25`) |
| Confirm Postgres on remote | install if missing | I'll detect via `ssh ubuntu@... 'which psql'` and install if absent |

---

## Run order (after prereqs land)

### Step 0 — backup local SQLite (paranoia gate)

```bash
cd /Users/tushar/Desktop/codebases/skills-lab-v2
cp skills_lab.db skills_lab.db.pre-pg-deploy-$(date +%Y%m%d-%H%M%S)
```

### Step 1 — push image to Docker Hub

```bash
DOCKERHUB_USER=tusharbisht  # confirm with user
TAG=terminal-first-2026-04-25
docker tag skillslab:latest ${DOCKERHUB_USER}/skillslab:${TAG}
docker tag skillslab:latest ${DOCKERHUB_USER}/skillslab:latest
docker push ${DOCKERHUB_USER}/skillslab:${TAG}
docker push ${DOCKERHUB_USER}/skillslab:latest
```

### Step 2 — install Postgres on the remote (if not present)

```bash
ssh ubuntu@52.88.255.208 << 'EOF'
set -euo pipefail
if ! which psql >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl enable --now postgresql
fi

# Create DB + user (idempotent)
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'skillslab'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE skillslab;"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = 'skillslab'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER skillslab WITH PASSWORD 'CHANGE_ME_REAL_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE skillslab TO skillslab;"
sudo -u postgres psql -d skillslab -c "GRANT ALL ON SCHEMA public TO skillslab;"

# Confirm
sudo -u postgres psql -d skillslab -c "\\dt"
EOF
```

### Step 3 — push code to remote

```bash
# From local repo root:
./scripts/deploy_sclr.sh   # existing rsync script — pushes backend/ + frontend/ + scripts/

# Then on remote: install asyncpg
ssh ubuntu@52.88.255.208 'cd ~/skills-lab-v2 && .venv/bin/pip install asyncpg==0.29.0'
```

### Step 4 — set env on remote + bootstrap PG schema

```bash
ssh ubuntu@52.88.255.208 << 'EOF'
set -euo pipefail
cd ~/skills-lab-v2
# Edit .env with prod values:
cat > .env.prod-additions << 'ENVEOF'
DATABASE_URL=postgresql+asyncpg://skillslab:CHANGE_ME_REAL_PASSWORD@localhost:5432/skillslab
SKILLSLAB_API_URL=http://52.88.255.208
SKILLSLAB_WEB_URL=http://52.88.255.208
ANTHROPIC_BUDGET_USD=350
ENVEOF
# Append (don't overwrite — preserves ANTHROPIC_API_KEY etc.)
cat .env.prod-additions >> .env
sort -u -t= -k1,1 .env -o .env  # dedupe by key
rm .env.prod-additions

# Bootstrap schema on PG
DATABASE_URL='postgresql+asyncpg://skillslab:CHANGE_ME_REAL_PASSWORD@localhost:5432/skillslab' \
  .venv/bin/python -c "import asyncio; from backend.database import create_tables; asyncio.run(create_tables())"

# Verify
sudo -u postgres psql -d skillslab -c "\\dt"
EOF
```

### Step 5 — migrate Kimi + Claude-Code from local SQLite to remote PG

From the local machine:

```bash
# Tunnel to remote PG via SSH (5433 local → 5432 remote)
ssh -N -L 5433:localhost:5432 ubuntu@52.88.255.208 &
SSH_PID=$!
sleep 2

cd /Users/tushar/Desktop/codebases/skills-lab-v2

# Dry-run first
.venv/bin/python -m tools.migrate_courses_to_target_db \
    --source 'sqlite+aiosqlite:///./skills_lab.db' \
    --target 'postgresql+asyncpg://skillslab:CHANGE_ME_REAL_PASSWORD@localhost:5433/skillslab' \
    --course-ids created-698e6399e3ca created-7fee8b78c742 \
    --dry-run

# If counts look right, drop --dry-run
.venv/bin/python -m tools.migrate_courses_to_target_db \
    --source 'sqlite+aiosqlite:///./skills_lab.db' \
    --target 'postgresql+asyncpg://skillslab:CHANGE_ME_REAL_PASSWORD@localhost:5433/skillslab' \
    --course-ids created-698e6399e3ca created-7fee8b78c742

kill $SSH_PID
```

### Step 6 — restart service + smoke

```bash
ssh ubuntu@52.88.255.208 << 'EOF'
sudo systemctl restart skills-lab.service
sleep 3
sudo systemctl status skills-lab.service --no-pager | head -10
EOF

# Smoke from local:
curl -s http://impact:getshitdone@52.88.255.208/api/courses | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(f'courses: {len(d.get(\"courses\",[]))}'); [print(' ', c['id'], '|', c['title']) for c in d.get('courses',[]) if c['id'] in ('created-698e6399e3ca','created-7fee8b78c742')]"
```

### Step 7 — Docker Hub image swap on remote (cli usage)

```bash
ssh ubuntu@52.88.255.208 << 'EOF'
cd ~/skills-lab-v2/cli
# Update docker-compose.yml: change `build:` to `image: tusharbisht/skillslab:latest`
# (manual edit OR sed — the build block is ~5 lines)

# Test pull:
docker compose pull skillslab
docker compose run --rm skillslab skillslab --version
EOF
```

### Step 8 — multi-user smoke

```bash
# Register two synthetic learners against the prod DB:
for name in alice bob; do
    curl -s -X POST http://impact:getshitdone@52.88.255.208/api/auth/register \
        -H 'Content-Type: application/json' \
        -d "{\"email\":\"${name}@deploy-smoke.com\",\"password\":\"smoke-test-${name}\"}"
done

# Verify both rows in PG (each should be a separate user):
ssh ubuntu@52.88.255.208 \
    "sudo -u postgres psql -d skillslab -c 'SELECT id, email FROM users WHERE email LIKE %@deploy-smoke.com%'"
```

---

## Rollback plan

If anything breaks at step 5/6/7:

1. `sudo systemctl stop skills-lab.service` on remote
2. Edit `~/skills-lab-v2/.env` — comment out `DATABASE_URL` (falls back to SQLite)
3. `sudo systemctl start skills-lab.service`
4. Service is back on SQLite; PG sits idle.

The existing `~/skills-lab-v2/skills_lab.db` is untouched throughout —
no destructive operations on it. Local SQLite backup is the second safety net.

---

## What stays SQLite

- **Local dev** — no env override; defaults to `sqlite+aiosqlite:///./skills_lab.db`
- **`18.236.242.248`** (the same machine, different DNS) — also picks up
  `DATABASE_URL` env from `~/skills-lab-v2/.env`; if you want THAT URL
  to keep using SQLite for some reason, partition by hostname (not done here
  because it's the same machine + same .env).
