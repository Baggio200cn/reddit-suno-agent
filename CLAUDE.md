# CLAUDE.md — Python Agent Engineering Standards

This file is read by Claude Code at the start of every session. Apply these principles to
all code written in this repository.

---

## 1. Error Paths Are Main Paths

Every external call (HTTP, file I/O, subprocess) has three layers:

```
Layer 1 – Retry once with back-off (transient failures)
Layer 2 – Fallback to degraded behavior (partial result still useful)
Layer 3 – Record failure in structured log, skip gracefully (never crash the agent)
```

**Concrete pattern:**

```python
def _fetch_with_retry(url: str, session, retries: int = 2) -> Optional[str]:
    for attempt in range(retries + 1):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(2 ** attempt)   # 1s, 2s back-off
                continue
            logger.warning("fetch_failed url=%s error=%s", url, e)
            return None
```

**Never:**
- Catch `Exception` and silently return empty string without logging
- Retry in a `while True` loop without a maximum
- Let one failed article/post abort the entire batch

---

## 2. Context as Working Memory

Long-running agents accumulate context. Keep it lean:

- **Token budget**: Truncate article content at 8 000 chars before sending to Claude.
  Summaries cap at 500 chars.
- **Per-run state object**: Pass a single `RunState` dataclass (or plain dict) through the
  pipeline instead of scattered globals.
- **Checkpoint after each unit**: After processing each post/article, write state to disk.
  The agent must be safely re-startable mid-run.

---

## 3. Independent Verification

After every Claude API call, verify the output before using it:

```python
def _verify_translation(zh_text: str, source_en: str) -> bool:
    """Return True only if translation looks valid."""
    if not zh_text or len(zh_text) < 20:
        return False
    # Must contain at least some CJK characters
    cjk_count = sum(1 for c in zh_text if '\u4e00' <= c <= '\u9fff')
    if cjk_count < 10:
        return False
    # Output shouldn't be dramatically shorter than input (< 10% of source)
    if len(zh_text) < len(source_en) * 0.10:
        return False
    return True
```

If verification fails: retry once with a clearer prompt. If still failing: log and skip.
Never store a failed translation as if it were valid.

---

## 4. Prompt as Control Plane

Prompts are code. Treat them with the same care:

- Define prompts as **module-level constants** (not inline strings)
- Use `{placeholders}` with `.format()` — never f-strings with user content
- Keep a `max_tokens` budget comment next to every prompt constant
- When changing a prompt, update the constant — not the call site

```python
# max_tokens=300  (summary — short)
_SUMMARIZE_PROMPT = (
    "请用中文写一段100字以内的摘要，概括以下 SEO 英文文章的核心要点，"
    "适合新手快速了解文章内容。直接输出摘要，不要解释。\n\n{text}"
)

# max_tokens=3000  (full translation)
_TRANSLATE_PROMPT = (
    "请将以下 SEO 英文教程翻译成中文，保持专业术语准确，"
    "语言通俗易懂，适合 SEO 新手阅读。直接输出译文，不要解释。\n\n{text}"
)
```

---

## 5. Structured Logging

Every log message must be machine-parseable:

```python
# Good — key=value pairs
logger.info("article_processed title=%r status=%s tokens=%d", title, status, tokens)

# Bad — natural language prose
logger.info(f"已处理文章：{title}")
```

Log levels:
- `DEBUG` — per-field detail inside a processing step
- `INFO`  — one line per article/post (processed, skipped, saved)
- `WARNING` — recoverable failures (API error, parse failure)
- `ERROR`  — batch-level failures (RSS source unreachable, disk full)

---

## 6. Configuration Contract

Every script that accepts a config dict must document its keys at the top:

```python
# Required keys:  claude_api_key, output_dir
# Optional keys:  proxy (default ""), limit_min (default 5), limit_max (default 8)
# Never mutate:   sources, keywords (treat as read-only within a run)
```

Never read `os.environ` directly in business logic. Pass config explicitly.

---

## 7. File I/O Safety

- Always use `Path` objects, never bare `os.path.join`
- Write to a temp file first, then rename atomically:

```python
tmp = Path(filepath).with_suffix(".tmp")
tmp.write_text(content, encoding="utf-8")
tmp.replace(filepath)   # atomic on POSIX
```

- On Windows `Path.replace()` raises if destination exists — wrap with try/except and
  fall back to `os.replace()`.

---

## 8. GUI Threading Rule

All tkinter state must be accessed from the main thread only.
Worker threads communicate via `queue.Queue` and `root.after(100, poll_queue)`.

```python
# Worker thread
result_q.put({"status": "done", "count": n})

# Main thread (polled)
def _poll(self):
    while not self.result_q.empty():
        msg = self.result_q.get_nowait()
        self._handle_result(msg)
    self.root.after(100, self._poll)
```

Never call `label.config()` or `listbox.insert()` from a worker thread.

---

## 9. Secrets Management

- API keys live only in `agent_config.json` (gitignored) or environment variables
- Log the first 8 chars + `...` for debugging, never the full key
- Validate key format before use: `if not api_key.startswith("sk-ant-"): raise ValueError`

---

## 10. Commit Hygiene

Each commit should be atomic and self-describing:

```
feat(seo): add layered error recovery to translate_article()
fix(scraper): add _VISION_PROMPT constant to resolve NameError
refactor(desktop): replace limit with limit_min/limit_max for random daily count
```

Never commit: API keys, `agent_config.json`, `__pycache__/`, `*.pyc`, output files.
