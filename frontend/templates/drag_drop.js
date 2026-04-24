/**
 * drag_drop template — handles parsons / ordering / categorization / sjt / code_review.
 *
 * Contract: mount(containerEl, data, judgeFn). The template owns the DOM;
 * the caller supplies (a) a rendered shell (via manifest), (b) the data payload,
 * and (c) a judge function that takes the submission and returns a Promise
 * resolving to a validator response.
 *
 * Data shape per exercise_type:
 *   parsons:          { exercise_type: "parsons",         items: [{id, text}] }
 *   ordering:         { exercise_type: "ordering",        items: [{id, text}] }
 *   categorization:   { exercise_type: "categorization",  items: [{id, text}], categories: [string] }
 *   sjt:              { exercise_type: "sjt",             items: [{id, text}] }   // items = options; N slots = N ranks
 *   code_review:      { exercise_type: "code_review",     language, code }
 */
(function (global) {
  'use strict';

  function esc(s) { return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  // 2026-04-22 fix: centralized submit-lock + pending-state helpers.
  // Fixes two bugs the beginner-agent caught:
  //   P1-3 stale feedback — prior attempt's "2 more retries" stayed visible
  //         for 5-15s on top of the new successful submission
  //   P1-7 browser hang — rapid Submit double-clicks sent parallel POSTs,
  //         renderer stalled for 30s, required hard preview reload
  function _beginSubmit(container) {
    const btn = container.querySelector('[data-action="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.dataset._originalText = btn.dataset._originalText || btn.textContent;
      btn.textContent = 'Submitting…';
      btn.style.opacity = '0.6';
      btn.style.cursor = 'wait';
    }
    const f = container.querySelector('[data-role="feedback"]');
    if (f) {
      f.className = 'tmpl-feedback pending';
      f.innerHTML = '<em style="color:var(--text-secondary, #9097aa);">Grading…</em>';
    }
  }
  function _endSubmit(container) {
    const btn = container.querySelector('[data-action="submit"]');
    if (btn) {
      btn.disabled = false;
      btn.textContent = btn.dataset._originalText || 'Submit';
      btn.style.opacity = '';
      btn.style.cursor = '';
    }
  }
  async function _guardedSubmit(container, runFn) {
    const btn = container.querySelector('[data-action="submit"]');
    if (btn && btn.disabled) return;  // already in-flight
    _beginSubmit(container);
    try {
      await runFn();
    } catch (e) {
      const f = container.querySelector('[data-role="feedback"]');
      if (f) {
        f.className = 'tmpl-feedback fail';
        f.innerHTML = '<strong>Error</strong><br>' + esc(e && e.message ? e.message : String(e));
      }
    } finally {
      _endSubmit(container);
    }
  }

  function mount(containerEl, data, handlersOrJudgeFn, options) {
    options = options || {};
    // 2026-04-22 fix: accept either a plain judgeFn (legacy) OR an
    // { judgeFn, executeFn, checkGhaFn } handlers object (current). The
    // renderStep dispatcher passes the handlers object — the previous code
    // mis-read it as a function, so `judgeFn(...)` in the click handlers
    // threw silently and Submit did nothing for parsons/ordering/
    // categorization/sjt/code_review/mcq/fill_in_blank. Bug caught by
    // beginner-agent walkthrough 2026-04-22 on Step 4 (code_review Submit
    // never fired) + Step 5 (categorization Submit never fired).
    const judgeFn = (typeof handlersOrJudgeFn === 'function')
      ? handlersOrJudgeFn
      : (handlersOrJudgeFn && typeof handlersOrJudgeFn.judgeFn === 'function'
         ? handlersOrJudgeFn.judgeFn
         : () => Promise.resolve({ score: 0, feedback: 'No judge function wired.' }));
    const ex = data.exercise_type;
    // 2026-04-22 v6: title slot removed from template HTML (outer .step-title
    // renders it once). Guarded for back-compat.
    const _titleEl = containerEl.querySelector('[data-slot="title"]');
    if (_titleEl) _titleEl.textContent = data.title || '';
    const briefEl = containerEl.querySelector('[data-slot="briefing"]');
    if (briefEl) briefEl.innerHTML = data.briefing || '';

    if (ex === 'code_review') return mountCodeReview(containerEl, data, judgeFn);
    if (ex === 'categorization') return mountCategorization(containerEl, data, judgeFn);
    if (ex === 'sjt') return mountSjt(containerEl, data, judgeFn);
    if (ex === 'mcq') return mountMcq(containerEl, data, judgeFn);
    if (ex === 'fill_in_blank') return mountFillBlank(containerEl, data, judgeFn);
    // parsons / ordering fall through to the generic single-target case
    return mountSequence(containerEl, data, judgeFn);
  }

  // ---------- MCQ: one question, N radio options, pick one ----------
  function mountMcq(container, data, judge) {
    container.querySelector('[data-role="source-bin"]').style.display = 'none';
    const bins = container.querySelector('[data-role="target-bins"]');
    const options = (data.options || data.items || []).map((o, i) => ({
      id: o.id != null ? String(o.id) : String(i),
      text: o.text || o.label || String(o),
    }));
    bins.innerHTML = `<div class="tmpl-mcq-options">
      ${options.map((o, i) => `<label class="tmpl-item" style="display:flex; gap:10px; align-items:center;">
        <input type="radio" name="mcq-${Date.now()}" value="${esc(String(i))}">
        <span>${esc(o.text)}</span>
      </label>`).join('')}
    </div>`;
    container.querySelector('[data-action="submit"]').addEventListener('click', () => _guardedSubmit(container, async () => {
      const picked = container.querySelector('input[type="radio"]:checked');
      const answer = picked ? parseInt(picked.value, 10) : null;
      if (answer === null) {
        renderFeedback(container, { score: 0, feedback: 'Pick an option first.' });
        return;
      }
      const res = await judge({ answer });
      renderFeedback(container, res);
    }));
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountMcq(container, data, judge));
  }

  // ---------- Fill in the blank: template with ____ → input boxes ----------
  function mountFillBlank(container, data, judge) {
    container.querySelector('[data-role="source-bin"]').style.display = 'none';
    const bins = container.querySelector('[data-role="target-bins"]');
    const code = data.code || data.template || '';
    const blanks = data.blanks || [];
    // Split the template on ____ and splice in input boxes between.
    const parts = code.split(/_{4,}/);
    let html = '<pre class="tmpl-fib-code" style="background:#161b26; border:1px solid #2a3352; border-radius:8px; padding:14px; color:#e8ecf4; font-family:monospace; font-size:0.9rem; white-space:pre-wrap;">';
    parts.forEach((part, i) => {
      html += esc(part);
      if (i < parts.length - 1) {
        const hint = (blanks[i] && blanks[i].hint) ? ` title="${esc(blanks[i].hint)}"` : '';
        html += `<input type="text" class="tmpl-fib-input" data-idx="${i}"${hint}
                 style="background:#1e2538; color:#2dd4bf; border:1px solid #2a3352; border-radius:4px; padding:2px 8px; margin:0 2px; font-family:monospace; font-size:0.9rem; min-width:80px;">`;
      }
    });
    html += '</pre>';
    bins.innerHTML = html;
    container.querySelector('[data-action="submit"]').addEventListener('click', () => _guardedSubmit(container, async () => {
      const inputs = container.querySelectorAll('.tmpl-fib-input');
      const answers = Array.from(inputs).map(inp => inp.value.trim());
      const res = await judge({ answers });
      renderFeedback(container, res);
      // Highlight per-blank correctness if grader returned it
      if (res.item_results && Array.isArray(res.item_results)) {
        res.item_results.forEach((ir, i) => {
          if (inputs[i]) {
            inputs[i].style.borderColor = ir.correct ? '#2dd4bf' : '#f87171';
          }
        });
      }
    }));
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountFillBlank(container, data, judge));
  }

  // ---------- Sequence (parsons + ordering): one source bin, one target bin ordered top-down ----------
  function mountSequence(container, data, judge) {
    const srcList = container.querySelector('[data-role="source-items"]');
    const bins = container.querySelector('[data-role="target-bins"]');
    const items = (data.items || []).slice();
    // Shuffle source on mount
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1)); [items[i], items[j]] = [items[j], items[i]];
    }
    srcList.innerHTML = items.map(it => `<div class="tmpl-item" draggable="true" data-id="${esc(it.id)}">${esc(it.text)}</div>`).join('');
    bins.innerHTML = `<div class="tmpl-bin" data-bin-id="target">
      <h5 class="tmpl-bin-label">Your sequence (drag here in order)</h5>
      <div class="tmpl-item-list" data-role="bin-items"></div>
    </div>`;
    wireDrag(container, { allowMultiple: true, maxPerBin: null });
    container.querySelector('[data-action="submit"]').addEventListener('click', () => _guardedSubmit(container, async () => {
      // 2026-04-22 fix (beginner-agent v8-post-wiring-fix caught): the Go
      // parsons step stores `validation.correct_order` as the literal line
      // TEXT (`["func F() {", "    x := 1", ...]`) but the client was
      // posting item IDs (`["l0","l1",...]`) — never matched, scored 0/8
      // even with correct visible order. Other courses (e.g. non-code
      // ordering) DO store IDs in correct_order. Fix: post BOTH the ID
      // array AND the text array; grader picks whichever matches.
      const targetEls = Array.from(container.querySelectorAll('[data-bin-id="target"] .tmpl-item'));
      const ordered = targetEls.map(el => el.dataset.id);
      const orderedText = targetEls.map(el => (el.textContent || '').trim());
      const res = await judge({ order: ordered, order_text: orderedText });
      renderFeedback(container, res);
      _applyItemResultStyles(container, res, 'ordering');
    }));
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountSequence(container, data, judge));
  }

  // ---------- Categorization: one source bin + N target bins (one per category) ----------
  function mountCategorization(container, data, judge) {
    const srcList = container.querySelector('[data-role="source-items"]');
    const bins = container.querySelector('[data-role="target-bins"]');
    const items = (data.items || []).slice();
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1)); [items[i], items[j]] = [items[j], items[i]];
    }
    srcList.innerHTML = items.map(it => `<div class="tmpl-item" draggable="true" data-id="${esc(it.id)}">${esc(it.text)}</div>`).join('');
    const cats = (data.categories || []);
    bins.innerHTML = cats.map(c => `<div class="tmpl-bin" data-bin-id="${esc(c)}">
      <h5 class="tmpl-bin-label">${esc(c)}</h5>
      <div class="tmpl-item-list" data-role="bin-items"></div>
    </div>`).join('');
    wireDrag(container, { allowMultiple: true });
    container.querySelector('[data-action="submit"]').addEventListener('click', () => _guardedSubmit(container, async () => {
      const mapping = {};
      container.querySelectorAll('.tmpl-bin[data-bin-id]').forEach(bin => {
        const cat = bin.dataset.binId;
        bin.querySelectorAll('.tmpl-item').forEach(it => { mapping[it.dataset.id] = cat; });
      });
      const res = await judge({ mapping });
      renderFeedback(container, res);
      _applyItemResultStyles(container, res, 'categorization');
    }));
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountCategorization(container, data, judge));
  }

  // ---------- SJT: one source bin + N ranked slots ----------
  function mountSjt(container, data, judge) {
    const srcList = container.querySelector('[data-role="source-items"]');
    const bins = container.querySelector('[data-role="target-bins"]');
    const items = (data.items || data.options || []).map((it, i) => ({ id: it.id || `o${i}`, text: it.label || it.text || String(it) }));
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1)); [items[i], items[j]] = [items[j], items[i]];
    }
    srcList.innerHTML = items.map(it => `<div class="tmpl-item" draggable="true" data-id="${esc(it.id)}">${esc(it.text)}</div>`).join('');
    bins.innerHTML = items.map((_, i) => `<div class="tmpl-bin" data-bin-id="rank-${i+1}">
      <h5 class="tmpl-bin-label">Rank ${i+1}${i===0?' (Best)':(i===items.length-1?' (Worst)':'')}</h5>
      <div class="tmpl-item-list" data-role="bin-items"></div>
    </div>`).join('');
    wireDrag(container, { allowMultiple: false, maxPerBin: 1 });
    container.querySelector('[data-action="submit"]').addEventListener('click', () => _guardedSubmit(container, async () => {
      const rankings = [];
      const idToOrder = items.map(it => it.id);
      container.querySelectorAll('.tmpl-bin[data-bin-id^="rank-"]').forEach(bin => {
        const rank = parseInt(bin.dataset.binId.split('-')[1], 10);
        bin.querySelectorAll('.tmpl-item').forEach(it => {
          const oidx = idToOrder.indexOf(it.dataset.id);
          if (oidx >= 0) rankings[oidx] = rank;
        });
      });
      const res = await judge({ rankings });
      renderFeedback(container, res);
      _applyItemResultStyles(container, res, 'sjt');
    }));
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountSjt(container, data, judge));
  }

  // ---------- Code review: clickable-line code block, no drag ----------
  function mountCodeReview(container, data, judge) {
    container.querySelector('[data-role="source-bin"]').style.display = 'none';
    container.querySelector('[data-role="target-bins"]').style.display = 'none';
    const crHost = container.querySelector('[data-role="code-review"]');
    crHost.style.display = 'block';
    const code = data.code || '';
    // 2026-04-22 v7: tag empty/whitespace-only lines distinctly so CSS can
    // collapse their height. User screenshot v6 showed a code_review where
    // every logical block was separated by a blank line (standard Python
    // formatting), producing a lot of visual dead space. Empty lines also
    // shouldn't be clickable-bug-candidates — flagging a blank line is
    // always wrong. Mark them with `.cr-line--empty` and skip the click
    // handler entirely; CSS gives them a short height.
    const lines = code.split('\n');
    crHost.querySelector('code').innerHTML = lines.map((ln, i) => {
      const lineNum = i + 1;
      const isEmpty = !ln.trim();
      const cls = isEmpty ? 'cr-line cr-line--empty' : 'cr-line';
      return `<span class="${cls}" data-line="${lineNum}"><span class="cr-lineno">${lineNum.toString().padStart(3, ' ')}</span>  ${esc(ln)}</span>`;
    }).join('\n');
    // Click-to-flag only on non-empty lines. Flagging a blank line never
    // catches a real bug, and visually empty rows as flagged are confusing.
    crHost.querySelectorAll('.cr-line:not(.cr-line--empty)').forEach(el => {
      el.addEventListener('click', () => el.classList.toggle('flagged'));
    });
    container.querySelector('[data-action="submit"]').addEventListener('click', () => _guardedSubmit(container, async () => {
      const bugLines = Array.from(crHost.querySelectorAll('.cr-line.flagged'))
        .map(el => parseInt(el.dataset.line, 10));
      // Clear prior correct/wrong/missed markers before re-submit
      crHost.querySelectorAll('.cr-line').forEach(el => {
        el.classList.remove('correct-click', 'wrong-click', 'missed-bug');
      });
      const res = await judge({ bug_lines: bugLines });
      // 2026-04-22 v2 — server now emits item_results[].{line, correct,
      // bug_on_line, found_by_user}. Paint per-line:
      //   flagged + correct=true  → green (correctly found a bug)
      //   flagged + correct=false → red   (false positive)
      //   unflagged + bug_on_line + reveal → amber (you missed this one)
      const itemResults = Array.isArray(res.item_results) ? res.item_results : [];
      const byLine = new Map();
      itemResults.forEach(r => {
        if (r && r.line != null) byLine.set(parseInt(r.line, 10), r);
      });
      // Paint flagged lines
      crHost.querySelectorAll('.cr-line.flagged').forEach(el => {
        const ln = parseInt(el.dataset.line, 10);
        const r = byLine.get(ln);
        if (r && r.correct) { el.classList.add('correct-click'); }
        else { el.classList.add('wrong-click'); }
      });
      // On reveal (passed OR attempt-3 where server emits missed rows),
      // paint MISSED bugs on unflagged lines with amber "missed-bug" outline.
      const reveal = res.correct === true || (res.score || 0) >= 0.95 ||
                     itemResults.some(r => r && r.bug_on_line === true && r.found_by_user === false);
      if (reveal) {
        itemResults.forEach(r => {
          if (r && r.bug_on_line === true && r.found_by_user === false && r.line != null) {
            const el = crHost.querySelector(`.cr-line[data-line="${parseInt(r.line, 10)}"]`);
            if (el && !el.classList.contains('flagged')) {
              el.classList.add('missed-bug');
            }
          }
        });
      }
      renderFeedback(container, res);
    }));
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountCodeReview(container, data, judge));
  }

  // ---------- Shared: drag + drop plumbing ----------
  function wireDrag(container, opts) {
    let dragged = null;
    container.querySelectorAll('.tmpl-item').forEach(el => {
      el.addEventListener('dragstart', e => { dragged = el; el.classList.add('dragging'); });
      el.addEventListener('dragend', e => { if (dragged) dragged.classList.remove('dragging'); dragged = null; });
    });
    container.querySelectorAll('.tmpl-bin, .tmpl-source-bin').forEach(bin => {
      bin.addEventListener('dragover', e => {
        e.preventDefault();
        bin.classList.add('drag-over');
      });
      bin.addEventListener('dragleave', () => bin.classList.remove('drag-over'));
      bin.addEventListener('drop', e => {
        e.preventDefault();
        bin.classList.remove('drag-over');
        if (!dragged) return;
        const list = bin.querySelector('[data-role="source-items"]') || bin.querySelector('[data-role="bin-items"]');
        if (!list) return;
        if (opts && opts.maxPerBin && list.children.length >= opts.maxPerBin) return;
        list.appendChild(dragged);
      });
    });
  }

  function renderFeedback(container, res) {
    const f = container.querySelector('[data-role="feedback"]');
    f.className = 'tmpl-feedback';
    const score = res.score || 0;
    if (res.correct || score >= 0.95) f.classList.add('pass');
    else if (score >= 0.5) f.classList.add('partial');
    else f.classList.add('fail');
    // v8.6 GATE C (2026-04-24): render counter ONLY when correctness data
    // is reliable + agrees with the server's score. Previously we counted
    // from item_results regardless of reveal-gate status — producing
    // misleading "0 correct · 6 wrong" for 83% submissions (correctness
    // was stripped but count logic ran anyway) and "(1 correct · 3 wrong)"
    // for MCQ single-select where 4 items render with 1 always-correct
    // leak. Structural fix: trust the score, render the count only when
    // (a) every item has a definite true/false correct flag, AND
    // (b) that count matches round(score × total) within ±1.
    // Otherwise, show the score header only — no misleading tally.
    const itemResults = Array.isArray(res.item_results) ? res.item_results : [];
    const knownRight = itemResults.filter(r => r && r.correct === true).length;
    const knownWrong = itemResults.filter(r => r && r.correct === false).length;
    const hasUnknown = itemResults.some(r => r && (r.correct === null || r.correct === undefined));
    const total = itemResults.length;
    const expectedRight = total > 0 ? Math.round(score * total) : 0;
    const countsAgree = !hasUnknown &&
                        (knownRight + knownWrong === total) &&
                        (Math.abs(knownRight - expectedRight) <= 1);
    let summary = `<strong>Score: ${Math.round(score * 100)}%</strong>`;
    if (total > 0 && countsAgree) {
      summary += ` <span style="color:var(--text-secondary, #9097aa); font-weight:normal;">(${knownRight} of ${total} correct)</span>`;
    }
    f.innerHTML = summary + `<br>${esc(res.feedback || '')}`;
  }

  // 2026-04-22 new: apply per-item red/green styles to items shown in bins
  // after submit. Fixes P1-2 from beginner walkthrough — categorization
  // feedback said "marked in red above" but nothing was actually marked.
  // Server returns item_results with {id, correct, expected_category?,
  // user_category?, user_position?, correct_position?}. We walk the rendered
  // items, match by data-id, and tint the border.
  function _applyItemResultStyles(container, res, kind) {
    const itemResults = Array.isArray(res && res.item_results) ? res.item_results : [];
    if (!itemResults.length) return;
    const byId = new Map();
    itemResults.forEach(r => {
      if (r && (r.id != null)) byId.set(String(r.id), r);
    });
    container.querySelectorAll('.tmpl-bin[data-bin-id] .tmpl-item').forEach(el => {
      const r = byId.get(String(el.dataset.id));
      if (!r) return;
      el.classList.remove('tmpl-item-correct', 'tmpl-item-wrong');
      if (r.correct) {
        el.classList.add('tmpl-item-correct');
        el.style.borderColor = '#2dd4bf';
        el.style.borderWidth = '2px';
        el.style.borderStyle = 'solid';
      } else {
        el.classList.add('tmpl-item-wrong');
        el.style.borderColor = '#f87171';
        el.style.borderWidth = '2px';
        el.style.borderStyle = 'solid';
        // Attach a tooltip naming the correct answer, but only on the
        // wrong picks (so we don't leak unrelated answer-key rows).
        const correct = r.expected_category || r.correct_category ||
                        r.expected_position || r.correct_position ||
                        r.correct_rank;
        if (correct != null) {
          el.title = `Correct: ${String(correct)}`;
        }
      }
    });
  }

  global.SllTemplateDragDrop = { mount };
})(window);
