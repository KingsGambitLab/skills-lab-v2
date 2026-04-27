# MEMORY — design discussions to revisit

Park-bench notes that aren't ready to ship but shouldn't be forgotten.
Append-only; date entries; cross-link to related code/issues.

---

## 2026-04-27 — Org-grounded course customization

**Context**: User asked what documents an organization could upload to make Creator-generated courses ground in their stack, domain, and curriculum. Answer was YES, fully feasible today on the existing UI with 3 small structural adds.

### Three input axes that matter

| Axis | Best documents to upload | Why |
|---|---|---|
| **Tech stack + versions** | `pyproject.toml` / `package.json` / `pom.xml` / `Cargo.toml`; `Dockerfile`/`docker-compose.yml`; `.github/workflows/*.yml`; READMEs of 2-3 most-touched repos | Version pins ARE the grounding — deterministic, no LLM guessing |
| **Domain space** | 5-10 anonymized postmortems / RFCs / design docs; internal wiki exports (Confluence/Notion); sanitized PR descriptions; onboarding "first 90 days" handbook; service catalog | Captures the kinds of problems engineers face + names of systems to reference |
| **Module skeleton** | Curriculum / learning roadmap (1-pager, 4-7 modules); skill matrix / job ladder; existing internal training catalog | Structural shape of the course — what to teach in what order |

### What's already in place (works today, no changes needed)

- `/api/creator/upload` accepts PDF/DOCX/PPTX/TXT/MD; extracts text; feeds as `source_material`
- `_extract_canonical_entities()` pulls names/numbers/IDs from source; LLM is forbidden from inventing alternates
- 7 grounding rules in the per-step prompt ("don't invent names; quote source; don't rename frameworks")
- `_runtime_deps_brief(language)` injects pinned versions for the runner image
- Per-tool verified-facts blocks: `_claude_code_reference_facts`, `tech_schema_data.py`, `tech_docs/aider.md`
- Title-hint matching surfaces the right tool facts when course title mentions the tool

So: an org that uploads `pom.xml` + 5 postmortems + a 1-page outline TODAY gets a course where every exercise mentions their actual systems with their actual stack — at "good guess" quality, not deterministic.

### The 3 structural adds (1-2 days each, when we revisit)

1. **Org Profile schema** — accept tech stack + domain + module outline as STRUCTURED fields, not just blob source_material. Creator prompt has explicit slots ("the org's pinned stack: …", "the org's named systems: …", "the requested module outline: …") instead of "go find the relevant bits in this prose."

2. **Per-org KB** — extend the `tech_schema` pattern to `org_schema_data.py` keyed by `org_slug`. Holds:
   - allowlist (system names the LLM CAN reference)
   - forbidden_examples (e.g. "we don't use Stripe Connect")
   - drift regexes
   Plus `backend/org_facts/<org_slug>.md` for canonical doc text.

3. **Module-skeleton hard contract at outline stage** — `_llm_refined_outline` validates that the generated outline matches the requested module count + scope. Today it's a soft suggestion; we'd make it a HARD reject-and-retry if the outline drifts from what was requested.

### Knowledge base evolution model (already proven)

Same pattern we use for Claude Code + Aider:
- Canonical doc text in `backend/tech_docs/<tool>.md`
- Allowlist + forbidden_examples in `backend/tech_schema_data.py`
- Refresh job: re-extract from official docs, diff, human-in-the-loop merge

For per-org KB: same shape, keyed by org_slug. Refresh job re-ingests their wiki on a cadence. New facts diff against current KB before merge.

### UI implication

**No UI changes** for this. The existing `/api/creator/start` flow accepts the structured fields as additional optional inputs. The wizard upload step gets one extra section ("Upload your org profile") with file slots. Creator API knows how to consume them. Same render, same generate flow, same dashboard.

### Open questions when we revisit

