"""
seo_scraper.py
==============
从权威 SEO 博客抓取 Ahrefs / Backlinks 新手教程，调用 Claude API 翻译为中文。

依赖：
    pip install requests feedparser beautifulsoup4

工程规范（参见 CLAUDE.md）：
  - 所有外部调用采用三层错误处理：重试 → 降级 → 跳过并记录
  - Claude API 输出必须通过质量验证后才写入文章
  - 每篇文章有明确状态：pending / translating / done / failed
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  RSS 数据源
# ─────────────────────────────────────────────
RSS_SOURCES: List[Dict[str, str]] = [
    {"name": "Ahrefs Blog",           "url": "https://ahrefs.com/blog/feed/"},
    {"name": "Backlinko",             "url": "https://backlinko.com/feed"},
    {"name": "Moz Blog",              "url": "https://moz.com/feeds/blog.rss"},
    {"name": "Neil Patel",            "url": "https://neilpatel.com/blog/feed/"},
    {"name": "Search Engine Journal", "url": "https://www.searchenginejournal.com/feed/"},
    {"name": "Search Engine Land",    "url": "https://searchengineland.com/feed"},
]

# ─────────────────────────────────────────────
#  关键词过滤（新手教程相关）
# ─────────────────────────────────────────────
LEARN_KEYWORDS: List[str] = [
    "beginner", "guide", "how to", "tutorial", "introduction",
    "basics", "step by step", "getting started", "for beginners",
    "ahrefs", "backlink", "link building", "domain authority",
    "anchor text", "outreach", "guest post", "seo",
    "off-page", "dofollow", "nofollow", "link profile", "serp",
]

# ─────────────────────────────────────────────
#  Claude API
# ─────────────────────────────────────────────
_CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
_CLAUDE_MODEL   = "claude-haiku-4-5-20251001"

# max_tokens=3000  (full translation)
_TRANSLATE_PROMPT = (
    "请将以下 SEO 英文教程翻译成中文，保持专业术语准确，"
    "语言通俗易懂，适合 SEO 新手阅读。直接输出译文，不要解释。\n\n{text}"
)

# max_tokens=300  (summary — short)
_SUMMARIZE_PROMPT = (
    "请用中文写一段100字以内的摘要，概括以下 SEO 英文文章的核心要点，"
    "适合新手快速了解文章内容。直接输出摘要，不要解释。\n\n{text}"
)

# ── 文章状态常量 ──────────────────────────────────────
STATUS_PENDING     = "pending"
STATUS_TRANSLATING = "translating"
STATUS_DONE        = "done"
STATUS_FAILED      = "failed"


# ═══════════════════════════════════════════════════════════════════
#  HTTP 会话
# ═══════════════════════════════════════════════════════════════════

def _make_session(proxy: str = "") -> requests.Session:
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    })
    if proxy:
        sess.proxies.update({"http": proxy, "https": proxy})
    return sess


# ═══════════════════════════════════════════════════════════════════
#  RSS 抓取
# ═══════════════════════════════════════════════════════════════════

def fetch_rss_articles(sources: List[Dict[str, str]],
                       proxy: str = "") -> List[Dict[str, Any]]:
    """
    读取所有 RSS 源，返回文章列表。
    每条文章包含：title, url, summary, source_name, published_date
    """
    try:
        import feedparser
    except ImportError:
        logger.error("请先安装 feedparser：pip install feedparser")
        return []

    session = _make_session(proxy)
    articles: List[Dict[str, Any]] = []

    for src in sources:
        name = src["name"]
        url  = src["url"]
        logger.info(f"  正在读取 RSS: {name}...")
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                pub_date = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6]).strftime("%Y-%m-%d")

                summary = ""
                if hasattr(entry, "summary"):
                    summary = re.sub(r"<[^>]+>", "", entry.summary or "").strip()
                    summary = re.sub(r"\s+", " ", summary)[:500]

                # 优先使用 RSS 全文（entry.content），避免二次抓取网页
                rss_full = ""
                if hasattr(entry, "content") and entry.content:
                    raw_html = entry.content[0].get("value", "")
                    rss_full = re.sub(r"<[^>]+>", "", raw_html).strip()
                    rss_full = re.sub(r"\s+", " ", rss_full)[:8000]
                    rss_full = re.sub(r"&#\d+;|&\w+;", " ", rss_full)  # 清理 HTML 实体

                articles.append({
                    "title":          entry.get("title", "").strip(),
                    "url":            entry.get("link", ""),
                    "summary":        summary,
                    "rss_full":       rss_full,   # RSS 全文（可能为空）
                    "source_name":    name,
                    "published_date": pub_date,
                    "read":           False,
                    "translated":     False,
                    "status":         STATUS_PENDING,
                    "zh_summary":     "",
                    "zh_content":     "",
                })
        except Exception as e:
            logger.warning(f"  读取 {name} RSS 失败: {e}")

    logger.info(f"RSS 共获取 {len(articles)} 篇文章")
    return articles


# ═══════════════════════════════════════════════════════════════════
#  关键词过滤
# ═══════════════════════════════════════════════════════════════════

def filter_articles(articles: List[Dict[str, Any]],
                    keywords: List[str]) -> List[Dict[str, Any]]:
    """只保留标题或摘要含关键词的文章。"""
    if not keywords:
        return articles
    kws = [k.lower() for k in keywords]
    result = []
    for art in articles:
        text = (art["title"] + " " + art["summary"]).lower()
        if any(kw in text for kw in kws):
            result.append(art)
    logger.info(f"关键词过滤后剩余 {len(result)} 篇")
    return result


# ═══════════════════════════════════════════════════════════════════
#  文章正文抓取
# ═══════════════════════════════════════════════════════════════════

def fetch_article_content(url: str, session: requests.Session,
                          retries: int = 1) -> str:
    """
    抓取文章正文。优先提取 <article> 标签内容，去掉导航/广告/脚本。
    返回纯文本，失败返回空字符串。
    第一层：重试一次（指数退避）；第二层：返回空字符串（调用方降级为仅摘要翻译）。
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("请先安装 beautifulsoup4：pip install beautifulsoup4")
        return ""

    for attempt in range(retries + 1):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            logger.warning("fetch_content_failed url=%s error=%s", url, e)
            return ""

    try:
        soup = BeautifulSoup(resp.text, "html.parser")

        # 移除无用标签
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "noscript", "iframe"]):
            tag.decompose()

        # 优先找 <article>，其次找常见正文 class
        content_el = (
            soup.find("article") or
            soup.find(class_=re.compile(r"(post|entry|content|article)[-_]?(body|content|text)?", re.I)) or
            soup.find("main") or
            soup.body
        )

        if not content_el:
            return ""

        # 提取文本，过滤空行
        lines = []
        for el in content_el.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
            text = el.get_text(separator=" ").strip()
            if len(text) > 30:   # 过滤太短的片段
                lines.append(text)

        content = "\n\n".join(lines)
        # 限制长度（避免 Claude 超 token）
        return content[:8000]

    except Exception as e:
        logger.warning("fetch_content_parse_failed url=%s error=%s", url, e)
        return ""


