#!/usr/bin/env node
// v8.5 Phase B — enforce HARNESS-CLOSURE INVARIANT for the Node runner.
//
// Two checks (same pattern as verify_baked_python.py):
//   1. /runner/node_modules contains jest + ts-jest + @types/jest at the
//      baked versions recorded in /opt/harness-venv-snapshot-js.json.
//   2. /app/node_modules does NOT have jest / ts-jest / @types/jest installed
//      (shadow-framework check — LLM-emitted package.json must not re-pin
//      the test framework).
//
// Exit codes:
//   0   — invariant holds → proceed to tests
//   127 — invariant violated → surface as DEP_DRIFT: for retry feedback

import { existsSync, readFileSync } from "node:fs";

const HARNESS_NODE_MODULES = "/runner/node_modules";
const LLM_NODE_MODULES = "/app/node_modules";
const SNAPSHOT_PATH = "/opt/harness-venv-snapshot-js.json";

// Shadow-forbidden: must NOT appear in /app/node_modules.
const SHADOW_FORBIDDEN_LLM = new Set([
  "jest", "ts-jest", "@types/jest", "jest-environment-node",
  "jest-jasmine2", "@jest/core", "@jest/reporters",
]);

function readPackageVersion(nodeModulesDir, pkgName) {
  const pkgPath = `${nodeModulesDir}/${pkgName}/package.json`;
  if (!existsSync(pkgPath)) return null;
  try {
    const pkg = JSON.parse(readFileSync(pkgPath, "utf-8"));
    return pkg.version || null;
  } catch {
    return null;
  }
}

function main() {
  const drifts = [];

  // CHECK 1 — harness /runner/node_modules is immutable
  if (existsSync(SNAPSHOT_PATH)) {
    const snapshot = JSON.parse(readFileSync(SNAPSHOT_PATH, "utf-8"));
    for (const [pkg, bakedVer] of Object.entries(snapshot)) {
      const got = readPackageVersion(HARNESS_NODE_MODULES, pkg);
      if (got !== bakedVer) {
        drifts.push(
          `DEP_DRIFT: harness-node-modules ${pkg} baked=${bakedVer} post-install=${got || "MISSING"}`
        );
      }
    }
  }

  // CHECK 2 — no shadow test framework in /app/node_modules
  for (const pkg of SHADOW_FORBIDDEN_LLM) {
    const got = readPackageVersion(LLM_NODE_MODULES, pkg);
    if (got !== null) {
      drifts.push(
        `DEP_DRIFT: shadow ${pkg}==${got} found in /app/node_modules ` +
        `(conflicts with /runner/node_modules/.bin/jest). ` +
        `LLM's package.json must NOT pin ${pkg}.`
      );
    }
  }

  if (drifts.length === 0) {
    process.exit(0);
  }

  for (const d of drifts) console.error(d);
  console.error(
    "\nHARNESS-CLOSURE INVARIANT VIOLATED. Drop any pin for jest / ts-jest / " +
    "@types/jest / jest-environment-node from your package.json — the image " +
    "ships them in /runner/node_modules and your tests invoke them via " +
    "/runner/node_modules/.bin/jest."
  );
  process.exit(127);
}

main();
