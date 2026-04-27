/**
 * Execution-based tests for vscode/src/widgets.ts — the load-bearing
 * CSP-safe rewriter that turns server HTML into WebView-safe HTML.
 *
 * Per user directive 2026-04-27: "shim should ideally not rely on grep
 * as it can be brittle, rely on higher level functions like click and
 * execute." These tests RUN the actual code paths and assert on real
 * outputs — comment text, refactor-renamed variables, etc. all behave
 * correctly because we measure behavior, not source.
 *
 * Runner: Node 18+ built-in `node:test` (zero new devDeps). Run via
 * `npm test` from `vscode/` (uses tsconfig.test.json to include this
 * file in the compile).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  convertArgsToJson,
  rewriteOnclicks,
  extractAndStripScripts,
  stripOuterIife,
  buildRuntimeScript,
  rewriteForWebview,
} from "../src/widgets";

// ──────────────────────────────────────────────────────────────────
// convertArgsToJson — JS-literal args → canonical JSON (no eval ever)
// ──────────────────────────────────────────────────────────────────

test("convertArgsToJson: empty input returns []", () => {
  assert.equal(convertArgsToJson(""), "[]");
  assert.equal(convertArgsToJson("   "), "[]");
});

test("convertArgsToJson: single-quoted string → double-quoted JSON", () => {
  // The exact bug from the user's screenshot 2026-04-27:
  //   selectScenario('ship_feature') → data-args-json='["ship_feature"]'
  const out = convertArgsToJson("'ship_feature'");
  assert.equal(out, '["ship_feature"]');
  // And it MUST round-trip through JSON.parse:
  assert.deepEqual(JSON.parse(out!), ["ship_feature"]);
});

test("convertArgsToJson: number args", () => {
  assert.equal(convertArgsToJson("1, 2, 3"), "[1, 2, 3]");
  assert.deepEqual(JSON.parse(convertArgsToJson("1, 2, 3")!), [1, 2, 3]);
});

test("convertArgsToJson: nested array of strings", () => {
  const out = convertArgsToJson("['a', 'b', 'c']");
  assert.deepEqual(JSON.parse(out!), [["a", "b", "c"]]);
});

test("convertArgsToJson: object with unquoted keys → quoted JSON", () => {
  const out = convertArgsToJson("{ foo: 1, bar: 'two' }");
  assert.notEqual(out, null, "object args with unquoted keys must coerce");
  assert.deepEqual(JSON.parse(out!), [{ foo: 1, bar: "two" }]);
});

test("convertArgsToJson: mixed args", () => {
  const out = convertArgsToJson("'first', 42, ['x', 'y']");
  assert.deepEqual(JSON.parse(out!), ["first", 42, ["x", "y"]]);
});

test("convertArgsToJson: returns null for shapes JSON can't represent", () => {
  // function-call-as-arg → caller leaves onclick raw
  assert.equal(convertArgsToJson("getCurrentUser()"), null);
  // template literal → can't coerce
  assert.equal(convertArgsToJson("`hello ${name}`"), null);
});

// ──────────────────────────────────────────────────────────────────
// rewriteOnclicks — server-side onclick → data-action + data-args-json
// ──────────────────────────────────────────────────────────────────

test("rewriteOnclicks: emits data-args-json (NOT data-args-raw)", () => {
  const out = rewriteOnclicks(`<button onclick="selectScenario('ship_feature')">x</button>`);
  // The v0.1.1 shape (eval-blocked) MUST be gone:
  assert.equal(
    out.includes("data-args-raw"),
    false,
    "data-args-raw is the pre-v0.1.2 eval-blocked shape; must not appear",
  );
  // The v0.1.2 shape MUST be present:
  assert.match(out, /data-action="selectScenario"/);
  assert.match(out, /data-args-json="\[&quot;ship_feature&quot;\]"/);
  // onclick MUST be stripped:
  assert.equal(out.includes("onclick="), false, "original onclick must be removed");
});

test("rewriteOnclicks: no-arg call emits data-args-json='[]'", () => {
  const out = rewriteOnclicks(`<button onclick="resetForm()">x</button>`);
  assert.match(out, /data-action="resetForm"/);
  assert.match(out, /data-args-json="\[\]"/);
});

test("rewriteOnclicks: leaves onclick alone when args don't coerce", () => {
  const out = rewriteOnclicks(
    `<button onclick="fn(getCurrentUser())">x</button>`,
  );
  // Leave the original (CSP-blocked, but at least doesn't lie about being
  // a working data-action). The delegator never sees this button.
  assert.equal(out.includes("data-action"), false);
  assert.match(out, /onclick=/);
});

test("rewriteOnclicks: multi-statement onclicks left untouched", () => {
  const out = rewriteOnclicks(`<button onclick="a();b();c()">x</button>`);
  assert.equal(out.includes("data-action"), false);
});

// ──────────────────────────────────────────────────────────────────
// stripOuterIife — handles Crockford / alt / leading-semicolon shapes
// ──────────────────────────────────────────────────────────────────

test("stripOuterIife: Crockford `})()` shape", () => {
  const wrapped = `(function(){ function fn(){return 1;} })();`;
  const out = stripOuterIife(wrapped);
  assert.ok(!out.startsWith("(function"));
  assert.ok(out.includes("function fn()"));
});

test("stripOuterIife: alt `}())` shape", () => {
  const wrapped = `(function(){ function fn(){return 1;} }());`;
  const out = stripOuterIife(wrapped);
  assert.ok(!out.startsWith("(function"));
});

test("stripOuterIife: leading-semicolon variant", () => {
  const wrapped = `;(function(){ function fn(){return 1;} })();`;
  const out = stripOuterIife(wrapped);
  assert.ok(!out.startsWith(";("));
});

test("stripOuterIife: leaves IIFE with args alone", () => {
  // `(function(x){...})("y")` is a parameterized IIFE — unwrapping
  // would lose the 'y' binding. Leave it.
  const wrapped = `(function(x){ return x; })("y");`;
  const out = stripOuterIife(wrapped);
  assert.equal(out, wrapped);
});

// ──────────────────────────────────────────────────────────────────
// buildRuntimeScript — the delegator MUST NOT contain Function/eval
// ──────────────────────────────────────────────────────────────────

test("buildRuntimeScript: zero Function( or eval( in delegator output", () => {
  // This is the test that would have caught Fix G in v0.1.1: we measure
  // the actual runtime string that gets embedded in <script nonce="..."
  // — not the source — so refactor-renames + comment edits don't
  // affect the assertion. The OUTPUT is what runs in the WebView under
  // CSP `script-src 'nonce-X'` (no unsafe-eval).
  const bundle = buildRuntimeScript([
    `function selectScenario(id){ console.log(id); }`,
  ]);
  assert.equal(
    /\bFunction\s*\(/.test(bundle),
    false,
    "delegator must not contain Function( — CSP unsafe-eval blocks it",
  );
  assert.equal(
    /\beval\s*\(/.test(bundle),
    false,
    "delegator must not contain eval( — CSP unsafe-eval blocks it",
  );
});

test("buildRuntimeScript: delegator parses args via JSON.parse", () => {
  const bundle = buildRuntimeScript([]);
  assert.match(
    bundle,
    /JSON\.parse\(argsJson\)/,
    "delegator must use JSON.parse on data-args-json (not eval)",
  );
});

test("buildRuntimeScript: hoists top-level function decls to window", () => {
  const bundle = buildRuntimeScript([
    `function selectScenario(id){ console.log(id); }`,
  ]);
  // The hoist tail looks like:
  //   try{if(typeof selectScenario!=="undefined")window["selectScenario"]=selectScenario;}catch(_e){}
  assert.match(
    bundle,
    /window\["selectScenario"\]\s*=\s*selectScenario/,
    "named function decl must be hoisted onto window for delegator dispatch",
  );
});

// ──────────────────────────────────────────────────────────────────
// rewriteForWebview — full pipeline on realistic widget HTML
// ──────────────────────────────────────────────────────────────────

test("rewriteForWebview: realistic widget end-to-end", () => {
  // Mirror of the Aider command explorer widget from Kimi M0.S1 — the
  // exact widget from the user's 2026-04-27 screenshot. Pre-v0.1.2 the
  // click fired EvalError. Post-v0.1.2 it should produce CSP-safe
  // output throughout.
  const input = `
<div class="widget">
  <button class="card" onclick="selectScenario('ship_feature')">Ship a New Feature</button>
  <button class="card" onclick="selectScenario('fix_bug')">Fix Bug</button>
  <script>
    (function(){
      function selectScenario(id) {
        document.querySelector('.shell').textContent = 'aider --scenario=' + id;
      }
    })();
  </script>
</div>`;
  const out = rewriteForWebview(input);

  // Output HTML — no inline scripts, no inline onclicks, only data-action + data-args-json
  assert.equal(out.html.includes("<script"), false, "all <script> tags must be stripped");
  assert.equal(out.html.includes("onclick="), false, "all inline onclicks must be rewritten");
  assert.match(out.html, /data-action="selectScenario"/);
  assert.match(out.html, /data-args-json="\[&quot;ship_feature&quot;\]"/);
  assert.match(out.html, /data-args-json="\[&quot;fix_bug&quot;\]"/);

  // Runtime bundle — no eval/Function, hoists `selectScenario` onto window
  assert.equal(/\bFunction\s*\(/.test(out.scriptBundle), false);
  assert.equal(/\beval\s*\(/.test(out.scriptBundle), false);
  assert.match(out.scriptBundle, /JSON\.parse\(argsJson\)/);
  assert.match(out.scriptBundle, /window\["selectScenario"\]\s*=\s*selectScenario/);

  // Nonce is non-trivial (≥ 16 chars, alnum)
  assert.match(out.nonce, /^[A-Za-z0-9]{16,}$/);
});

test("rewriteForWebview: data-args-json values round-trip through JSON.parse", () => {
  // Strong regression test: if the server-side rewriter emits args that
  // JSON.parse can't handle, the delegator throws at click time.
  // Extract every data-args-json="..." attribute and verify each is
  // valid JSON.
  const input = `
<button onclick="fn1('a')">a</button>
<button onclick="fn2(1, 2)">b</button>
<button onclick="fn3({foo: 'bar', baz: 42})">c</button>
<button onclick="fn4(['x', 'y', 'z'])">d</button>`;
  const out = rewriteForWebview(input);

  // Find all data-args-json attribute values (HTML-decoded)
  const re = /data-args-json="([^"]+)"/g;
  const matches: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(out.html)) !== null) {
    // HTML-decode &quot; back to "
    matches.push(m[1].replace(/&quot;/g, '"').replace(/&amp;/g, "&"));
  }
  assert.equal(matches.length, 4, "all 4 buttons should rewrite to data-args-json");

  for (const json of matches) {
    // This is the assertion that catches Fix G regressions:
    // every emitted args value MUST parse cleanly with JSON.parse,
    // because that's what the runtime delegator does — never eval.
    assert.doesNotThrow(
      () => JSON.parse(json),
      `data-args-json "${json}" must be valid JSON (delegator parses via JSON.parse — eval is CSP-blocked)`,
    );
  }
});
