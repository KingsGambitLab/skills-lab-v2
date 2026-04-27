/* Creator Workspace v2 (F1, 2026-04-27)
 * ----------------------------------------------------------------------
 * All UI code for the dedicated Creator workspace lives here. Loaded by
 * index.html via /creator-assets/workspace.js. Runtime overrides any
 * earlier function definitions of the same name in index.html — the SPA's
 * main file no longer carries the wizard's UI bloat.
 *
 * What this file owns:
 *   - openCreatorPage()        — mounts page chrome into #contentScroll
 *   - renderCreatorWizard()    — dispatches the active step + footer
 *   - renderCreatorFooter()    — page-level sticky CTAs
 *   - renderCreatorStep1..4()  — each step's body content
 *   - F1 outline-edit helpers  — module/step mutators, save scheduler,
 *                                drift detector, ontology-types loader
 *
 * What stays in index.html:
 *   - Hash-routing additions (parseHash / restoreFromHash / updateHash)
 *   - openCreatorWizard() thin alias + closeCreatorWizard()
 *   - Existing tightly-coupled flows (creatorStart / creatorRefine /
 *     creatorReRefine / creatorGenerate / draft persistence / autocomplete /
 *     char meter)
 *
 * Globals consumed (defined in index.html):
 *   - state, creatorState, API, esc(), CREATOR_STEPS, CREATOR_STARTERS
 *   - showCatalog(), goToCatalog(), updateHash(), updateCreatorFab()
 *   - _loadCreatorDraft(), _applyCreatorDraftToDOM()
 *   - refreshAutoReviewBannerVisibility()
 *   - openTemplateBrowser(), showTemplateAutocomplete(), hideTemplateAutocomplete*(),
 *     onTitleAutocompleteKey(), updateCreatorContentMeter(),
 *     creatorFetchUrls(), creatorStart(), creatorRefine(), creatorGenerate(),
 *     creatorGoToCourse(), creatorReRefine(), closeCreatorWizard()
 */

