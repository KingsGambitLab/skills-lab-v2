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
function extractAndStripScripts(html: string): { html: string; scripts: string[] } {
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
 * Walk every `onclick="…"` attribute. If it parses as a single function
 * call (`fn(arg1, arg2)`), rewrite to `data-action="fn"` +
 * `data-args-raw="arg1, arg2"`. Multi-statement onclicks are left untouched
 * (they're rare and risky to auto-rewrite; if the page emits them, the
 * delegator will log a missing-function and the human moves on).
 *
 * NB: This is a regex-driven port of the frontend's same-named function.
 * Same regexes, same parsing rules. Tested via `tests/widgets.test.ts`.
 */
function rewriteOnclicks(html: string): string {
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
      const args = m[2];
      return `${before} data-action="${escapeAttr(fn)}" data-args-raw="${escapeAttr(
        args,
      )}"${after}`;
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
function stripOuterIife(code: string): string {
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
function buildRuntimeScript(scripts: string[]): string {
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
      const argsRaw = el.getAttribute('data-args-raw') || '';
      let args = [];
      try { args = Function('"use strict"; return [' + argsRaw + '];')(); }
      catch (err) { console.error('[skillslab widget action] failed to parse args for "' + name + '":', err); return; }
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
