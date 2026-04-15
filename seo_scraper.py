"""
seo_scraper.py
==============
从权威 SEO 博客抓取 Ahrefs / Backlinks 新手教程，调用 Claude API 翻译为中文。

依赖：
    pip install requests feedparser beautifulsoup4
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

_TRANSLATE_PROMPT = (
    "请将以下 SEO 英文教程翻译成中文，保持专业术语准确，"
    "语言通俗易懂，适合 SEO 新手阅读。直接输出译文，不要解释。\n\n"
)

_SUMMARIZE_PROMPT = (
    "请用中文写一段100字以内的摘要，概括以下 SEO 英文文章的核心要点，"
    "适合新手快速了解文章内容。直接输出摘要，不要解释。\n\n"
)


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
                    # 去掉 HTML 标签
                    summary = re.sub(r"<[^>]+>", "", entry.summary or "").strip()
                    summary = re.sub(r"\s+", " ", summary)[:500]

                articles.append({
                    "title":          entry.get("title", "").strip(),
                    "url":            entry.get("link", ""),
                    "summary":        summary,
                    "source_name":    name,
                    "published_date": pub_date,
                    "read":           False,
                    "translated":     False,
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

def fetch_article_content(url: str, session: requests.Session) -> str:
    """
    抓取文章正文。优先提取 <article> 标签内容，去掉导航/广告/脚本。
    返回纯文本，失败返回空字符串。
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("请先安装 beautifulsoup4：pip install beautifulsoup4")
        return ""

    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
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
        logger.warning(f"抓取正文失败 {url}: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════
#  Claude API 翻译 / 摘要
# ═══════════════════════════════════════════════════════════════════

def _call_claude(text: str, system_prompt: str, api_key: str,
                 max_tokens: int = 2000) -> str:
    """调用 Claude API，返回结果文本，失败返回空字符串。"""
    if not api_key or not text.strip():
        return ""
    headers = {
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    payload = {
        "model":      _CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "messages": [{
            "role":    "user",
            "content": system_prompt + text,
        }],
    }
    try:
        resp = requests.post(_CLAUDE_API_URL, headers=headers,
                             json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.warning(f"Claude API 调用失败: {e}")
        return ""


def translate_article(article: Dict[str, Any], api_key: str,
                      session: requests.Session) -> Dict[str, Any]:
    """
    为文章补充中文摘要和中文翻译。
    - zh_summary：对 RSS summary 做摘要（快，用于列表展示）
    - zh_content：对抓取到的正文做全文翻译（慢，用于深度阅读）
    """
    logger.info(f"  [翻译] {article['title'][:50]}...")

    # 中文摘要（基于 RSS summary，无需额外抓取）
    if article["summary"] and not article["zh_summary"]:
        article["zh_summary"] = _call_claude(
            article["summary"], _SUMMARIZE_PROMPT, api_key, max_tokens=300
        )

    # 全文翻译（抓取正文后翻译）
    if not article["zh_content"]:
        content = fetch_article_content(article["url"], session)
        if content:
            article["zh_content"] = _call_claude(
                content, _TRANSLATE_PROMPT, api_key, max_tokens=3000
            )

    article["translated"] = bool(article["zh_summary"] or article["zh_content"])
    return article


# ═══════════════════════════════════════════════════════════════════
#  保存文章
# ═══════════════════════════════════════════════════════════════════

def save_article(article: Dict[str, Any], output_dir: str) -> str:
    """
    保存文章为中英对照 txt 文件，返回文件路径。
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 清理文件名中的非法字符
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", article["title"])[:60]
    date_str   = article.get("published_date", datetime.now().strftime("%Y-%m-%d"))
    filename   = f"{date_str}_{safe_title}.txt"
    filepath   = os.path.join(output_dir, filename)

    lines = [
        f"标题：{article['title']}",
        f"Title: {article['title']}",
        f"来源 / Source：{article['source_name']}",
        f"原文 / URL：{article['url']}",
        f"日期 / Date：{date_str}",
        "─" * 50,
        "",
    ]

    if article.get("zh_summary"):
        lines += ["【中文摘要】", article["zh_summary"], ""]

    if article.get("summary"):
        lines += ["【English Summary】", article["summary"], ""]

    if article.get("zh_content"):
        lines += ["【中文全文翻译】", article["zh_content"], ""]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"  已保存: {filename}")
        return filepath
    except Exception as e:
        logger.warning(f"保存失败: {e}")
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
