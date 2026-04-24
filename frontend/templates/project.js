/**
 * project template — handles system_build / github_classroom_capstone / cluster_state_check.
 *
 * mount(containerEl, data, handlers)
 *   data = { exercise_type, title, problem_statement, phases: [{id, title}],
 *            checklist: [{id, label}], starter_repo?, gha_workflow_check?,
 *            endpoint_check? }
 *   handlers = { judgeFn(submission) => Promise<validateResult>,
 *                checkGhaFn(runUrl) => Promise<{ok, conclusion, run_id, detail}> }
 *
 * The learner clicks through phases + checklist, pastes a GHA run URL or
 * deployment URL (when applicable), and submits. Grader validates + renders
 * feedback.
 */
(function (global) {
  'use strict';

  function esc(s) { return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  function mount(container, data, handlers) {
    handlers = handlers || {};
    // 2026-04-22 v6: title slot removed from template HTML. Guarded.
    const _titleEl = container.querySelector('[data-slot="title"]');
    if (_titleEl) _titleEl.textContent = data.title || '';
    const pb = container.querySelector('[data-slot="problem_statement"]');
    if (pb) pb.innerHTML = data.problem_statement || '';

    // Starter repo banner
    if (data.starter_repo && data.starter_repo.url) {
      const banner = container.querySelector('[data-role="clone-banner"]');
      banner.style.display = '';
      const a = banner.querySelector('[data-role="clone-url"]');
      a.href = data.starter_repo.url;
      a.textContent = data.starter_repo.url;
      banner.querySelector('[data-role="clone-meta"]').textContent =
        data.starter_repo.ref ? `(ref: ${data.starter_repo.ref})` : '';
    }

    // Phases
    const phaseList = container.querySelector('[data-role="phase-list"]');
    const phases = (data.phases || []);
    phaseList.innerHTML = phases.map(p =>
      `<div class="tmpl-phase-item" data-phase-id="${esc(p.id)}">
         <span class="tmpl-phase-icon">○</span>
         <span>${esc(p.title)}</span>
       </div>`
    ).join('');
    phaseList.querySelectorAll('.tmpl-phase-item').forEach(el => {
      el.addEventListener('click', () => {
        el.classList.toggle('done');
        el.querySelector('.tmpl-phase-icon').textContent = el.classList.contains('done') ? '✓' : '○';
      });
    });

    // Checklist
    const checkList = container.querySelector('[data-role="checklist-list"]');
    const checklist = (data.checklist || []);
    checkList.innerHTML = checklist.map(c =>
      `<label class="tmpl-check-item" data-check-id="${esc(c.id)}">
         <input type="checkbox" />
         <span>${esc(c.label)}</span>
       </label>`
    ).join('');
    checkList.querySelectorAll('.tmpl-check-item').forEach(el => {
      el.querySelector('input').addEventListener('change', (e) => {
        el.classList.toggle('done', e.target.checked);
      });
    });

    // GHA widget
    const ghaWidget = container.querySelector('[data-role="gha-widget"]');
    const ghaCfg = data.gha_workflow_check;
    if (ghaCfg) {
      ghaWidget.style.display = '';
      if (ghaCfg.workflow_file) {
        ghaWidget.querySelector('[data-role="gha-workflow-file"]').textContent = ghaCfg.workflow_file;
      }
      ghaWidget.querySelector('[data-action="check-gha"]').addEventListener('click', async () => {
        const urlInput = ghaWidget.querySelector('[data-role="gha-run-url"]');
        const runUrl = (urlInput.value || '').trim();
        const resEl = ghaWidget.querySelector('[data-role="gha-result"]');
        resEl.style.display = '';
        resEl.className = 'tmpl-gha-result pending';
        resEl.textContent = 'Polling GitHub Actions…';
        if (!handlers.checkGhaFn) {
          resEl.className = 'tmpl-gha-result fail';
          resEl.textContent = 'Check function not wired. Tell your instructor.';
          return;
        }
        try {
          const r = await handlers.checkGhaFn(runUrl);
          if (r.ok) {
            resEl.className = 'tmpl-gha-result ok';
            resEl.textContent = `✓ GitHub Actions run ${r.run_id} succeeded. Conclusion: ${r.conclusion}.`;
          } else {
            resEl.className = 'tmpl-gha-result fail';
            resEl.textContent = `✗ ${r.detail || 'CI did not pass.'}`;
          }
        } catch (e) {
          resEl.className = 'tmpl-gha-result fail';
          resEl.textContent = 'Network error: ' + (e.message || e);
        }
      });
    }

    // Endpoint widget
    const epWidget = container.querySelector('[data-role="endpoint-widget"]');
    if (data.endpoint_check && data.endpoint_check.url) {
      epWidget.style.display = '';
    }

    // v8.6.2 — Paste widget (zero-code rubric capstone).
    // Shows when validation has `rubric` (free-text LLM rubric) AND no GHA/endpoint
    // primitive is configured. Paste a markdown doc → grader LLM-scores it.
    const pasteWidget = container.querySelector('[data-role="paste-widget"]');
    const pastePromptEl = container.querySelector('[data-role="paste-prompt"]');
    const hasRubric = !!(data.rubric && String(data.rubric).trim());
    if (pasteWidget && hasRubric && !ghaCfg && !(data.endpoint_check && data.endpoint_check.url)) {
      pasteWidget.style.display = '';
      if (pastePromptEl) {
        pastePromptEl.textContent = data.paste_prompt || 'Paste your complete deliverable (markdown) below.';
      }
    }

    // Submit
    container.querySelector('[data-action="submit"]').addEventListener('click', async () => {
      if (!handlers.judgeFn) return;
      const phasesCompleted = Array.from(container.querySelectorAll('.tmpl-phase-item.done'))
        .map(el => el.dataset.phaseId);
      const checklistData = {};
      container.querySelectorAll('.tmpl-check-item').forEach(el => {
        checklistData[el.dataset.checkId] = el.classList.contains('done');
      });
      const deployUrlEl = container.querySelector('[data-role="deploy-url"]');
      const runUrlEl = container.querySelector('[data-role="gha-run-url"]');
      const pasteEl = container.querySelector('[data-role="paste-markdown"]');
      const submission = {
        phases_completed: phasesCompleted,
        checklist: checklistData,
      };
      if (deployUrlEl && deployUrlEl.value.trim()) submission.endpoint_url = deployUrlEl.value.trim();
      if (runUrlEl && runUrlEl.value.trim()) submission.workflow_run_url = runUrlEl.value.trim();
      if (pasteEl && pasteEl.value.trim()) submission.paste_markdown = pasteEl.value.trim();
      const res = await handlers.judgeFn(submission);
      renderFeedback(container, res);
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

  global.SllTemplateProject = { mount };
})(window);
