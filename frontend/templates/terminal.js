/**
 * terminal_exercise template — BYO-execution (learner runs on their own
 * machine, pastes output for grading).
 *
 * Data contract (v8.6.1):
 *   mount(container, data, handlers)
 *     data = {
 *       exercise_type: "terminal_exercise",
 *       title, briefing,
 *       instructions: string (HTML allowed),
 *       byo_key_notice: bool,
 *       hint?: string,
 *       asciinema_url?: string,
 *
 *       // SWITCHING-UX (v8.6.1 2026-04-24):
 *       bootstrap_command?: string,     // copy-to-terminal one-liner
 *       step_slug?: string,             // e.g. "M3.S2" — rendered in banner
 *       step_task?: string,             // e.g. "Add /health endpoint"
 *       dashboard_deeplink?: string,    // URL back to this step
 *       dependencies?: [{kind, label?, why?, install_hint?}],
 *       paste_slots?: [{id, label, hint?, placeholder?}],
 *     }
 *     handlers = { judgeFn({paste}), ... }
 *       — or when paste_slots present: judgeFn({pastes: {slot_id: text}})
 *
 * SECURITY: this template NEVER captures/stores/transmits any API key.
 * The BYO-key panel is informational only. Do not add key input.
 */
(function (global) {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // v8.6.1 — wraps the LLM-authored bootstrap with a step-aware banner +
  // shell-prompt indicator so the learner's terminal shows [SLL:M3.S2] as
  // they work. Idempotent: if the bootstrap already contains echo-banner
  // output, we don't re-wrap.
  function buildBootstrap(data) {
    const raw = (data.bootstrap_command || '').trim();
    if (!raw) return '';
    if (raw.indexOf('__SLL_BANNER__') !== -1) return raw;  // pre-wrapped
    const slug = data.step_slug || '';
    const task = data.step_task || '';
    const link = data.dashboard_deeplink || '';
    const banner = [
      '╭─────────────────────────────────────────────────────────╮',
      slug ? `│  Skills Lab — ${slug}`.padEnd(60) + '│' : '',
      task ? `│  Task: ${task.slice(0, 50)}`.padEnd(60) + '│' : '',
      link ? `│  Back to dashboard: ${link.slice(0, 35)}`.padEnd(60) + '│' : '',
      '╰─────────────────────────────────────────────────────────╯',
    ].filter(Boolean).join('\n');
    // Shell prompt indicator — survives for this shell session only (no .rc touch).
    const promptTag = slug ? `\nexport PS1="[SLL:${slug}] $PS1" # revert by closing the tab` : '';
    // Escape single quotes inside the banner for the echo
    const echoSafe = banner.replace(/'/g, "'\\''");
    return `${raw} && echo '__SLL_BANNER__${echoSafe}'${promptTag}`;
  }

  function renderDeps(list, deps) {
    list.innerHTML = '';
    const humanLabel = {
      anthropic_api_key: 'Anthropic API key (get one at console.anthropic.com)',
      claude_cli: 'Claude Code installed (`brew install anthropic-ai/claude/claude`)',
      claude_code: 'Claude Code installed (`brew install anthropic-ai/claude/claude`)',
      docker: 'Docker running locally',
      git: 'git',
      git_clone: 'Local clone of the course starter repo',
      python: 'Python 3.11+',
      nodejs: 'Node.js 20+',
      node: 'Node.js 20+',
      github_account: 'GitHub account + ability to push to a public fork',
      github_pat: 'GitHub Personal Access Token (read-only Actions scope)',
    };
    (deps || []).forEach(raw => {
      // Coerce string entries to {kind} objects (Creator sometimes emits
      // a flat string[] instead of [{kind, label, why}])
      const d = (typeof raw === 'string') ? { kind: raw } : (raw || {});
      const li = document.createElement('li');
      li.className = 'tmpl-dep-item';
      const name = d.label || humanLabel[d.kind] || (d.kind ? d.kind.replace(/_/g, ' ') : 'Requirement');
      const extra = [];
      if (d.version) extra.push(d.version);
      if (d.why) extra.push(d.why);
      if (d.install_hint) extra.push(`hint: ${d.install_hint}`);
      li.innerHTML = `<span class="tmpl-dep-marker">▸</span> <strong>${esc(name)}</strong>` +
        (extra.length ? ` <span class="tmpl-dep-extra">— ${esc(extra.join(' · '))}</span>` : '');
      list.appendChild(li);
    });
  }

  function renderPasteSlots(container, slots) {
    container.innerHTML = '';
    slots.forEach((slot, idx) => {
      const block = document.createElement('div');
      block.className = 'tmpl-paste-block';
      block.innerHTML = `
        <div class="tmpl-paste-header">
          <span>${esc(slot.label || 'Paste')}${slot.hint ? ` <span class="tmpl-slot-hint">— ${esc(slot.hint)}</span>` : ''}</span>
          <span class="tmpl-paste-count" data-role="slot-count-${idx}">0 chars</span>
        </div>
        <textarea class="tmpl-paste" data-role="slot-${slot.id}" spellcheck="false"
                  autocomplete="off" autocorrect="off" autocapitalize="off"
                  placeholder="${esc(slot.placeholder || '')}"></textarea>`;
      container.appendChild(block);
      const ta = block.querySelector('textarea');
      const cnt = block.querySelector(`[data-role="slot-count-${idx}"]`);
      ta.addEventListener('input', () => { cnt.textContent = ta.value.length + ' chars'; });
    });
  }

  function mount(container, data, handlersOrJudgeFn) {
    const judgeFn = (typeof handlersOrJudgeFn === 'function')
      ? handlersOrJudgeFn
      : (handlersOrJudgeFn && handlersOrJudgeFn.judgeFn) || (() => Promise.resolve({score: 0, feedback: 'No judge.'}));

    // Briefing
    const briefEl = container.querySelector('[data-slot="briefing"]');
    if (briefEl) briefEl.innerHTML = data.briefing || '';

    // v8.6.1 — Bootstrap block
    const bootstrap = buildBootstrap(data);
    if (bootstrap) {
      const root = container.querySelector('[data-role="bootstrap"]');
      const codeEl = container.querySelector('[data-role="bootstrap-code"]');
      if (root && codeEl) {
        codeEl.textContent = bootstrap;
        root.style.display = '';
        const copyBtn = container.querySelector('[data-action="copy-bootstrap"]');
        if (copyBtn) {
          copyBtn.addEventListener('click', async () => {
            try {
              await navigator.clipboard.writeText(bootstrap);
              const orig = copyBtn.textContent;
              copyBtn.textContent = '✓ Copied';
              setTimeout(() => { copyBtn.textContent = orig; }, 1500);
            } catch (_) {
              // Fallback — select text
              const range = document.createRange();
              range.selectNode(codeEl);
              window.getSelection().removeAllRanges();
              window.getSelection().addRange(range);
              copyBtn.textContent = 'Press ⌘C';
            }
          });
        }
      }
    }

    // v8.6.1 — Dependencies panel
    if (Array.isArray(data.dependencies) && data.dependencies.length) {
      const depsRoot = container.querySelector('[data-role="deps"]');
      const depsList = container.querySelector('[data-role="deps-list"]');
      if (depsRoot && depsList) {
        renderDeps(depsList, data.dependencies);
        depsRoot.style.display = '';
      }
    }

    // BYO-key info panel
    if (data.byo_key_notice) {
      const info = container.querySelector('[data-role="byo-info"]');
      if (info) info.style.display = '';
    }

    // Instructions
    const instrEl = container.querySelector('[data-slot="instructions"]');
    if (instrEl) instrEl.innerHTML = data.instructions || '';

    // v8.6.1 — Paste area: single textarea OR structured slots
    const singleBlock = container.querySelector('[data-role="paste-single-block"]');
    const slotsContainer = container.querySelector('[data-role="paste-slots-container"]');
    const useSlots = Array.isArray(data.paste_slots) && data.paste_slots.length > 0;
    let paste = null, pasteCountEl = null;
    if (useSlots) {
      if (singleBlock) singleBlock.style.display = 'none';
      if (slotsContainer) {
        slotsContainer.style.display = '';
        renderPasteSlots(slotsContainer, data.paste_slots);
      }
    } else {
      paste = container.querySelector('[data-role="paste"]');
      pasteCountEl = container.querySelector('[data-role="paste-count"]');
      const updateCount = () => { if (pasteCountEl) pasteCountEl.textContent = (paste.value || '').length + ' chars'; };
      paste.addEventListener('input', updateCount);
      updateCount();
    }

    // Submit handler — mode-aware
    const submitBtn = container.querySelector('[data-action="submit"]');
    submitBtn.addEventListener('click', async () => {
      let payload;
      if (useSlots) {
        const pastes = {};
        let totalLen = 0;
        data.paste_slots.forEach(s => {
          const ta = container.querySelector(`[data-role="slot-${s.id}"]`);
          const v = (ta && ta.value || '').trim();
          pastes[s.id] = v;
          totalLen += v.length;
        });
        if (totalLen === 0) {
          renderFeedback(container, { score: 0, feedback: 'Please fill at least one paste slot before submitting.' });
          return;
        }
        payload = { pastes, paste: Object.values(pastes).join('\n\n---\n\n') };
      } else {
        const value = (paste.value || '').trim();
        if (!value) {
          renderFeedback(container, { score: 0, feedback: 'Paste your terminal output first.' });
          return;
        }
        payload = { paste: value };
      }

      submitBtn.disabled = true;
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Grading…';
      const f = container.querySelector('[data-role="feedback"]');
      if (f) {
        f.className = 'tmpl-feedback pending';
        f.innerHTML = '<em style="color:var(--text-secondary, #9097aa);">Reading your paste…</em>';
      }
      try {
        const res = await judgeFn(payload);
        renderFeedback(container, res);
      } catch (e) {
        renderFeedback(container, { score: 0, feedback: 'Network error: ' + (e.message || e) });
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });

    // Reset — clear all paste fields
    container.querySelector('[data-action="reset"]').addEventListener('click', () => {
      if (useSlots) {
        container.querySelectorAll('[data-role^="slot-"]').forEach(el => {
          if (el.tagName === 'TEXTAREA') { el.value = ''; el.dispatchEvent(new Event('input')); }
        });
      } else {
        paste.value = '';
        if (pasteCountEl) pasteCountEl.textContent = '0 chars';
        paste.focus();
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
  }

  function renderFeedback(container, res) {
    const f = container.querySelector('[data-role="feedback"]');
    if (!f) return;
    f.className = 'tmpl-feedback';
    const score = res.score || 0;
    if (res.correct || score >= 0.95) f.classList.add('pass');
    else if (score >= 0.5) f.classList.add('partial');
    else f.classList.add('fail');
    f.innerHTML = `<strong>Score: ${Math.round(score * 100)}%</strong><br>${esc(res.feedback || '')}`;
  }

  global.SllTemplateTerminal = { mount };
})(window);
