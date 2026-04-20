# Python Agent Development Checklist

Use this before every PR. Tick each box or add a reason it does not apply.

---

## Before Writing Code

- [ ] Read the relevant existing files first (never modify unseen code)
- [ ] Identify all external calls (HTTP, file, subprocess, Claude API)
- [ ] Define config contract: which keys are required vs optional?
- [ ] Define module-level prompt constants with `max_tokens` comments

---

## Error Handling

- [ ] Every external call has retry logic (at least 1 retry with back-off)
- [ ] Every external call has a fallback (degraded output > no output)
- [ ] Failures are logged with `key=value` pairs, not free-form prose
- [ ] No bare `except Exception: pass` or silent empty-string returns
- [ ] Batch loops never abort on a single item failure

---

## Claude API Usage

- [ ] `api_key` validated (`startswith("sk-ant-")`) before first call
- [ ] `max_tokens` explicitly set on every API call
- [ ] Output verified after every call (length check + CJK char check for Chinese)
- [ ] Translation retry: one re-attempt with clearer prompt if verification fails
- [ ] Token budget: input truncated to ≤ 8 000 chars; summary capped at 500 chars

---

## State and Persistence

- [ ] History/state saved after each processed item (not just at the end)
- [ ] Agent can be safely restarted mid-run without duplicate work
- [ ] Output files written atomically (tmp → rename)
- [ ] No output files tracked by git (gitignore covers output dirs)

---

## GUI (tkinter)

- [ ] All UI updates run on main thread only
- [ ] Worker threads communicate via `queue.Queue` + `root.after()` polling
- [ ] Long operations (scrape, translate) run in daemon threads
- [ ] Progress is shown during work (spinner, count, log messages)
- [ ] Settings saved to `agent_config.json` on every change

---

## Security

- [ ] API keys never appear in logs (show first 8 chars + `...` only)
- [ ] `agent_config.json` is gitignored
- [ ] No user-supplied strings interpolated into shell commands
- [ ] No hardcoded credentials anywhere in source

---

## Code Quality

- [ ] Each function has one responsibility (≤ 40 lines as soft limit)
- [ ] No speculative abstractions — only what the current task needs
- [ ] Module-level constants, not magic literals
- [ ] Imports grouped: stdlib → third-party → local, no star imports

---

## Git

- [ ] Branch matches the assigned feature branch
- [ ] Commit message follows `type(scope): description` format
- [ ] No `agent_config.json`, `*.pyc`, `__pycache__/`, or output files committed
- [ ] Each commit is atomic (one logical change)

---

## Testing / Verification

- [ ] Ran the modified script manually and observed expected log output
- [ ] Edge cases tested: empty API key, no articles match filter, network timeout
- [ ] GUI: launched app, clicked every new button, no uncaught exceptions
- [ ] Re-ran after a restart to verify state persistence works correctly
