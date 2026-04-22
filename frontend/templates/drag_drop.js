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

  function mount(containerEl, data, judgeFn, options) {
    options = options || {};
    const ex = data.exercise_type;
    containerEl.querySelector('[data-slot="title"]').textContent = data.title || '';
    const briefEl = containerEl.querySelector('[data-slot="briefing"]');
    if (briefEl) briefEl.innerHTML = data.briefing || '';

    if (ex === 'code_review') return mountCodeReview(containerEl, data, judgeFn);
    if (ex === 'categorization') return mountCategorization(containerEl, data, judgeFn);
    if (ex === 'sjt') return mountSjt(containerEl, data, judgeFn);
    // parsons / ordering fall through to the generic single-target case
    return mountSequence(containerEl, data, judgeFn);
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
    container.querySelector('[data-action="submit"]').addEventListener('click', async () => {
      const ordered = Array.from(container.querySelectorAll('[data-bin-id="target"] .tmpl-item'))
        .map(el => el.dataset.id);
      const res = await judge({ order: ordered });
      renderFeedback(container, res);
    });
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
    container.querySelector('[data-action="submit"]').addEventListener('click', async () => {
      const mapping = {};
      container.querySelectorAll('.tmpl-bin[data-bin-id]').forEach(bin => {
        const cat = bin.dataset.binId;
        bin.querySelectorAll('.tmpl-item').forEach(it => { mapping[it.dataset.id] = cat; });
      });
      const res = await judge({ mapping });
      renderFeedback(container, res);
    });
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
    container.querySelector('[data-action="submit"]').addEventListener('click', async () => {
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
    });
    container.querySelector('[data-action="reset"]').addEventListener('click', () => mountSjt(container, data, judge));
  }

  // ---------- Code review: clickable-line code block, no drag ----------
  function mountCodeReview(container, data, judge) {
    container.querySelector('[data-role="source-bin"]').style.display = 'none';
    container.querySelector('[data-role="target-bins"]').style.display = 'none';
    const crHost = container.querySelector('[data-role="code-review"]');
    crHost.style.display = 'block';
    const code = data.code || '';
    const lines = code.split('\n');
    crHost.querySelector('code').innerHTML = lines.map((ln, i) => {
      const lineNum = i + 1;
      return `<span class="cr-line" data-line="${lineNum}"><span class="cr-lineno">${lineNum.toString().padStart(3, ' ')}</span>  ${esc(ln)}</span>`;
    }).join('\n');
    crHost.querySelectorAll('.cr-line').forEach(el => {
      el.addEventListener('click', () => el.classList.toggle('flagged'));
    });
    container.querySelector('[data-action="submit"]').addEventListener('click', async () => {
      const bugLines = Array.from(crHost.querySelectorAll('.cr-line.flagged'))
        .map(el => parseInt(el.dataset.line, 10));
      const res = await judge({ bug_lines: bugLines });
      // Apply correct/wrong classes to flagged lines per server response
      const correctSet = new Set((res.item_results || []).filter(r => r.correct).map(r => r.line));
      const myFlags = new Set(bugLines);
      crHost.querySelectorAll('.cr-line.flagged').forEach(el => {
        const ln = parseInt(el.dataset.line, 10);
        if (correctSet.has(ln)) { el.classList.add('correct-click'); }
        else { el.classList.add('wrong-click'); }
      });
      renderFeedback(container, res);
    });
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
    f.innerHTML = `<strong>Score: ${Math.round(score * 100)}%</strong><br>${esc(res.feedback || '')}`;
  }

  global.SllTemplateDragDrop = { mount };
})(window);
