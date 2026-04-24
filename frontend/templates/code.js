/**
 * code template — handles code_exercise / code_read / code.
 *
 * mount(containerEl, data, handlers)
 *   data = { exercise_type, language, starter_code, problem_statement, title,
 *            hint?, starter_files?, starter_repo?, repo_path_var?, must_contain?[] }
 *   handlers = { executeFn(code, language, extras) => Promise<execResult>,
 *                judgeFn(submission)           => Promise<validateResult> }
 *
 * The template renders all the UI (editor, scaffold banners, Run/Submit
 * buttons, output panel, test-result panel, hint reveal) and calls back
 * into the caller's handlers for the actual HTTP I/O. No HTML comes from
 * the LLM — only data.
 */
(function (global) {
  'use strict';

  function esc(s) { return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  function mount(container, data, handlers) {
    handlers = handlers || {};
    const lang = (data.language || 'python').toLowerCase();
    // Populate slots. 2026-04-22 v6: title slot removed from template HTML
    // (outer .step-title renders it once). Guard kept for back-compat if the
    // HTML gets restored.
    const _titleEl = container.querySelector('[data-slot="title"]');
    if (_titleEl) _titleEl.textContent = data.title || '';
    const pbEl = container.querySelector('[data-slot="problem_statement"]');
    if (pbEl) pbEl.innerHTML = data.problem_statement || '';
    container.querySelector('[data-slot="lang-badge"]').textContent = lang;

    // F26 scaffold banners
    const cloneBanner = container.querySelector('[data-role="clone-banner"]');
    const filesBanner = container.querySelector('[data-role="files-banner"]');
    if (data.starter_repo && data.starter_repo.url) {
      cloneBanner.style.display = '';
      const link = cloneBanner.querySelector('[data-role="clone-url"]');
      link.textContent = data.starter_repo.url;
      link.href = data.starter_repo.url;
      const meta = cloneBanner.querySelector('[data-role="clone-meta"]');
      meta.textContent = data.starter_repo.ref ? `(ref: ${data.starter_repo.ref})` : '';
    }
    if (data.starter_files && data.starter_files.length) {
      filesBanner.style.display = '';
      filesBanner.querySelector('[data-role="files-count"]').textContent = data.starter_files.length;
      filesBanner.querySelector('[data-role="repo-path-var"]').textContent =
        data.repo_path_var || 'repo_path';
    }

    // Editor
    const editor = container.querySelector('[data-role="editor"]');
    editor.value = data.starter_code || '';
    // 2026-04-22: line-number gutter. Mirrors the textarea's line count and
    // scroll position. Re-renders on `input`, syncs scroll on `scroll`.
    const gutter = container.querySelector('[data-role="gutter"]');
    const renderGutter = () => {
      if (!gutter) return;
      const lines = Math.max(1, (editor.value || '').split('\n').length);
      // Only re-render if line count changed (avoid DOM churn on every keystroke).
      if (gutter.childElementCount !== lines) {
        let html = '';
        for (let i = 1; i <= lines; i++) html += '<div>' + i + '</div>';
        gutter.innerHTML = html;
      }
    };
    const syncGutterScroll = () => {
      if (gutter) gutter.scrollTop = editor.scrollTop;
    };
    // Auto-size
    const autoSize = () => { editor.style.height = 'auto'; editor.style.height = Math.max(320, editor.scrollHeight + 2) + 'px'; };
    editor.addEventListener('input', () => { autoSize(); renderGutter(); });
    editor.addEventListener('scroll', syncGutterScroll);
    setTimeout(() => { autoSize(); renderGutter(); }, 0);
    // Tab -> 4 spaces
    editor.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const s = editor.selectionStart, end = editor.selectionEnd;
        editor.value = editor.value.substring(0, s) + '    ' + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = s + 4;
        renderGutter();
      }
    });

    // Hint reveal
    const hintEl = container.querySelector('[data-action="reveal-hint"]');
    if (data.hint) {
      hintEl.addEventListener('click', () => {
        if (hintEl.classList.contains('revealed')) return;
        hintEl.textContent = data.hint;
        hintEl.classList.add('revealed');
      });
    } else {
      hintEl.style.display = 'none';
    }

    // Reset button
    container.querySelector('[data-action="reset-code"]').addEventListener('click', () => {
      if (confirm('Reset to starter code? Your changes will be lost.')) {
        editor.value = data.starter_code || '';
        autoSize();
      }
    });

    // Run button — runs code via executeFn, renders stdout/stderr.
    container.querySelector('[data-action="run"]').addEventListener('click', async () => {
      if (!handlers.executeFn) return;
      const out = container.querySelector('[data-role="output"]');
      const body = container.querySelector('[data-role="output-body"]');
      out.style.display = '';
      body.className = 'tmpl-output-body';
      body.textContent = 'Running…';
      const extras = {
        starter_files: data.starter_files,
        repo_path_var: data.repo_path_var,
        schema_setup: data.schema_setup,
        seed_rows: data.seed_rows,
      };
      try {
        const res = await handlers.executeFn(editor.value, lang, extras);
        const stdout = res.stdout || res.output || '';
        const stderr = res.stderr || res.error || '';
        if ((res.exit_code && res.exit_code !== 0) || (!stdout && stderr)) {
          body.classList.add('error');
          body.textContent = stderr || 'Code execution failed.';
        } else {
          body.textContent = stdout || '(no output)';
        }
      } catch (e) {
        body.classList.add('error');
        body.textContent = 'Network error running code: ' + (e.message || e);
      }
    });

    // Submit button — sends code to judgeFn; renders test panel if hidden_tests.
    container.querySelector('[data-action="submit"]').addEventListener('click', async () => {
      if (!handlers.judgeFn) return;
      const btn = container.querySelector('[data-action="submit"]');
      btn.disabled = true; btn.textContent = 'Grading…';
      try {
        const res = await handlers.judgeFn({ code: editor.value });
        renderFeedback(container, res);
        // Structured test results (when Docker runner returned them)
        const tr = res.test_results;
        if (tr && typeof tr.total === 'number' && tr.total > 0) {
          const panel = container.querySelector('[data-role="test-panel"]');
          const verdict = container.querySelector('[data-role="test-verdict"]');
          const count = container.querySelector('[data-role="test-count"]');
          const outp = container.querySelector('[data-role="test-output"]');
          panel.style.display = '';
          verdict.className = 'tmpl-test-verdict';
          if (tr.passed === tr.total && tr.failed === 0) {
            verdict.classList.add('pass'); verdict.textContent = '✓ All tests pass';
          } else if (tr.passed > 0) {
            verdict.classList.add('partial'); verdict.textContent = '◑ Partial pass';
          } else {
            verdict.classList.add('fail'); verdict.textContent = '✗ Tests failing';
          }
          count.textContent = `${tr.passed}/${tr.total} tests · ${tr.failed} failed`;
          outp.textContent = (res.feedback || '').slice(0, 2000);
        }
      } catch (e) {
        renderFeedback(container, { score: 0, feedback: 'Network error: ' + (e.message || e) });
      } finally {
        btn.disabled = false; btn.textContent = 'Submit';
      }
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

  global.SllTemplateCode = { mount };
})(window);
