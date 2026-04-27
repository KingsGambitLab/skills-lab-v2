/**
 * CSP-safe widget rewrite for the WebView.
 *
 * Per buddy-Opus 2026-04-27 (the load-bearing risk): VS Code WebViews ship
 * a strict default CSP that blocks inline `<script>` and inline event
 * handlers. Server-rendered HTML with `onclick="generateComparison()"`
 * will render but be inert. Mirrors what `frontend/index.html`'s
 * `_rewriteOnclicksToDataActions` already does for the browser SPA — same
 * pattern, ported to TypeScript so the WebView gets the same treatment.
 *
 * Pipeline:
 *   1. Strip <script> inline tags (security + CSP) and capture their
 *      bodies — we'll re-inject as a single nonce'd script bundle.
 *   2. Walk every `[onclick]` attribute; convert to `data-action` +
 *      `data-args-raw`; remove the original onclick.
 *   3. Generate a nonce; produce a CSP meta tag that ONLY allows scripts
 *      with that nonce.
 *   4. Inject a single nonce'd <script> that:
 *      - Defines all hoisted functions on `window` (from captured script
 *        bodies, with outer-IIFE unwrap matching frontend/index.html v7).
 *      - Installs the data-action delegator (single click handler).
 *
 * Result: server's freely-emitted "<button onclick="fn()">" widgets work
 * inside the WebView with zero CSP relaxations. Same security posture
 * as the browser; no `unsafe-inline`.
 */

const _NONCE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

export function generateNonce(len = 32): string {
  let s = "";
  for (let i = 0; i < len; i++) {
    s += _NONCE_CHARS.charAt(Math.floor(Math.random() * _NONCE_CHARS.length));
  }
  return s;
}

/**
 * Extract <script>...</script> bodies + return HTML with all script tags
 * removed. We'll re-inject the bodies inside a single nonce'd wrapper.
 */
export function extractAndStripScripts(html: string): { html: string; scripts: string[] } {
  const scripts: string[] = [];
  const stripped = html.replace(
    /<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi,
    (_match, body: string) => {
      // Only capture INLINE scripts (no `src=` attribute on the tag).
      // External scripts are referenced via webview.asWebviewUri elsewhere.
      if (/<script\b[^>]*\bsrc=/i.test(_match)) return ""; // strip externals too
      scripts.push(body);
      return "";
    },
  );
  return { html: stripped, scripts };
}

/**
 * Convert a raw JS-literal argument list (`'a', 1, ['b', 2]`) into a JSON
 * array string (`["a",1,["b",2]]`) by best-effort regex coercion:
 *   - single-quoted strings → double-quoted
 *   - unquoted object keys → "quoted"
 *
 * Returns null if the result still doesn't `JSON.parse` (common for
 * function-call-as-arg, regex literals, template strings, etc.). Caller
 * should leave the onclick untouched in that case so the delegator's
 * missing-function path catches the click and logs a clear error.
 *
 * Why JSON, not eval? CSP `script-src 'nonce-X'` (without `'unsafe-eval'`)
 * blocks `new Function(...)` and `eval(...)` in the WebView. Pre-2026-04-27
 * (v0.1.1) the runtime delegator used `Function('return [' + raw + ']')()`
 * — fired EvalError on every widget click. The right fix is to do the
 * parse at SERVER SIDE (here, in Node, no CSP) and emit canonical JSON
 * for the runtime to JSON.parse — never eval.
 */
