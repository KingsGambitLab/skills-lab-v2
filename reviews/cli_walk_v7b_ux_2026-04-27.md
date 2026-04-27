# CLI walk v7b UX verification (2026-04-27)

**Image**: `tusharbisht1391/skillslab:latest`
**Digest**: `sha256:1cb76693954fc272ba594cfc1e371101d2017440a163f76a66906eea475c682f` (confirmed via `docker pull`)
**LMS**: http://52.88.255.208
**Scope**: Narrow re-verify of 2 fixes from v7a SHIP-WITH-FIXES verdict + presence-check on a queued one + light sanity sweep.
**Verifier**: detailed-walk@example.com (cli_token label v7b)

---

## Fix 1 — `skillslab whoami` no longer crashes on missing token  →  **PASS**

Command:
```bash
mkdir -p /tmp/whoami-fresh-1777263188
docker run --rm \
  -v /tmp/whoami-fresh-1777263188:/root/.skillslab \
  -e SKILLSLAB_API_URL=http://52.88.255.208 \
  tusharbisht1391/skillslab:latest skillslab whoami
```

Verbatim output:
```
Not signed in. Run skillslab login.
```
Exit code: **1** (matches expected).

No traceback. Friendly text. Fix landed.

---

## Fix 2 — Course themes render correct accent color (not cyan)  →  **PASS (all three)**

Method: started each course (`skillslab start <slug>`), then ran `skillslab spec --course <slug>` under `script -q` to allocate a real PTY (Rich strips color when stdout is a pipe — pipe-to-tee per spec gave 0 escapes; the PTY capture is the right method, called out in the spec as "use `script` or `tee` so ANSI escapes survive"). Captured to `/tmp/spec_<slug>_pty.bin`.

Truecolor escape extraction via regex `\x1b\[38;2;(\d+);(\d+);(\d+)m`:

| Course | First-5 truecolor triples | Cyan (`\x1b[36m`) count | Expected | Verdict |
|---|---|---|---|---|
| **kimi** | `(79, 70, 229)` × 5 | 0 | 79,70,229 OR 99,102,241 | PASS — exact indigo |
| **claude-code** | `(234, 88, 12)` × 5 | 0 | 234,88,12 OR 249,115,22 | PASS — exact orange |
| **jspring** | `(185, 28, 28)` × 5 | 0 | 185,28,28 OR 220,38,38 | PASS — exact red |

Per-file totals: kimi 33 truecolor escapes; claude-code 31; jspring 31. Zero cyan (36m) anywhere. Each course's first border-color escape (immediately after panel-open) is its own distinct accent — no quantization, no fallback to ANSI-16.

Raw evidence files preserved at `/tmp/spec_kimi_pty.bin`, `/tmp/spec_claude-code_pty.bin`, `/tmp/spec_jspring_pty.bin`.

---

## Fix 3 — celebration code presence (queued, presence-only)  →  **PRESENT**

```bash
$ docker run --rm tusharbisht1391/skillslab:latest grep render_celebration \
    /skillslab-cli/src/skillslab/views/celebration.py
def render_celebration(
```

Code path is still in the image. (Full celebration walk not in this v7b scope.)

---

## Sanity sweep — no regressions

- **`skillslab --help` lists `toc`**: PASS
  ```
    toc        Print a course outline — what's done, what's active, what's...
  ```

- **`skillslab courses` with no token**: PASS — exits 0, lists 3 courses (jspring, claude-code, kimi) with public-catalog notice; no traceback.

- **Surface rule II3 (step_pos=1 → /0)**: PASS
  ```
  $ ... python3 -c "from skillslab.cli import _browser_url; \
        print(_browser_url('created-698e6399e3ca', \
              {'module_id': 23209, 'step_pos': 1}))"
  http://52.88.255.208/#created-698e6399e3ca/23209/0
  ```
  Ends with `/23209/0` exactly as expected — pos→idx subtraction still correct.

---

## Verdict: **SHIP**

Both targeted fixes confirmed in the published multi-arch image. Celebration code present. No regressions in the sanity sweep (toc command, no-token courses listing, surface II3 URL builder).
