# Pre-built image for Skills Lab v2 TypeScript / JavaScript code_exercise grading.
# Mirrors sll-python-runner for Node: jest + common libs preinstalled so per-run
# time drops from ~60s (fresh npm install) to ~1-2s (test execution only).
#
# Build: docker build -t sll-node-runner:latest -f backend/docker_images/sll-node-runner.Dockerfile backend/docker_images/

FROM node:20-slim

ENV NODE_ENV=test \
    CI=true

WORKDIR /runner

# Install the libraries our course content reaches for most.
# Pinned versions chosen 2026-04-22; bump on image rebuild as ecosystem evolves.
RUN npm init -y >/dev/null \
 && npm install --no-audit --no-fund \
    jest@29.7.0 \
    ts-jest@29.2.5 \
    typescript@5.7.2 \
    @types/node@22.10.2 \
    @types/jest@29.5.14 \
    zod@3.24.1 \
    express@4.21.2 \
    @types/express@5.0.0 \
    supertest@7.0.0 \
    @types/supertest@6.0.2 \
    axios@1.7.9 \
    node-fetch@3.3.2 \
    bcrypt@5.1.1 \
    jsonwebtoken@9.0.2 \
    @types/jsonwebtoken@9.0.7 \
    pg@8.13.1 \
    @types/pg@8.11.10 \
    redis@4.7.0 \
    rxjs@7.8.1 \
 && npx jest --version \
 && node -e "require('zod'); require('express'); require('bcrypt'); require('jsonwebtoken'); console.log('preload ok')"

# Preinstall ts-node config + a minimal jest config so TS tests work out-of-box.
RUN cat > /runner/jest.config.js <<'EOF'
// v8.5 Phase B HARNESS-CLOSURE INVARIANT (2026-04-23):
// ts-jest explicitly told to use /runner/tsconfig.json which points typeRoots
// at BOTH /app/node_modules/@types (LLM's types) and /runner/node_modules/@types
// (harness types incl. jest). LLM cannot override this — we pass --config=/runner/jest.config.js
// explicitly in _cmd_for_lang, and LLM's /app/jest.config.js is ignored.
//
// testMatch covers BOTH naming conventions:
//   - jest default: `*.test.ts` (solution.test.ts, foo.test.ts)
//   - pytest-style:  `test_*.ts`  (test_solution.ts) — our runner writes this
// Either is OK; tests collect correctly regardless of filename style.
module.exports = {
  testEnvironment: 'node',
  preset: 'ts-jest',
  testMatch: [
    '<rootDir>/tests/**/*.test.{ts,js}',
    '<rootDir>/tests/**/test_*.{ts,js}',
    '<rootDir>/*.test.{ts,js}',
    '<rootDir>/test_*.{ts,js}',
  ],
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      tsconfig: '/runner/tsconfig.json',
    }],
  },
  // Ensure jest's module resolver finds /app first (LLM's deps) then /runner.
  moduleDirectories: ['node_modules', '/app/node_modules', '/runner/node_modules'],
};
EOF

RUN cat > /runner/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "esModuleInterop": true,
    "strict": false,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "typeRoots": ["/app/node_modules/@types", "/runner/node_modules/@types"],
    "types": ["jest", "node"]
  }
}
EOF

# v8.5 Phase B HARNESS-CLOSURE INVARIANT (2026-04-23):
# Snapshot baked harness /runner/node_modules versions so verify_baked_js.mjs
# can assert immutability at grade time. Read back via JSON; any mutation
# of jest / ts-jest / @types/jest etc. fires DEP_DRIFT.
RUN node -e "                                                               \
  const fs = require('fs');                                                  \
  const pkg = JSON.parse(fs.readFileSync('/runner/package.json'));           \
  const tracked = ['jest','ts-jest','typescript','@types/jest','@types/node',\
                   'zod','express','supertest','bcrypt','jsonwebtoken','pg','redis','rxjs','axios','node-fetch']; \
  const snap = {};                                                           \
  for (const name of tracked) {                                              \
    try { snap[name] = JSON.parse(fs.readFileSync('/runner/node_modules/' + name + '/package.json')).version; } \
    catch (e) { snap[name] = null; }                                         \
  }                                                                          \
  fs.writeFileSync('/opt/harness-venv-snapshot-js.json', JSON.stringify(snap, null, 2)); \
  console.log('harness-js snapshot:', Object.keys(snap).length, 'packages');                \
"
COPY verify_baked_js.mjs /opt/verify_baked.mjs
RUN chmod +x /opt/verify_baked.mjs && node /opt/verify_baked.mjs && echo "verify_baked-js: OK"

WORKDIR /app