# ═══════════════════════════════════════════════════════════════════
#  Claude API 翻译 / 摘要
# ═══════════════════════════════════════════════════════════════════

def _verify_chinese_output(text: str, source: str = "") -> bool:
    """
    验证 Claude 输出是否为有效中文译文。
    规则：
      1. 非空且长度 ≥ 20 字符
      2. 包含至少 10 个 CJK 汉字
      3. 长度不低于原文的 10%（避免截断/拒绝回答）
    """
    if not text or len(text) < 20:
        return False
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if cjk_count < 10:
        return False
    if source and len(text) < len(source) * 0.10:
        return False
    return True


def _call_claude(text: str, prompt_template: str, api_key: str,
                 max_tokens: int = 2000, retries: int = 1) -> str:
    """
    调用 Claude API，返回结果文本。
    - 失败自动重试 retries 次（指数退避）
    - 验证输出质量；如不合格则重试一次（更简短的 prompt）
    - 最终失败返回空字符串并记录日志
    """
    if not api_key or not text.strip():
        return ""
    headers = {
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    def _post(prompt: str) -> str:
        payload = {
            "model":      _CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(_CLAUDE_API_URL, headers=headers,
                             json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()

    # ── 第一层：重试（网络/限速错误）──────────────────
    for attempt in range(retries + 1):
        try:
            prompt = prompt_template.format(text=text)
            result = _post(prompt)
            # ── 第二层：质量验证 ───────────────────────
            if _verify_chinese_output(result, source=text):
                return result
            # 质量不合格：用更简洁的 prompt 重试一次
            logger.warning(
                "claude_output_quality_fail attempt=%d len=%d cjk=%d",
                attempt, len(result),
                sum(1 for c in result if '\u4e00' <= c <= '\u9fff'),
            )
            if attempt == 0:
                # 重试时换更简单的 prompt
                simple_prompt = "请用中文翻译以下内容，直接输出译文：\n\n" + text[:4000]
                result2 = _post(simple_prompt)
                if _verify_chinese_output(result2, source=text):
                    return result2
            break  # 质量两次都不合格，放弃
        except Exception as e:
            if attempt < retries:
                wait = 2 ** attempt
                logger.warning(
                    "claude_api_error attempt=%d wait=%ds error=%s",
                    attempt, wait, e,
                )
                time.sleep(wait)
            else:
                logger.warning("claude_api_failed error=%s", e)

    return ""


def translate_article(article: Dict[str, Any], api_key: str,
                      session: requests.Session) -> Dict[str, Any]:
    """
    为文章补充中文摘要和中文翻译。
    - zh_summary：对 RSS summary 做摘要（快，用于列表展示）
    - zh_content：对抓取到的正文做全文翻译（慢，用于深度阅读）
    - status 字段追踪进度：pending → translating → done / failed
    """
    article["status"] = STATUS_TRANSLATING
    logger.info("translate_start title=%r", article["title"][:50])

    # ── 中文摘要（基于 RSS summary，无需额外抓取）────────
    if article.get("summary") and not article.get("zh_summary"):
        zh = _call_claude(
            article["summary"][:500],
            _SUMMARIZE_PROMPT,
            api_key,
            max_tokens=300,
        )
        if zh:
            article["zh_summary"] = zh
        else:
            logger.warning(
                "summary_translate_failed title=%r", article["title"][:50]
            )

    # ── 全文翻译：RSS全文 → 网页抓取 → 降级为仅摘要 ────────
    if not article.get("zh_content"):
        # 第一选择：RSS feed 自带全文（无需抓网页，最可靠）
        content = article.get("rss_full", "").strip()
        source  = "rss_full"

        # 第二选择：抓取网页正文
        if not content:
            logger.info("rss_full_empty url=%s — scraping web page", article["url"])
            content = fetch_article_content(article["url"], session)
            source  = "web_scrape"

        if content:
            logger.info(
                "content_source=%s len=%d title=%r",
                source, len(content), article["title"][:40],
            )
            zh = _call_claude(
                content,
                _TRANSLATE_PROMPT,
                api_key,
                max_tokens=3000,
            )
            if zh:
                article["zh_content"] = zh
            else:
                logger.warning(
                    "content_translate_failed source=%s title=%r",
                    source, article["title"][:50],
                )
        else:
            logger.warning(
                "content_unavailable url=%s — summary only",
                article["url"],
            )

    ok = bool(article.get("zh_summary") or article.get("zh_content"))
    article["translated"] = ok
    article["status"]     = STATUS_DONE if ok else STATUS_FAILED
    logger.info(
        "translate_end title=%r status=%s zh_summary_len=%d zh_content_len=%d",
        article["title"][:50],
        article["status"],
        len(article.get("zh_summary") or ""),
        len(article.get("zh_content") or ""),
    )
    return article


# ═══════════════════════════════════════════════════════════════════
#  保存文章
# ═══════════════════════════════════════════════════════════════════

def save_article(article: Dict[str, Any], output_dir: str) -> str:
    """
    保存文章为中文 Markdown 笔记，返回文件路径。
    文件名：{日期}_{中文标题}.md
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    safe_title = re.sub(r'[\\/:*?"<>|]', "_", article["title"])[:60]
    date_str   = article.get("published_date", datetime.now().strftime("%Y-%m-%d"))
    filename   = f"{date_str}_{safe_title}.md"
    filepath   = out_path / filename

    parts: List[str] = []

    # ── 标题与元数据 ──────────────────────────────────
    zh_title = article.get("zh_summary", "").split("。")[0][:30] if article.get("zh_summary") else ""
    parts.append(f"# {article['title']}")
    parts.append("")
    parts.append(f"| 字段 | 内容 |")
    parts.append(f"|------|------|")
    parts.append(f"| 来源 | {article.get('source_name', '')} |")
    parts.append(f"| 日期 | {date_str} |")
    parts.append(f"| 原文 | [{article['title']}]({article.get('url', '')}) |")
    parts.append("")

    # ── 中文摘要 ─────────────────────────────────────
    if article.get("zh_summary"):
        parts.append("## 中文摘要")
        parts.append("")
        parts.append(article["zh_summary"])
        parts.append("")

    # ── 中文全文翻译 ──────────────────────────────────
    if article.get("zh_content"):
        parts.append("## 中文全文翻译")
        parts.append("")
        parts.append(article["zh_content"])
        parts.append("")
    else:
        parts.append("> **提示**：暂无全文翻译。点击「翻译选中」获取完整中文内容。")
        parts.append("")

    # ── 英文摘要（参考）──────────────────────────────
    if article.get("summary"):
        parts.append("## English Summary（参考原文）")
        parts.append("")
        parts.append(article["summary"])
        parts.append("")

    content = "\n".join(parts)

    # 原子写入：先写 .tmp，再重命名
    tmp = filepath.with_suffix(".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        try:
            tmp.replace(filepath)
        except OSError:
            import os as _os
            _os.replace(str(tmp), str(filepath))
        logger.info("article_saved filename=%s", filename)
        return str(filepath)
    except Exception as e:
        logger.warning("save_failed filename=%s error=%s", filename, e)
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        return ""


# ═══════════════════════════════════════════════════════════════════
#  阅读历史（已读 URL 集合）
# ═══════════════════════════════════════════════════════════════════

def load_read_history(base_dir: str) -> set:
    """加载已读文章 URL 集合。"""
    hist_file = Path(base_dir) / "seo_read_history.json"
    if not hist_file.exists():
        return set()
    try:
        with open(hist_file, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("urls", []))
    except Exception:
        return set()


def save_read_history(base_dir: str, read_urls: set):
    """保存已读 URL（最多保留 1000 条）。"""
    hist_file = Path(base_dir) / "seo_read_history.json"
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    urls_list = list(read_urls)[-1000:]
    try:
        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump({
                "urls":         urls_list,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"保存阅读历史失败: {e}")