export function convertArgsToJson(argsRaw: string): string | null {
  const trimmed = argsRaw.trim();
  if (trimmed === "") return "[]";
  let json = "[" + trimmed + "]";
  // single-quoted strings → double-quoted (preserve escapes)
  json = json.replace(/'([^'\\]*(?:\\.[^'\\]*)*)'/g, (_m, inner: string) => {
    return '"' + inner.replace(/\\'/g, "'").replace(/"/g, '\\"') + '"';
  });
  // unquoted object keys: { foo: 1 } → { "foo": 1 }
  json = json.replace(
    /([{,]\s*)([a-zA-Z_$][\w$]*)\s*:/g,
    (_m, lead: string, key: string) => `${lead}"${key}":`,
  );
  try {
    JSON.parse(json);
    return json;
  } catch {
    return null;
  }
}

/**
 * Walk every `onclick="…"` attribute. If it parses as a single function
 * call (`fn(arg1, arg2)`), rewrite to `data-action="fn"` +
 * `data-args-json='[arg1, arg2]'` (canonical JSON). Multi-statement
 * onclicks and arg shapes that don't coerce to JSON are left untouched.
 *
 * NB: This is a regex-driven port of the frontend's same-named function.
 * The 2026-04-27 v0.1.2 evolution: emit canonical JSON instead of raw JS
 * source so the WebView delegator can `JSON.parse` (CSP-safe) instead of
 * `Function(...)` (CSP unsafe-eval, blocked).
 */
export function rewriteOnclicks(html: string): string {
  const callRe = /^\s*([a-zA-Z_$][\w$]*)\s*\(([\s\S]*)\)\s*;?\s*$/;
  return html.replace(
    /(<\w+\b[^>]*?)\sonclick\s*=\s*(["'])([\s\S]*?)\2([^>]*>)/gi,
    (_match, before: string, _q: string, body: string, after: string) => {
      const m = body.match(callRe);
      if (!m) {
        // Multi-statement / non-function-call onclick — leave it.
        return `${before} onclick="${escapeAttr(body)}"${after}`;
      }
      const fn = m[1];
      const argsJson = convertArgsToJson(m[2]);
      if (argsJson === null) {
        // Args don't coerce to JSON (e.g. function-call-as-arg, template
        // literal, regex). Leave onclick untouched — better than emitting
        // a broken data-action that fails to parse at runtime.
        return `${before} onclick="${escapeAttr(body)}"${after}`;
      }
      return `${before} data-action="${escapeAttr(
        fn,
      )}" data-args-json="${escapeAttr(argsJson)}"${after}`;
    },
  );
}

function escapeAttr(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Strip an outer IIFE wrapper from a script body. Mirrors the
 * 2026-04-27 v7 fix in frontend/index.html: handles both Crockford
 * `})()` and alt `}())` shapes; leading-semicolon variants too.
 *
 * Without this, a script wrapped in `(function() { function fn(){} })()`
 * defines `fn` at IIFE-scope; the hoist tail's `typeof fn` check at the
 * outer scope can't see it → `window.fn` stays undefined → click silent.
 */
export function stripOuterIife(code: string): string {
  const re = /^[;\s]*\(\s*function\s*\(\s*\)\s*\{([\s\S]*)\}\s*(?:\)\s*\(\s*\)|\(\s*\)\s*\))\s*;?\s*$/;
  const m = code.trim().match(re);
  return m ? m[1] : code;
}

/**
 * Build the runtime <script> body (executed inside the nonce'd tag) that:
 *   1. Re-runs the stripped scripts (with outer-IIFE unwrap).
 *   2. Hoists named function decls to `window`.
 *   3. Installs the data-action delegator.
 */
export function buildRuntimeScript(scripts: string[]): string {
  const hoistShapes = [
    /(?:^|\n)\s*function\s+([a-zA-Z_$][\w$]*)\s*\(/g,
    /(?:^|\n)\s*(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|[a-zA-Z_$][\w$]*\s*=>)/g,
  ];
  const reserved = new Set([
    "if","else","for","while","do","switch","case","return","function","var","let","const",
    "class","new","this","async","await","try","catch","finally","throw","break","continue",
    "true","false","null","undefined","NaN","Infinity",
  ]);

  const wrappers: string[] = [];
  for (const raw of scripts) {
    const code = stripOuterIife(raw);
    const names = new Set<string>();
    for (const re of hoistShapes) {
      let m: RegExpExecArray | null;
      const r = new RegExp(re.source, re.flags);
      while ((m = r.exec(code)) !== null) names.add(m[1]);
    }
    const toHoist = [...names].filter((n) => !reserved.has(n));
    const tail = toHoist
      .map((n) => `try{if(typeof ${n}!=="undefined")window[${JSON.stringify(n)}]=${n};}catch(_e){}`)
      .join("");
    wrappers.push(`(function(){
      try { ${code}\n${tail} } catch (e) { console.error('[skillslab widget script]', e); }
    })();`);
  }

  // Delegator: dispatches data-action clicks. JSON.parse ONLY — never
  // eval / Function. Two reasons:
  //   1. CSP: 'unsafe-eval' is not (and must not be) in the WebView's
  //      script-src. Pre-2026-04-27 (v0.1.1) the delegator ran
  //      `Function('return ['+argsRaw+'];')()` which fired EvalError on
  //      every click in the WebView.
  //   2. Defense-in-depth: even in browser contexts where eval is
  //      permitted, evaluating arbitrary attribute strings as JS is an
  //      XSS amplifier. JSON.parse only handles structured data; narrow
  //      attack surface; deterministic.
  //
  // Args MUST arrive as canonical JSON in `data-args-json`. The
  // server-side rewriter (rewriteOnclicks above) does the JS-literal →
  // JSON conversion exactly once, in Node, where there's no CSP. If a
  // widget's onclick can't be coerced to JSON, the rewriter leaves the
  // onclick raw and this delegator never sees it.
  const delegator = `
    document.addEventListener('click', function(e) {
      const el = e.target.closest && e.target.closest('[data-action]');
      if (!el) return;
      const name = el.getAttribute('data-action');
      const fn = window[name];
      if (typeof fn !== 'function') {
        console.error('[skillslab widget action] "' + name + '" is not on window. Check the widget script defines it via window.' + name + ' = ... or function ' + name + '() {} at top scope.');
        return;
      }
      const argsJson = el.getAttribute('data-args-json') || '[]';
      let args = [];
      try { args = JSON.parse(argsJson); }
      catch (err) {
        console.error('[skillslab widget action] data-args-json malformed for "' + name + '":', err, '— raw:', argsJson);
        return;
      }
      if (!Array.isArray(args)) args = [args];
      try { fn.apply(null, args); }
      catch (err) { console.error('[skillslab widget action] "' + name + '" threw:', err); }
    }, true);
  `;
  return wrappers.join("\n") + "\n" + delegator;
}

/**
 * The single public entry: take server-rendered HTML, return CSP-safe
 * HTML ready to embed in a VS Code WebView.
 *
 * Returns:
 *   { html: <body html>, scriptBundle: <runtime js>, nonce: <nonce> }
 *
 * The caller wraps with a full document including:
 *   <meta http-equiv="Content-Security-Policy"
 *         content="default-src 'none'; style-src 'unsafe-inline';
 *                  script-src 'nonce-NONCE'; img-src https: data:;">
 *   <script nonce="NONCE">SCRIPT_BUNDLE</script>
 *
 * (The WebView's webview.cspSource must also be referenced for any
 * resources we might load via webview.asWebviewUri — kept minimal in v1.)
 */
export function rewriteForWebview(html: string): { html: string; scriptBundle: string; nonce: string } {
  const { html: stripped, scripts } = extractAndStripScripts(html);
  const rewritten = rewriteOnclicks(stripped);
  const scriptBundle = buildRuntimeScript(scripts);
  return { html: rewritten, scriptBundle, nonce: generateNonce() };
}