(function () {
  'use strict';

  // ── Page mount ─────────────────────────────────────────────────────

  window.openCreatorPage = function openCreatorPage() {
    // First-visit flag (2026-04-21): remember that the user has discovered
    // the button so the attention-pulse doesn't keep nagging on next loads.
    try { localStorage.setItem('creatorFabOpened', '1'); } catch (e) {}
    const fab = document.getElementById('creatorFab');
    if (fab) fab.classList.remove('pulse');

    // 2026-04-21 draft-persistence: if a draft exists, restore creatorState
    // BEFORE rendering so the wizard lands on the same step the user left on.
    const draft = (typeof _loadCreatorDraft === 'function') ? _loadCreatorDraft() : null;
    if (draft && draft.state) {
      window.creatorState = Object.assign({}, window.creatorState, draft.state);
      if (draft.urlsFetchedMaterial) {
        state._urlsFetchedMaterial = draft.urlsFetchedMaterial;
      }
    } else {
      window.creatorState = {
        step: 1,
        sessionId: null,
        questions: [],
        initialOutline: null,
        refinedOutline: null,
        followUpQuestions: null,
        generatedCourseId: null,
        generatedCourse: null,
      };
    }

    // Tear down catalog/course chrome so the page takes the full pane.
    state.view = 'create';
    state.currentCourse = null;
    state.currentModule = null;
    state.currentModuleData = null;
    document.body.classList.add('catalog-mode');
    ['sidebarCourseInfo', 'sidebarFooter'].forEach(id => {
      const e = document.getElementById(id); if (e) e.style.display = 'none';
    });
    ['moduleList', 'stepDotsContainer', 'stepNavContainer'].forEach(id => {
      const e = document.getElementById(id); if (e) e.innerHTML = '';
    });
    const clickyFab = document.getElementById('clickyFab');
    if (clickyFab) clickyFab.classList.add('hidden');
    const clickyPanel = document.getElementById('clickyPanel');
    if (clickyPanel) clickyPanel.classList.remove('open');
    if (typeof refreshAutoReviewBannerVisibility === 'function') {
      refreshAutoReviewBannerVisibility();
    }

    // Single-row sticky top bar: back link · page title · per-step label ·
    // step indicator · save pill. Replaces the previous util-bar + hero +
    // steps-bar stack so primary content (and the sticky footer CTA) stays
    // above the fold. Hero subtitle moved into per-step body where it has
    // contextual value rather than as standing chrome.
    const scroll = document.getElementById('contentScroll');
    if (!scroll) return;
    scroll.innerHTML = `
      <div class="creator-page">
        <div class="creator-page-topbar">
          <button class="creator-page-back" onclick="closeCreatorWizard()">&larr; Catalog</button>
          <h1 class="creator-page-title">Create a Course</h1>
          <span class="creator-page-substep" id="creatorPageSubstep"></span>
          <div class="creator-steps-bar" id="creatorStepsBar"></div>
          <span class="creator-page-savepill" id="creatorPageSavePill">Drafts auto-save</span>
        </div>
        <div class="creator-body" id="creatorBody"></div>
        <div class="creator-page-footer" id="creatorPageFooter"></div>
      </div>`;

    if (typeof updateHash === 'function') updateHash();
    if (typeof updateCreatorFab === 'function') updateCreatorFab();
    renderCreatorWizard();
    if (draft && draft.fields && typeof _applyCreatorDraftToDOM === 'function') {
      _applyCreatorDraftToDOM(draft);
    }
  };

  // ── Wizard dispatcher ──────────────────────────────────────────────

  window.renderCreatorWizard = function renderCreatorWizard() {
    if (typeof renderCreatorStepsBar === 'function') renderCreatorStepsBar();
    const body = document.getElementById('creatorBody');
    if (!body) return;

    // Per-step label in the topbar — gives orientation ("Setup", "Outline")
    // without consuming a full hero row.
    const sub = document.getElementById('creatorPageSubstep');
    const stepLabels = {
      1: '· Setup',
      2: '· Tailoring',
      3: '· Outline',
      4: '· Done',
    };
    if (sub) sub.textContent = stepLabels[creatorState.step] || '';

    if (creatorState.step === 1) body.innerHTML = renderCreatorStep1();
    else if (creatorState.step === 2) body.innerHTML = renderCreatorStep2();
    else if (creatorState.step === 3) body.innerHTML = renderCreatorStep3();
    else if (creatorState.step === 4) body.innerHTML = renderCreatorStep4();

    renderCreatorFooter();
  };

  window.renderCreatorFooter = function renderCreatorFooter() {
    const foot = document.getElementById('creatorPageFooter');
    if (!foot) return;
    if (creatorState.step === 1) {
      foot.innerHTML = `
        <span class="left">Step 1 of 4 — Setup</span>
        <button class="creator-btn" onclick="closeCreatorWizard()">Cancel</button>
        <button class="creator-btn primary" id="creatorStartBtn" onclick="creatorStart()">Continue &rarr;</button>`;
    } else if (creatorState.step === 2) {
      foot.innerHTML = `
        <span class="left">Step 2 of 4 — Tailoring questions</span>
        <button class="creator-btn" onclick="creatorState.step=1;renderCreatorWizard();">&larr; Back</button>
        <button class="creator-btn primary" id="creatorRefineBtn" onclick="creatorRefine()">Submit answers &rarr;</button>`;
    } else if (creatorState.step === 3) {
      const confirmed = !!creatorState.outlineConfirmed;
      const tip = confirmed
        ? 'Outline confirmed — generation will use these modules.'
        : 'Edit the outline, then click "Looks good" in the side panel before generating.';
      foot.innerHTML = `
        <span class="left">${tip}</span>
        <button class="creator-btn" onclick="creatorState.step=2;renderCreatorWizard();">&larr; Back</button>
        <button class="creator-btn success" id="creatorGenerateBtn" onclick="creatorGenerate()" ${confirmed ? '' : 'disabled'}>Generate Course</button>`;
    } else if (creatorState.step === 4) {
      foot.innerHTML = `
        <span class="left">Course generated successfully.</span>
        <button class="creator-btn" onclick="closeCreatorWizard()">Back to catalog</button>
        <button class="creator-btn primary" onclick="creatorGoToCourse()">Open course &rarr;</button>`;
    } else {
      foot.innerHTML = '';
    }
  };

  // ── Step 1 — Setup ─────────────────────────────────────────────────

  window.renderCreatorStep1 = function renderCreatorStep1() {
    return `
      <div class="creator-shell">
        <div class="creator-shell-main">
          <div class="creator-section">
            <div class="creator-section-header">
              <h2>Topic</h2>
              <span class="hint">Specific is better than broad. Or browse <a href="#" onclick="openTemplateBrowser(); return false;" style="color:var(--accent);">${CREATOR_STARTERS.length} templates</a>.</span>
            </div>
            <div class="creator-form-group" style="position:relative; margin:0;">
              <input class="creator-form-input" id="creatorTitle" type="text" autocomplete="off"
                     placeholder="e.g. Incident response for on-call engineers"
                     oninput="showTemplateAutocomplete()" onfocus="showTemplateAutocomplete()" onblur="hideTemplateAutocompleteSoon()"
                     onkeydown="onTitleAutocompleteKey(event)"
                     role="combobox" aria-autocomplete="list" aria-controls="templateAutocomplete" aria-expanded="false"
                     style="font-size:1.05rem; padding:16px 18px;">
              <div id="templateAutocomplete" style="display:none; position:absolute; top:100%; left:0; right:0; margin-top:4px; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; max-height:320px; overflow-y:auto; z-index:10; box-shadow:0 12px 32px rgba(0,0,0,0.35);"></div>
            </div>
          </div>

          <div class="creator-section">
            <div class="creator-section-header">
              <h2>Course objective</h2>
              <span class="hint">Audience, outcomes, must-know facts.</span>
            </div>
            <textarea class="creator-form-textarea" id="creatorDesc"
                      oninput="updateCreatorContentMeter()"
                      placeholder="Everything you want learners to walk away with — persona, constraints, specific skills, facts they must know verbatim, framework names, metrics.&#10;&#10;Example: &quot;Senior engineers picking up on-call in Q3. They know Linux, not Kubernetes. Must cover our incident runbook v4.2 (MERIDIAN framework, 7 stages), PagerDuty tiers, and the 15-min acknowledgement SLA.&quot;"
                      style="min-height:240px; font-size:0.95rem; padding:14px 16px; resize:vertical;"></textarea>
          </div>

          <input type="hidden" id="creatorType" value="">
          <input type="hidden" id="creatorLevel" value="">
          <input type="hidden" id="creatorMode" value="">
          <input type="hidden" id="creatorArchetype" value="">
        </div>

        <aside class="creator-shell-side">
          <div class="creator-side-card">
            <h4>Supporting materials</h4>
            <p style="font-size:0.82rem; color:var(--text-muted); margin:0 0 14px;">Anything the Creator can read — preference order: objective &rarr; files &rarr; links. <strong style="color:var(--text-secondary);">18,000 chars total.</strong></p>

            <div style="margin-bottom:14px;">
              <label style="font-size:0.72rem; font-weight:700; letter-spacing:0.06em; color:var(--text-muted); text-transform:uppercase; display:block; margin-bottom:6px;">Files</label>
              <input type="file" id="creatorFiles" multiple
                     accept=".pdf,.docx,.pptx,.ppt,.txt,.md"
                     onchange="updateCreatorContentMeter()"
                     style="width:100%; color:var(--text-secondary); font-size:0.82rem; padding:10px 12px; background:var(--bg-tertiary); border:1px dashed var(--border); border-radius:6px;">
              <div style="font-size:0.72rem; color:var(--text-muted); margin-top:4px;">PDF · PPTX · DOCX · TXT · MD</div>
            </div>

            <div>
              <label style="font-size:0.72rem; font-weight:700; letter-spacing:0.06em; color:var(--text-muted); text-transform:uppercase; display:block; margin-bottom:6px;">Link</label>
              <div style="display:flex; gap:8px; align-items:stretch;">
                <input type="url" id="creatorUrls"
                       oninput="updateCreatorContentMeter()"
                       placeholder="https://docs.mycompany.com/handbook"
                       style="flex:1; color:var(--text-primary); font-size:0.84rem; padding:10px 12px; background:var(--bg-tertiary); border:1px solid var(--border); border-radius:6px;">
                <button type="button" id="creatorFetchUrlBtn" onclick="creatorFetchUrls()"
                        style="flex:0 0 auto; padding:10px 14px; font-size:0.82rem; font-weight:600; color:var(--accent); background:var(--bg-tertiary); border:1px solid var(--border); border-radius:6px; cursor:pointer;">Fetch</button>
              </div>
              <div id="creatorUploadStatus" style="font-size:0.74rem; color:var(--text-muted); margin-top:6px;"></div>
            </div>
          </div>

          <div id="creatorContentMeter" class="creator-side-card" style="display:flex; align-items:center; gap:12px; padding:14px 18px;">
            <div style="flex:1;">
              <div id="creatorContentMeterText" style="font-size:0.82rem; color:var(--text-secondary);">0 / 18,000 chars</div>
              <div style="margin-top:6px; height:6px; background:var(--bg-tertiary); border-radius:3px; overflow:hidden;">
                <div id="creatorContentMeterBar" style="height:100%; width:0%; background:#34d399; transition:width 0.2s, background 0.2s;"></div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <style>
        .tmpl-row { display:block; padding:10px 14px; border-bottom:1px solid var(--border); cursor:pointer; transition:background 0.12s; }
        .tmpl-row:hover, .tmpl-row.kb-focus { background: rgba(124,58,237,0.08); }
        .tmpl-row:last-child { border-bottom: 0; }
        .tmpl-title { font-size:0.92rem; color:var(--text-primary); font-weight:600; margin-bottom:2px; }
        .tmpl-meta { font-size:0.76rem; color:var(--text-muted); }
        .tmpl-hint { padding:10px 14px; font-size:0.78rem; color:var(--text-muted); font-style:italic; }
      </style>
    `;
  };

  // ── Step 2 — Clarifying questions ──────────────────────────────────

  window.renderCreatorStep2 = function renderCreatorStep2() {
    // Each clarifying question is a typeahead combobox: input + dropdown of
    // suggestions that filters as you type, but always accepts free text.
    // ARIA wired for screen readers. The combo state lives on the input
    // element; existing onComboInput / showComboDropdown / etc. handle it.
    const questionsHtml = creatorState.questions.map((q, qIdx) => {
      const suggestions = (q.type === 'choice' && Array.isArray(q.options)) ? q.options : [];
      const comboId = `creatorCombo_${qIdx}`;
      const ddId = comboId + '_dd';
      const suggestionsJson = JSON.stringify(suggestions).replace(/"/g, '&quot;');
      const hint = suggestions.length
        ? `${suggestions.length} suggestion${suggestions.length === 1 ? '' : 's'} — or write your own`
        : 'Type your own answer';
      return `<div class="creator-question-item" style="margin-bottom:22px;">
        <label for="${comboId}" class="creator-question-text" style="margin-bottom:8px; display:block; font-size:0.96rem; color:var(--text-primary); font-weight:600;">${esc(q.question)}</label>
        <div class="combo-wrap" style="position:relative;" role="combobox" aria-expanded="false" aria-haspopup="listbox" aria-owns="${ddId}">
          <input class="creator-form-input creator-answer combo-input"
                 id="${comboId}"
                 data-qid="${esc(q.id)}"
                 data-suggestions="${suggestionsJson}"
                 type="text"
                 autocomplete="off"
                 role="combobox"
                 aria-autocomplete="list"
                 aria-controls="${ddId}"
                 aria-expanded="false"
                 placeholder="Type your answer or press ↓ for suggestions"
                 oninput="onComboInput('${comboId}')"
                 onfocus="showComboDropdown('${comboId}')"
                 onblur="hideComboDropdownSoon('${comboId}')"
                 onkeydown="onComboKey(event, '${comboId}')"
                 style="font-size:0.95rem; padding:12px 14px;">
          <div class="combo-hint" style="font-size:0.74rem; color:var(--text-muted); margin-top:6px;">${esc(hint)}</div>
          <div class="combo-dropdown"
               id="${ddId}"
               role="listbox"
               style="display:none; position:absolute; top:100%; left:0; right:0; margin-top:4px; background:var(--bg-card); border:1px solid var(--border); border-radius:8px; max-height:240px; overflow-y:auto; z-index:20; box-shadow:0 12px 32px rgba(0,0,0,0.35);">
          </div>
        </div>
      </div>`;
    }).join('');

    // Side panel: read-only recap of Step 1 (Topic + Objective). The
    // creator can re-read what they're tailoring without going back, plus
    // an "Edit setup" link that sends them to Step 1.
    const topic = (creatorState && creatorState.title) || '(no topic set)';
    const objective = (creatorState && creatorState.description) || '';
    const objClipped = objective.length > 360 ? objective.slice(0, 360) + '…' : objective;
    const recapHtml = `
      <div class="creator-side-card">
        <h4>From your setup</h4>
        <div class="recap-row">
          <span class="label">Topic</span>
          <div>${topic ? esc(topic) : '<span class="recap-empty">(blank)</span>'}</div>
        </div>
        <div class="recap-row">
          <span class="label">Objective</span>
          <div>${objClipped ? esc(objClipped) : '<span class="recap-empty">(blank)</span>'}</div>
        </div>
        <div class="recap-row">
          <a href="#" onclick="event.preventDefault();creatorState.step=1;renderCreatorWizard();" style="color:var(--accent); text-decoration:none; font-size:0.82rem;">&larr; Edit setup</a>
        </div>
      </div>`;

    return `
      <div class="creator-shell">
        <div class="creator-shell-main">
          <div class="creator-section">
            <div class="creator-section-header">
              <h2>Tailoring questions</h2>
              <span class="hint">Skip any that don't apply — we'll work with whatever you give us.</span>
            </div>
            ${questionsHtml || '<p style="color:var(--text-muted); font-size:0.86rem;">No questions to answer — you can submit and proceed.</p>'}
          </div>
        </div>
        <aside class="creator-shell-side">
          ${recapHtml}
        </aside>
      </div>
    `;
  };

  // ── Step 3 — Outline workspace (the F1 surface) ────────────────────

  // Lazy-loaded ontology cache. First render uses defaults; the fetch
  // resolves and triggers a re-render that swaps in the registry values.
  const CREATOR_DEFAULT_TYPES = [
    { id: 'concept',         description: 'Teaching content (HTML)' },
    { id: 'code_exercise',   description: 'Hands-on coding with hidden tests' },
    { id: 'code_review',     description: 'Find bugs in realistic code' },
    { id: 'mcq',             description: 'Multiple-choice knowledge check' },
    { id: 'scenario_branch', description: 'Decision-making with consequences' },
    { id: 'system_build',    description: 'Build & deploy a real system' },
  ];

  async function _creatorLoadAssignmentTypes() {
    if (creatorState._assignmentTypes && creatorState._assignmentTypes.length) return;
    try {
      const r = await fetch(`${API}/creator/ontology/assignments`);
      if (r.ok) {
        const types = await r.json();
        if (Array.isArray(types) && types.length) {
          creatorState._assignmentTypes = types;
          return;
        }
      }
    } catch (_) { /* fall through to defaults */ }
    creatorState._assignmentTypes = CREATOR_DEFAULT_TYPES;
  }
  window._creatorLoadAssignmentTypes = _creatorLoadAssignmentTypes;

  function _creatorTypeOptions(selectedType) {
    const types = creatorState._assignmentTypes || CREATOR_DEFAULT_TYPES;
    const ids = new Set(types.map(t => t.id));
    if (selectedType && !ids.has(selectedType)) {
      types.push({ id: selectedType, description: '(legacy)' });
    }
    return types.map(t => {
      const sel = t.id === selectedType ? ' selected' : '';
      return `<option value="${esc(t.id)}"${sel}>${esc(t.id)}</option>`;
    }).join('');
  }

  // Outline mutations — every edit goes through these; never edit
  // refinedOutline directly from inline handlers, so the save scheduler
  // and re-render fire consistently.
  function _creatorMutateOutline(mutator, opts) {
    opts = opts || {};
    const o = creatorState.refinedOutline;
    if (!o || !Array.isArray(o.modules)) return;
    mutator(o);
    o.modules.forEach((m, i) => { m.position = i + 1; });
    if (opts.structural !== false) creatorState.outlineConfirmed = false;
    _creatorScheduleSaveOutline();
    if (opts.rerender !== false) renderCreatorWizard();
  }

  window.creatorRenameModule = function (idx, value) {
    const o = creatorState.refinedOutline;
    if (!o || !o.modules[idx]) return;
    o.modules[idx].title = value;
    _creatorScheduleSaveOutline();
  };

  window.creatorMoveModule = function (idx, dir) {
    _creatorMutateOutline(o => {
      const j = idx + dir;
      if (j < 0 || j >= o.modules.length) return;
      const tmp = o.modules[idx];
      o.modules[idx] = o.modules[j];
      o.modules[j] = tmp;
      // Follow the active module to its new position so the expansion
      // doesn't jump to a different module after a swap.
      if (creatorState._activeModuleIdx === idx) creatorState._activeModuleIdx = j;
      else if (creatorState._activeModuleIdx === j) creatorState._activeModuleIdx = idx;
    });
  };

  window.creatorDeleteModule = function (idx) {
    if (!confirm('Delete this module and all its steps?')) return;
    _creatorMutateOutline(o => {
      o.modules.splice(idx, 1);
      // Adjust active-module pointer: deleted-active → collapse all;
      // deleted-before-active → shift active down by 1.
      const a = creatorState._activeModuleIdx;
      if (a === idx) creatorState._activeModuleIdx = null;
      else if (typeof a === 'number' && a > idx) creatorState._activeModuleIdx = a - 1;
    });
  };

  window.creatorAddModule = function () {
    _creatorMutateOutline(o => {
      o.modules.push({
        title: `New Module ${o.modules.length + 1}`,
        position: o.modules.length + 1,
        objectives: [],
        steps: [{ title: 'New Step', exercise_type: 'concept', description: '' }],
      });
      // Auto-expand the new module so the creator sees what they just added.
      creatorState._activeModuleIdx = o.modules.length - 1;
    });
  };

  window.creatorRenameStep = function (modIdx, stepIdx, value) {
    const o = creatorState.refinedOutline;
    if (!o || !o.modules[modIdx] || !o.modules[modIdx].steps[stepIdx]) return;
    o.modules[modIdx].steps[stepIdx].title = value;
    _creatorScheduleSaveOutline();
  };

  window.creatorChangeStepType = function (modIdx, stepIdx, value) {
    _creatorMutateOutline(o => {
      o.modules[modIdx].steps[stepIdx].exercise_type = value;
    });
  };

  window.creatorEditStepDesc = function (modIdx, stepIdx, value) {
    const o = creatorState.refinedOutline;
    if (!o || !o.modules[modIdx] || !o.modules[modIdx].steps[stepIdx]) return;
    o.modules[modIdx].steps[stepIdx].description = value;
    _creatorScheduleSaveOutline();
  };

  window.creatorMoveStep = function (modIdx, stepIdx, dir) {
    _creatorMutateOutline(o => {
      const steps = o.modules[modIdx].steps;
      const j = stepIdx + dir;
      if (j < 0 || j >= steps.length) return;
      const tmp = steps[stepIdx];
      steps[stepIdx] = steps[j];
      steps[j] = tmp;
    });
  };

  window.creatorDeleteStep = function (modIdx, stepIdx) {
    _creatorMutateOutline(o => {
      o.modules[modIdx].steps.splice(stepIdx, 1);
    });
  };

  window.creatorAddStep = function (modIdx) {
    _creatorMutateOutline(o => {
      o.modules[modIdx].steps.push({
        title: 'New Step',
        exercise_type: 'concept',
        description: '',
      });
    });
  };

  window.creatorToggleStepDesc = function (modIdx, stepIdx) {
    const key = `${modIdx}_${stepIdx}`;
    if (!creatorState._descOpen) creatorState._descOpen = {};
    creatorState._descOpen[key] = !creatorState._descOpen[key];
    renderCreatorWizard();
  };

  // ── Module-accordion helpers (F1 v3, 2026-04-27) ─────────────────
  // One module is expanded at a time. _activeModuleIdx defaults to 0 on
  // first entry; clicking a row toggles it. Per-module review state
  // lives on each module as `_reviewed` (boolean). Saved with the
  // outline draft via _saveCreatorDraft (pydantic strips it on the
  // /outline round-trip but it survives in localStorage between reloads).

  window.creatorToggleModule = function (idx) {
    const cur = creatorState._activeModuleIdx;
    creatorState._activeModuleIdx = (cur === idx) ? null : idx;
    renderCreatorWizard();
  };

  window.creatorMarkModuleReviewed = function (idx) {
    const o = creatorState.refinedOutline;
    if (!o || !o.modules[idx]) return;
    o.modules[idx]._reviewed = true;
    _creatorScheduleSaveOutline();
    renderCreatorWizard();
  };

  window.creatorUnmarkModuleReviewed = function (idx) {
    const o = creatorState.refinedOutline;
    if (!o || !o.modules[idx]) return;
    o.modules[idx]._reviewed = false;
    _creatorScheduleSaveOutline();
    renderCreatorWizard();
  };

  // Stop click propagation when interacting with controls inside a
  // collapsed row's right side (move/delete buttons) — otherwise the
  // row's onclick toggles expansion and the user fights the UI.
  window.creatorStopProp = function (event) {
    if (event && typeof event.stopPropagation === 'function') {
      event.stopPropagation();
    }
  };

  // Save scheduler — debounced POST /api/creator/outline.
  let _creatorOutlineSaveTimer = null;
  let _creatorOutlineSaveSeq = 0;

  function _creatorScheduleSaveOutline() {
    if (_creatorOutlineSaveTimer) clearTimeout(_creatorOutlineSaveTimer);
    _creatorSetSaveStatus('Saving…', '');
    _creatorOutlineSaveTimer = setTimeout(_creatorSaveOutline, 600);
    // F1 v2 (2026-04-27): also snapshot the local draft on every outline
    // mutation so a refresh restores the latest state. The backend POST
    // can fail (offline, 4xx) but the localStorage draft is what the
    // creator actually sees on reload — keep both in lockstep. Without
    // this, structural mutations (move/delete/add/mark-reviewed) bypass
    // the input-event listener and never reach localStorage.
    if (typeof _saveCreatorDraft === 'function') _saveCreatorDraft();
  }
  window._creatorScheduleSaveOutline = _creatorScheduleSaveOutline;

  async function _creatorSaveOutline() {
    if (!creatorState.sessionId || !creatorState.refinedOutline) return;
    const seq = ++_creatorOutlineSaveSeq;
    try {
      const r = await fetch(`${API}/creator/outline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: creatorState.sessionId,
          outline: creatorState.refinedOutline,
        }),
      });
      if (seq !== _creatorOutlineSaveSeq) return;  // newer save in flight
      if (r.ok) _creatorSetSaveStatus('Saved', 'saved');
      else {
        const body = await r.json().catch(() => ({}));
        _creatorSetSaveStatus(`Save failed: ${body.detail || r.status}`, 'error');
      }
    } catch (e) {
      if (seq !== _creatorOutlineSaveSeq) return;
      _creatorSetSaveStatus('Save failed (offline?)', 'error');
    }
  }

  function _creatorSetSaveStatus(text, klass) {
    const el = document.getElementById('creatorOutlineSaveStatus');
    if (!el) return;
    el.textContent = text;
    el.className = 'creator-outline-save-status' + (klass ? ' ' + klass : '');
  }

  // Module-count drift detection (CLAUDE.md "post-refine structural diff").
  function _creatorDetectSourceModuleCount() {
    const parts = [
      creatorState.description || '',
      creatorState.sourceMaterial || '',
      (typeof state !== 'undefined' && state._urlsFetchedMaterial) || '',
    ];
    const src = parts.filter(Boolean).join('\n');
    if (!src) return null;
    const matches = src.matchAll(/\b(?:module|week|unit)\s*(\d{1,2})\s*[:.\-]/gi);
    let max = 0;
    for (const m of matches) {
      const n = parseInt(m[1], 10);
      if (n > max && n < 50) max = n;
    }
    return max >= 2 ? max : null;
  }
  window._creatorDetectSourceModuleCount = _creatorDetectSourceModuleCount;

  // Render one module's expanded body — step list with edit controls + the
  // module-level controls (rename, move/delete, mark reviewed). Pulled out
  // of the main render so the row layout stays scannable.
  function _renderModuleDetail(mod, mIdx, totalModules) {
    const reviewed = !!mod._reviewed;
    const stepsHtml = (mod.steps || []).map((s, sIdx) => {
      const descKey = `${mIdx}_${sIdx}`;
      const descOpen = creatorState._descOpen && creatorState._descOpen[descKey];
      const stepRow = `
        <div class="creator-step-edit">
          <input class="creator-edit-input step" value="${esc(s.title || '')}"
                 oninput="creatorRenameStep(${mIdx}, ${sIdx}, this.value)" />
          <select class="creator-edit-select"
                  onchange="creatorChangeStepType(${mIdx}, ${sIdx}, this.value)">
            ${_creatorTypeOptions(s.exercise_type || 'concept')}
          </select>
          <button class="creator-icon-btn" title="Move up"
                  onclick="creatorMoveStep(${mIdx}, ${sIdx}, -1)"
                  ${sIdx === 0 ? 'disabled' : ''}>&uarr;</button>
          <button class="creator-icon-btn" title="Move down"
                  onclick="creatorMoveStep(${mIdx}, ${sIdx}, 1)"
                  ${sIdx === ((mod.steps || []).length - 1) ? 'disabled' : ''}>&darr;</button>
          <button class="creator-icon-btn danger" title="Delete step"
                  onclick="creatorDeleteStep(${mIdx}, ${sIdx})">&times;</button>
        </div>`;
      const descRow = `
        <div class="creator-step-desc-row">
          <button class="creator-step-desc-toggle"
                  onclick="creatorToggleStepDesc(${mIdx}, ${sIdx})">
            ${descOpen ? '- hide description' : '+ description' + (s.description ? ' (set)' : '')}
          </button>
          ${descOpen ? `<textarea class="creator-step-desc-textarea"
                           placeholder="What this step teaches / what the learner does..."
                           oninput="creatorEditStepDesc(${mIdx}, ${sIdx}, this.value)">${esc(s.description || '')}</textarea>` : ''}
        </div>`;
      return stepRow + descRow;
    }).join('');

    const objHtml = (mod.objectives || []).length
      ? `<ul class="creator-module-objectives" style="margin: 0 0 12px;">${mod.objectives.map(o => `<li>${esc(o)}</li>`).join('')}</ul>`
      : '';

    return `
      <div class="creator-module-detail">
        <div class="module-title-input-row">
          <input class="creator-edit-input" value="${esc(mod.title || '')}" placeholder="Module title"
                 oninput="creatorRenameModule(${mIdx}, this.value)" />
        </div>
        ${objHtml}
        ${stepsHtml || '<p style="color:var(--text-muted); font-size:0.82rem; margin: 8px 0;">No steps yet.</p>'}
        <button class="creator-add-btn step" style="margin-left: 0;" onclick="creatorAddStep(${mIdx})">+ Add step</button>

        <div class="module-actions">
          <button class="creator-icon-btn" title="Move module up"
                  onclick="creatorMoveModule(${mIdx}, -1)"
                  ${mIdx === 0 ? 'disabled' : ''}>&uarr; Move up</button>
          <button class="creator-icon-btn" title="Move module down"
                  onclick="creatorMoveModule(${mIdx}, 1)"
                  ${mIdx === (totalModules - 1) ? 'disabled' : ''}>&darr; Move down</button>
          <button class="creator-icon-btn danger" title="Delete module"
                  onclick="creatorDeleteModule(${mIdx})">&times; Delete module</button>
          <span class="left-spacer"></span>
          ${reviewed
            ? `<button class="review-btn reviewed"
                       onclick="creatorUnmarkModuleReviewed(${mIdx})">&#10003; Reviewed — undo</button>`
            : `<button class="review-btn"
                       onclick="creatorMarkModuleReviewed(${mIdx})">Mark module reviewed</button>`
          }
        </div>
      </div>`;
  }

  window.renderCreatorStep3 = function renderCreatorStep3() {
    if (!creatorState._assignmentTypes) {
      _creatorLoadAssignmentTypes().then(() => {
        if (creatorState.step === 3) renderCreatorWizard();
      });
    }

    const outline = creatorState.refinedOutline || { modules: [] };
    const modules = outline.modules || [];
    const totalSteps = modules.reduce((acc, m) => acc + (m.steps || []).length, 0);
    const reviewedCount = modules.filter(m => m && m._reviewed).length;
    const allReviewed = modules.length > 0 && reviewedCount === modules.length;
    const confirmed = !!creatorState.outlineConfirmed;
    const sourceModuleCount = _creatorDetectSourceModuleCount();
    const belowLimits = modules.length < 2 || totalSteps < 6;

    // Default-expand the first module on first entry, then preserve selection.
    if (creatorState._activeModuleIdx === undefined && modules.length) {
      creatorState._activeModuleIdx = 0;
    }
    const activeIdx = creatorState._activeModuleIdx;

    // ── Banners (limits + drift) ──
    let outlineBanners = '';
    if (modules.length < 2) {
      outlineBanners += `<div class="creator-outline-banner error">
        <span class="creator-outline-banner-icon">!</span>
        <span>At least <strong>2 modules</strong> required to generate.</span>
      </div>`;
    } else if (totalSteps < 6) {
      outlineBanners += `<div class="creator-outline-banner error">
        <span class="creator-outline-banner-icon">!</span>
        <span>At least <strong>6 steps total</strong> required to generate (currently ${totalSteps}).</span>
      </div>`;
    }
    if (sourceModuleCount && Math.abs(modules.length - sourceModuleCount) >= 1) {
      const delta = modules.length - sourceModuleCount;
      const verb = delta > 0 ? `${delta} more` : `${-delta} fewer`;
      outlineBanners += `<div class="creator-outline-banner warn">
        <span class="creator-outline-banner-icon">!</span>
        <span>Source material enumerates <strong>${sourceModuleCount}</strong> modules; outline has <strong>${modules.length}</strong> (${verb}). Verify before generating.</span>
      </div>`;
    }

    // ── Module index (one card per module, expand-on-click) ──
    const cardsHtml = modules.map((mod, mIdx) => {
      const expanded = activeIdx === mIdx;
      const reviewed = !!mod._reviewed;
      const stepCount = (mod.steps || []).length;
      const cardClasses = ['creator-module-card'];
      if (expanded) cardClasses.push('expanded');
      if (reviewed) cardClasses.push('reviewed');
      return `
        <div class="${cardClasses.join(' ')}">
          <div class="creator-module-row" onclick="creatorToggleModule(${mIdx})">
            <span class="chev">&#9656;</span>
            <span class="pos">${mIdx + 1}.</span>
            <span class="title">${esc(mod.title || '(untitled module)')}</span>
            <span class="meta">${stepCount} step${stepCount === 1 ? '' : 's'}</span>
            <span class="pill ${reviewed ? 'reviewed' : ''}">${reviewed ? '✓ Reviewed' : 'Pending'}</span>
          </div>
          ${expanded ? _renderModuleDetail(mod, mIdx, modules.length) : ''}
        </div>`;
    }).join('');

    const outlineHtml = `
      <div class="creator-section">
        <div class="creator-section-header">
          <h2>Outline</h2>
          <span class="hint" id="creatorOutlineSaveStatus"></span>
        </div>
        ${outlineBanners}
        <div class="creator-module-list">
          ${cardsHtml || '<p style="color:var(--text-muted)">No modules in outline.</p>'}
        </div>
        <button class="creator-add-module-btn" onclick="creatorAddModule()">+ Add module</button>
      </div>`;

    // ── Side panel ──
    const summaryCard = `
      <div class="creator-side-card">
        <h4>Course summary</h4>
        <div class="stat"><span>Modules</span><strong>${modules.length}</strong></div>
        <div class="stat"><span>Total steps</span><strong>${totalSteps}</strong></div>
        <div class="stat"><span>Reviewed</span><strong>${reviewedCount} of ${modules.length}</strong></div>
        ${creatorState.title ? `<div class="recap-row" style="border-top:1px solid var(--border); margin-top:8px; padding-top:10px;">
          <span class="label">Topic</span>
          <div>${esc(creatorState.title)}</div>
        </div>` : ''}
      </div>`;

    let confirmHint;
    if (belowLimits) {
      confirmHint = 'Add modules/steps to meet the minimum (2 modules, 6 steps) before confirming.';
    } else if (!allReviewed) {
      confirmHint = `Review each module — ${modules.length - reviewedCount} left.`;
    } else if (confirmed) {
      confirmHint = 'Outline confirmed. Generation will use these modules.';
    } else {
      confirmHint = 'All modules reviewed. Confirm to enable Generate.';
    }

    const confirmCard = `
      <div class="creator-confirm-bar ${confirmed ? 'confirmed' : ''}">
        <div class="creator-confirm-bar-text">${esc(confirmHint)}</div>
        ${confirmed
          ? `<a href="#" onclick="event.preventDefault();creatorState.outlineConfirmed=false;renderCreatorWizard();" style="font-size:0.82rem;">Edit again</a>`
          : `<button class="creator-btn primary" id="creatorConfirmBtn"
                     onclick="creatorState.outlineConfirmed=true;renderCreatorWizard();"
                     ${(belowLimits || !allReviewed) ? 'disabled' : ''}>Looks good</button>`
        }
      </div>`;

    let followUpsCard = '';
    if (creatorState.followUpQuestions && creatorState.followUpQuestions.length) {
      followUpsCard = `
        <div class="creator-side-card">
          <h4>Follow-up questions</h4>
          ${creatorState.followUpQuestions.map(fq => `
            <div style="margin-bottom:10px;">
              <div style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:4px;">${esc(fq.question)}</div>
              <input class="creator-form-input creator-followup-answer" data-fqid="${esc(fq.id)}" placeholder="Optional response" style="font-size:0.84rem; padding:8px 10px;">
            </div>`).join('')}
        </div>`;
    }

    const refineCard = `
      <div class="creator-side-card">
        <h4>Re-refine with the LLM</h4>
        <textarea class="creator-form-textarea" id="creatorFeedback" placeholder="Request changes — add modules, adjust difficulty, etc." style="min-height:90px; font-size:0.84rem; padding:10px 12px;"></textarea>
        <button class="creator-btn" id="creatorReRefineBtn" onclick="creatorReRefine()" style="width:100%; margin-top:10px; padding:9px;">Refine again</button>
      </div>`;

    return `
      <div class="creator-shell">
        <div class="creator-shell-main">
          ${outlineHtml}
        </div>
        <aside class="creator-shell-side">
          ${summaryCard}
          ${confirmCard}
          ${followUpsCard}
          ${refineCard}
        </aside>
      </div>
    `;
  };

  // ── Step 4 — Done ──────────────────────────────────────────────────

  window.renderCreatorStep4 = function renderCreatorStep4() {
    const title = creatorState.generatedCourse?.title || creatorState.title || 'your course';
    const refined = creatorState.refinedOutline || { modules: [] };
    const moduleCount = (refined.modules || []).length;
    const totalSteps = (refined.modules || []).reduce(
      (acc, m) => acc + ((m.steps || []).length), 0);
    const firstModuleTitle = (refined.modules && refined.modules[0])
      ? refined.modules[0].title : '';

    return `
      <div class="creator-done-hero">
        <span class="icon">&#10024;</span>
        <h2>Course Created</h2>
        <p class="subtitle">"${esc(title)}" is ready for learners.</p>
        ${moduleCount ? `<div class="preview">
          <strong>What's inside</strong>
          ${moduleCount} module${moduleCount === 1 ? '' : 's'} · ${totalSteps} step${totalSteps === 1 ? '' : 's'}${firstModuleTitle ? `<br>First up: ${esc(firstModuleTitle)}` : ''}
        </div>` : ''}
      </div>
    `;
  };
})();