- How does an org REGISTER itself + claim a slug? (today there's no org concept; courses are owned by `creator_user_id`)
- Multi-tenancy: does each org get its own tag-filtered catalog view, or do all courses live in one global pool?
- Privacy/compliance: org's uploaded docs probably contain proprietary info → at-rest encryption, retention policy, who-can-read access controls
- Revenue model: per-seat? per-course-generated? unlimited under contract?

### Code references for next session

- `backend/main.py:_extract_canonical_entities` — entity pull
- `backend/main.py:_runtime_deps_brief` — pattern for stack injection
- `backend/main.py:_claude_code_reference_facts` — pattern for tool facts
- `backend/tech_schema_data.py` — registry pattern to mirror for org KB
- `backend/main.py:_llm_refined_outline` — where outline contract would tighten
- `frontend/index.html` — wizard upload step (no changes; just one new section)

---

## 2026-04-27 — Deploy + SQLite→Postgres migration playbook

**Why this is in MEMORY**: deployments happen rarely (per box, per migration round), so the steps fall out of muscle memory between rounds. CLAUDE.md has the brief version (top H2 "🚀 DEPLOY PLAYBOOK"); this is the verbose version with gotchas + lessons.

**Status as of 2026-04-27**:
- `52.88.255.208` — fully migrated (Phase 1 + Phase 2). Live on PG15.
- `skills.sclr.ac` — still on SQLite. Replay both phases when ready.

### Pre-flight (every deploy, regardless of phase)

```bash
# SSH key + user
KEY=~/Downloads/ai-agent-demo.pem
USER=ec2-user      # NOT ubuntu — Amazon Linux 2023
HOST=52.88.255.208 # or skills.sclr.ac, etc.

ssh -i $KEY $USER@$HOST "uname -a; df -h / | tail -1"
```

If SSH fails: the key file might not be `chmod 400`. `chmod 400 $KEY`.

### Phase 1 — Code rsync + service restart (SQLite stays as-is)

```bash
# 1. Stop service to avoid mid-write races
ssh -i $KEY $USER@$HOST "sudo systemctl stop skills-lab.service"

# 2. Rsync code. CRITICAL EXCLUDES — never include these:
#    .db-shm / .db-wal — past WAL state on remote can be corrupted by
#    rsync overlaying our local WAL files. The .db file alone is
#    usually fine to leave untouched (we exclude it explicitly too).
#    .anthropic_budget.json — local spend tracking, would clobber prod.
#    reviews/ — agent artifacts; not deployable.
rsync -az --delete \
  --exclude={'.venv','.git','__pycache__','*.pyc','skills_lab.db','*.db-journal','*.db-wal','*.db-shm','.anthropic_budget.json','.skillslab','reviews','.claude','node_modules'} \
  -e "ssh -i $KEY" ./ $USER@$HOST:/home/ec2-user/skills-lab-v2/

# 3. Pip install missing deps (every fresh deploy — venv may be stale)
ssh -i $KEY $USER@$HOST "
  cd /home/ec2-user/skills-lab-v2
  .venv/bin/pip install -q -r requirements.txt
  # email-validator was missing on .208 first deploy — keep this line
  .venv/bin/pip install -q 'pydantic[email]' email-validator
"

# 4. Schema migration is AUTOMATIC. backend/database.py:_ensure_column
#    runs at startup; engine-agnostic since 2026-04-27 (uses
#    sqlalchemy.inspect, not PRAGMA). New columns ALTER on first boot.

# 5. nginx — scope basic auth to / only. /api/* + /templates/* MUST be
#    open (CLI uses Bearer auth; basic-auth-everywhere breaks the CLI).
ssh -i $KEY $USER@$HOST 'sudo tee /etc/nginx/conf.d/skills-lab.conf' << 'NGX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    client_max_body_size 30M;
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
    location /templates/ {
        proxy_pass http://127.0.0.1:8001/templates/;
        proxy_set_header Host $host;
    }
    location / {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGX_EOF
ssh -i $KEY $USER@$HOST "sudo nginx -t && sudo systemctl reload nginx"

# 6. Restart + smoke
ssh -i $KEY $USER@$HOST "sudo systemctl restart skills-lab.service"
sleep 5
curl -s http://$HOST/api/courses | jq 'length'   # should be > 0
curl -s -o /dev/null -w "/: %{http_code}\n" http://$HOST/  # 401 (basic auth)
curl -s -o /dev/null -w "/api/courses: %{http_code}\n" http://$HOST/api/courses  # 200
```

**Phase 1 gotchas seen on 52.88.255.208**:
- **Corrupt 134MB WAL**: an old `skills_lab.db-wal` had un-replayable writes; `sqlite3` reported "database disk image is malformed." Recovery: move the .wal + .shm files aside; the .db file alone is intact. (Lost some learner-progress bytes; courses + users intact.)
- **email-validator missing**: pydantic email field was added to a model; remote venv didn't have the dep; uvicorn refused to start. Belt-and-braces install above.
- **default.conf vs skills-lab.conf duplicate `default_server`**: don't write a NEW conf file; OVERWRITE the existing one (`/etc/nginx/conf.d/skills-lab.conf` on .208).

### Phase 2 — SQLite → Postgres migration (one-shot, on top of Phase 1)

```bash
# 1. Generate a strong PG password — SAVE THIS, it goes in DATABASE_URL
PGPASS=$(openssl rand -hex 16)
echo "PG password: $PGPASS"
# Persist locally too in case the SSH session closes mid-script
echo "$PGPASS" > /tmp/pg_password.txt

# 2. Install + start PG (Amazon Linux 2023)
ssh -i $KEY $USER@$HOST "
  set -e
  sudo dnf install -y postgresql15-server postgresql15 postgresql15-contrib
  sudo /usr/bin/postgresql-setup --initdb
  sudo systemctl enable --now postgresql
  sudo systemctl status postgresql --no-pager | head -3
"

# 3. Fix pg_hba.conf — default uses 'ident' which fails for non-postgres
#    user. Switch localhost auth to scram-sha-256 (md5 also OK).
ssh -i $KEY $USER@$HOST "
  sudo sed -i 's|^host\\(.*\\)127.0.0.1/32\\(.*\\)ident|host\\1127.0.0.1/32\\2scram-sha-256|' /var/lib/pgsql/data/pg_hba.conf
  sudo sed -i 's|^host\\(.*\\)::1/128\\(.*\\)ident|host\\1::1/128\\2scram-sha-256|' /var/lib/pgsql/data/pg_hba.conf
  sudo systemctl reload postgresql
"

# 4. Create user + db
ssh -i $KEY $USER@$HOST "
  sudo -u postgres psql -c \"CREATE USER skillslab WITH PASSWORD '$PGPASS';\"
  sudo -u postgres psql -c 'CREATE DATABASE skills_lab OWNER skillslab;'
  sudo -u postgres psql -c 'GRANT ALL ON DATABASE skills_lab TO skillslab;'
  PGPASSWORD='$PGPASS' psql -h localhost -U skillslab -d skills_lab -c 'SELECT current_user;'
"

# 5. Install asyncpg in remote venv
ssh -i $KEY $USER@$HOST "
  /home/ec2-user/skills-lab-v2/.venv/bin/pip install -q asyncpg==0.30.0
"

# 6. Append DATABASE_URL to .env (commented for now; flip post-migration)
ssh -i $KEY $USER@$HOST "
  grep -q DATABASE_URL /home/ec2-user/skills-lab-v2/.env \
    || echo \"#DATABASE_URL=postgresql+asyncpg://skillslab:$PGPASS@localhost:5432/skills_lab\" >> /home/ec2-user/skills-lab-v2/.env
"

# 7. Run the migration script (checked in at tools/migrate_sqlite_to_pg.py).
#    Reads SRC_URL (default = remote SQLite path) and DST_URL.
#    Migrates in FK-safe order: User → Session → Course → Module → Step
#    → Enrollment → UserProgress → Certificate → ReviewSchedule →
#    CourseReview. NULLs out FK refs to users that don't exist in source
#    (artifact of past INSERT-OR-REPLACE migrations that SQLite didn't
#    enforce; PG does). Advances PG sequences after migration.
DST_URL="postgresql+asyncpg://skillslab:$PGPASS@localhost:5432/skills_lab"
ssh -i $KEY $USER@$HOST \
  "cd /home/ec2-user/skills-lab-v2 && DST_URL='$DST_URL' .venv/bin/python tools/migrate_sqlite_to_pg.py"
# Confirm "Verification: row counts SQLite → PG" shows ✓ on every table.

# 8. Cutover
ssh -i $KEY $USER@$HOST "
  cp /home/ec2-user/skills-lab-v2/.env /home/ec2-user/skills-lab-v2/.env.bak.\$(date +%s)
  cp /home/ec2-user/skills-lab-v2/skills_lab.db /home/ec2-user/skills-lab-v2/skills_lab.db.pre-pg-bak
  sed -i 's|^#DATABASE_URL=|DATABASE_URL=|' /home/ec2-user/skills-lab-v2/.env
  sudo systemctl restart skills-lab.service
  sleep 5
  sudo systemctl status skills-lab.service --no-pager | head -5
"

# 9. Verify writes hit PG
curl -s -X POST http://$HOST/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"pg-smoke@example.com","password":"pg-smoke-2026","name":"PG Smoke"}'
ssh -i $KEY $USER@$HOST \
  "PGPASSWORD='$PGPASS' psql -h localhost -U skillslab -d skills_lab -c 'SELECT id, email FROM users ORDER BY id;'"
# pg-smoke@example.com should appear in the PG output
```

**Phase 2 gotchas seen on 52.88.255.208**:
- **PRAGMA-only `_ensure_column`**: pre-2026-04-27 the schema-add code was hardcoded to SQLite (`PRAGMA table_info(courses)`). Service crashed on first PG boot with `syntax error at or near "PRAGMA"`. Fix shipped in commit ad35e94 — uses `sqlalchemy.inspect` which works on both engines. CHECK before deploying to a new box that this fix is present.
- **FK violations on `creator_user_id`**: courses migrated from a different host had `creator_user_id=4` referencing a user that didn't exist on the remote. SQLite tolerated; PG rejected. Migration script NULLs out dangling FK refs before INSERT (3 courses on .208).
- **`could not change directory to "/home/ec2-user"`**: harmless warning when running `sudo -u postgres psql` from a non-postgres-readable cwd. Ignore.

### Rollback (if Phase 2 cutover fails)

```bash
ssh -i $KEY $USER@$HOST "
  mv /home/ec2-user/skills-lab-v2/skills_lab.db.pre-pg-bak /home/ec2-user/skills-lab-v2/skills_lab.db
  sed -i 's|^DATABASE_URL=|#DATABASE_URL=|' /home/ec2-user/skills-lab-v2/.env
  sudo systemctl restart skills-lab.service
"
# Service is back on SQLite; no data loss (we never deleted the .db).
```

PG remains installed but unused; can drop the database (`sudo -u postgres psql -c 'DROP DATABASE skills_lab;'`) if you want to retry from scratch.

### Hostname facts (do not lose)

| IP / hostname | Internal hostname | DB engine | Notes |
|---|---|---|---|
| `52.88.255.208` | `ip-172-31-39-221.us-west-2` | **PG15** (post 2026-04-27) | UPDATE deploy; 26 archived courses preserved + 3 published (kimi/aie/jspring) |
| `skills.sclr.ac` | `ip-172-31-13-27.us-west-2` | SQLite | Shared with external team. Replay Phase 1 + Phase 2 when greenlit. |
| `18.236.242.248` | (same as skills.sclr.ac) | SQLite | Same machine as skills.sclr.ac despite different DNS |

Same SSH key (`~/Downloads/ai-agent-demo.pem`) opens all 3.

### What lives where (don't grep blindly)

- **Migration script**: `tools/migrate_sqlite_to_pg.py` (committed)
- **Deploy playbook (brief)**: top H2 of `CLAUDE.md`
- **Deploy playbook (verbose, with gotchas)**: this file
- **Schema models**: `backend/database.py` (10 models, FK-safe migration order matches the file's class order)
- **Engine-agnostic schema migrations**: `_ensure_column` in `backend/database.py` (post-2026-04-27)
- **Nginx config canonical**: above (under Phase 1 step 5)

