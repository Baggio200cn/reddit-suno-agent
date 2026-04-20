"""
reddit_scraper.py
================
从 Reddit 抓取 r/ThinkingDeeplyAI 热门帖子，并下载配图到本地。

用法：
    python reddit_scraper.py

配置：直接修改下方 CONFIG 区域。

依赖：
    pip install requests
"""

import html
import json
import logging
import math
import random
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

# ─────────────────────────────────────────────
#  ★ 用户配置区（改这里）
# ─────────────────────────────────────────────
CONFIG = {
    # 多社区抓取
    "subreddits": [
        "AI_Agents",
        "AgentsOfAI",
        "ThinkingDeeplyAI",
        "TrueReddit",
        "ClaudeCode",
        "aiArt",       # AI 绘画作品（有图）
        "aivideo",     # AI 视频作品（有图）
    ],

    # 每日抓取数量范围
    "limit_min": 5,
    "limit_max": 8,

    # Reddit OAuth 凭据（可选，有则更稳定）
    "reddit_client_id":     "",
    "reddit_client_secret": "",

    # 代理（国内用户必须填）示例："http://127.0.0.1:7890"
    "proxy": "",

    # 图片保存目录
    "output_dir": "",

    # 每次请求间隔（秒）— 适当拉长可降低 503 概率
    "request_delay": 3.0,

    # AI 主题关键词过滤（留空列表则不过滤）
    "ai_keywords": [
        "llm", "large language model", "agent", "machine learning",
        "claude", "openai", "codex", "deepseek", "kimi", "veo", "gemini",
        "gpt", "diffusion", "transformer", "neural", "algorithm",
        "fine-tuning", "rag", "multimodal", "reasoning", "inference",
        "model", "ai", "artificial intelligence",
        "art", "teacher", "book", "education", "creative",
        # SEO / 外链
        "seo", "search engine optimization", "backlink", "link building",
        "external link", "outreach", "anchor text", "domain authority",
        "guest post", "dofollow", "nofollow", "serp", "organic traffic",
        "pagerank", "link profile", "off-page", "link juice",
    ],
}
# ─────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════
#  抓取策略定义
# ═══════════════════════════════════════════════════════════════════

STRATEGIES: Dict[str, dict] = {
    "trending": {
        # 趋势：近48小时高热度新帖（默认推荐）
        "api_mode": "hot",
        "weights": {"recency": 0.40, "score": 0.30, "comments": 0.20, "relevance": 0.10},
        "min_score": 10,
        "min_upvote_ratio": 0.65,
        "max_age_hours": 48,
    },
    "quality": {
        # 精品：高赞高讨论、一周内权威帖子
        "api_mode": "top",
        "weights": {"score": 0.40, "comments": 0.25, "recency": 0.20, "relevance": 0.15},
        "min_score": 100,
        "min_upvote_ratio": 0.80,
        "max_age_hours": 168,
    },
    "fresh": {
        # 新鲜：24小时内任意有讨论的新帖
        "api_mode": "new",
        "weights": {"recency": 0.60, "score": 0.20, "comments": 0.10, "relevance": 0.10},
        "min_score": 1,
        "min_upvote_ratio": 0.50,
        "max_age_hours": 24,
    },
    "hot": {
        # 热门：兼容旧版行为
        "api_mode": "hot",
        "weights": {"score": 0.50, "recency": 0.30, "comments": 0.20, "relevance": 0.00},
        "min_score": 5,
        "min_upvote_ratio": 0.60,
        "max_age_hours": 168,
    },
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_BASE_URL   = "https://www.reddit.com"
_OAUTH_URL  = "https://oauth.reddit.com"   # OAuth 认证后使用此域名
_TOKEN_URL  = "https://www.reddit.com/api/v1/access_token"
_USER_AGENT = "python:reddit-ai-scraper:v2.0 (by /u/anonymous)"

# RSS/HTML 图片提取常量
# preview.redd.it 是 Reddit 压缩版（≤640px，重编码），i.redd.it 才是原图
_REDDIT_CDN_RE = re.compile(
    r'https?://(?:preview|i|external-preview)\.redd\.it/([\w-]+)\.([a-zA-Z]{3,4})',
    re.IGNORECASE,
)
_IMG_NOISE = (
    "icon", "snoo", "emoji", "redditstatic.com",
    "styles.reddit", "redditmedia.com/t5", "thumbs.redd",
    "award_images",
)
_MAX_IMAGES_PER_POST = 6


def _upgrade_reddit_image_url(url: str) -> str:
    """把 Reddit 压缩预览 URL 升级到 i.redd.it 原图 URL。

    preview.redd.it/abc.jpg?width=640&format=pjpg  →  https://i.redd.it/abc.jpg
    external-preview.redd.it/xxx.jpg?...           →  https://i.redd.it/xxx.jpg
    非 Reddit 托管图片：保持原样返回。
    """
    if not url:
        return url
    match = _REDDIT_CDN_RE.search(url)
    if not match:
        return url
    media_id = match.group(1)
    ext = match.group(2).lower()
    if ext == "jpeg":
        ext = "jpg"
    return f"https://i.redd.it/{media_id}.{ext}"


def _extract_rss_image_urls(html_content: str,
                            max_images: int = _MAX_IMAGES_PER_POST
                            ) -> List[str]:
    """从 RSS HTML 片段提取去重后的高分辨率图片 URL。

    同时扫描 <img src=...> 和 <a href=...>（gallery 帖往往只有 href），
    对 preview.redd.it 自动升级为 i.redd.it 原图。
    """
    urls: List[str] = []
    seen: set = set()

    def _add(candidate: str) -> None:
        if not candidate or any(n in candidate for n in _IMG_NOISE):
            return
        upgraded = _upgrade_reddit_image_url(candidate)
        if upgraded not in seen:
            seen.add(upgraded)
            urls.append(upgraded)

    # 1) <img src="..."> 标签（RSS 通常嵌入 preview.redd.it 压缩图，会被升级）
    for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_content):
        if len(urls) >= max_images:
            break
        _add(src)

    # 2) <a href="..."> 指向 Reddit CDN 的链接（gallery 多图、纯链接帖）
    for href in re.findall(r'href=["\']([^"\']+)["\']', html_content):
        if len(urls) >= max_images:
            break
        if any(x in href for x in ("i.redd.it", "preview.redd.it",
                                    "external-preview.redd.it")):
            _add(href)

    return urls


# ═══════════════════════════════════════════════════════════════════
#  Reddit OAuth（Application-Only，无需用户登录）
# ═══════════════════════════════════════════════════════════════════

def _fetch_oauth_token(client_id: str, client_secret: str,
                       proxy: str = "") -> Optional[str]:
    """
    申请 Reddit Application-Only OAuth token。
    返回 access_token 字符串，失败返回 None。
    """
    if not client_id or not client_secret:
        return None
    proxies = {"http": proxy, "https": proxy} if proxy else {}
    try:
        resp = requests.post(
            _TOKEN_URL,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": _USER_AGENT},
            proxies=proxies,
            timeout=20,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if token:
            logger.info("reddit_oauth=ok token_prefix=%s...", token[:8])
        return token
    except Exception as e:
        logger.warning("reddit_oauth_failed error=%s", e)
        return None


# ═══════════════════════════════════════════════════════════════════
#  HTTP 会话
# ═══════════════════════════════════════════════════════════════════

def _make_session(proxy: str, oauth_token: str = "") -> requests.Session:
    """
    创建 requests.Session。
    - 有 oauth_token：使用 oauth.reddit.com + Bearer 认证（2023年后推荐）
    - 无 oauth_token：匿名请求 www.reddit.com（可能被 403）
    """
    sess = requests.Session()
    sess.headers.update({"User-Agent": _USER_AGENT})
    if oauth_token:
        sess.headers.update({"Authorization": f"Bearer {oauth_token}"})
        sess._reddit_base = _OAUTH_URL
        logger.info("session_mode=oauth base=%s", _OAUTH_URL)
    else:
        sess._reddit_base = _BASE_URL
        logger.warning("session_mode=anonymous — may be blocked by Reddit")
    if proxy:
        sess.proxies.update({"http": proxy, "https": proxy})
        logger.info("proxy=%s", proxy)
    return sess


# ═══════════════════════════════════════════════════════════════════
#  RSS 抓取（替代 JSON API，无需 OAuth）
# ═══════════════════════════════════════════════════════════════════

def _fetch_rss_posts(session: requests.Session, subreddit: str,
                     mode: str = "hot") -> List[Dict[str, Any]]:
    """
    通过 Reddit RSS Feed 抓取帖子列表。
    mode: hot / new / top  →  对应 /{mode}.rss
    返回与原 JSON API 兼容的帖子字典列表。
    """
    try:
        import feedparser
    except ImportError:
        logger.error("请安装 feedparser: pip install feedparser")
        return []

    url = f"https://www.reddit.com/r/{subreddit}/{mode}.rss"
    for attempt in range(2):   # 最多重试一次（处理 503）
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 0:
                logger.warning("rss_retry subreddit=%s attempt=1 error=%s", subreddit, e)
                time.sleep(4)
                continue
            logger.error("rss_fetch_failed subreddit=%s url=%s error=%s", subreddit, url, e)
            return []

    feed = feedparser.parse(resp.content)
    if not feed.entries:
        logger.warning("rss_empty subreddit=%s", subreddit)
        return []

    now_ts = time.time()
    posts: List[Dict[str, Any]] = []

    for entry in feed.entries:
        # ── 帖子 ID（从 URL 中提取 comments/{id}/）──────
        link  = entry.get("link", "")
        parts = [p for p in link.rstrip("/").split("/") if p]
        try:
            idx     = parts.index("comments")
            post_id = parts[idx + 1]
        except (ValueError, IndexError):
            post_id = re.sub(r"[^a-z0-9]", "", link.split("/")[-2] or link[-8:])

        # ── 发布时间 ──────────────────────────────────────
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            created_utc = time.mktime(entry.published_parsed)
        else:
            created_utc = now_ts

        # ── 正文（RSS summary 是 HTML，去标签）────────────
        raw_html  = entry.get("summary", "")
        selftext  = re.sub(r"<[^>]+>", " ", raw_html)
        selftext  = re.sub(r"&#\d+;|&\w+;", " ", selftext)
        selftext  = re.sub(r"\s+", " ", selftext).strip()[:2000]

        # ── 作者 ──────────────────────────────────────────
        author = ""
        if hasattr(entry, "author_detail"):
            author = entry.author_detail.get("name", "")
        elif hasattr(entry, "author"):
            author = str(entry.author)
        author = author.replace("/u/", "").strip()

        # ── 图片：从 RSS HTML 提取高分辨率图片 URL ─────
        # 用 _extract_rss_image_urls 统一处理：
        #   - 反转义 &amp; → &
        #   - 合并 <img src=...> 与 <a href=...>（gallery 帖关键）
        #   - preview.redd.it → i.redd.it 自动升级到原图
        #   - 去重 + 上限 _MAX_IMAGES_PER_POST
        img_urls = _extract_rss_image_urls(html.unescape(raw_html))

        posts.append({
            "id":           post_id,
            "title":        html.unescape(entry.get("title", "").strip()),
            "selftext":     selftext,
            "url":          link,
            "score":        1,      # RSS 不提供，设 1 以通过 min_score≥1 门槛
            "num_comments": 0,
            "upvote_ratio": 0.9,    # 默认高好评率
            "created_utc":  created_utc,
            "created_date": datetime.fromtimestamp(created_utc).strftime("%Y-%m-%d %H:%M"),
            "author":       author,
            "comments":     [],
            "image_urls":   img_urls,
            "local_images": [],
            "subreddit":    subreddit,
        })

    logger.info("rss_fetched subreddit=%s mode=%s count=%d", subreddit, mode, len(posts))
    return posts


# ═══════════════════════════════════════════════════════════════════
#  图片 URL 提取
# ═══════════════════════════════════════════════════════════════════

def _extract_image_urls(data: dict, session: requests.Session,
                        delay: float) -> List[str]:
    """
    从帖子数据中提取图片 URL（最多3张）。
    分三种情况处理：
      1. 直接图片帖 (post_hint == "image")
      2. Gallery 帖（hot.json 不含 media_metadata，需二次请求）
      3. 预览图 (preview.images)
    """
    urls: List[str] = []
    post_hint = data.get("post_hint", "") or ""
    post_url = data.get("url", "") or ""

    # ── 情况 1：直接图片帖 ────────────────────────────
    if post_hint == "image":
        img_url = data.get("url_overridden_by_dest") or data.get("url", "")
        if img_url and _is_image_url(img_url):
            urls.append(img_url)
            logger.info(f"  [图片] 直链图片: {img_url[:70]}...")
            return urls

    # ── 情况 2：Gallery ───────────────────────────────
    is_gallery = data.get("is_gallery", False)
    if not is_gallery and "reddit.com/gallery/" in post_url:
        is_gallery = True  # 有些帖子 flag 没设但 URL 是 gallery

    if is_gallery:
        # hot.json 里 media_metadata 可能缺失，尝试直接用，缺失则二次请求
        media_metadata = data.get("media_metadata")
        if not media_metadata:
            post_id = data.get("id", "")
            if post_id:
                logger.info(f"  [图片] Gallery 帖，正在获取完整数据 (id={post_id})...")
                time.sleep(delay)  # 避免限流
                full_data, _ = _fetch_single_post(session, post_id)
                if full_data:
                    media_metadata = full_data.get("media_metadata")
                    # 同时更新 gallery_data
                    if not data.get("gallery_data") and full_data.get("gallery_data"):
                        data["gallery_data"] = full_data["gallery_data"]

        if media_metadata:
            # 按照 gallery_data.items 的顺序提取（保持原始顺序）
            gallery_items = []
            if data.get("gallery_data") and data["gallery_data"].get("items"):
                gallery_items = [
                    item["media_id"]
                    for item in data["gallery_data"]["items"]
                ]
            else:
                gallery_items = list(media_metadata.keys())

            for media_id in gallery_items:
                if len(urls) >= 3:
                    break
                item = media_metadata.get(media_id, {})
                if item.get("status") == "valid" and "s" in item:
                    raw = item["s"].get("u", "")
                    if raw:
                        clean_url = html.unescape(raw)
                        urls.append(clean_url)
                        logger.info(f"  [图片] Gallery: {clean_url[:70]}...")

            if urls:
                return urls

    # ── 情况 3：预览图（link / self 帖内嵌图片）────────
    if not urls:
        try:
            preview = data.get("preview") or {}
            images = preview.get("images", [])
            if images:
                raw = images[0]["source"]["url"]
                clean_url = html.unescape(raw)
                urls.append(clean_url)
                logger.info(f"  [图片] 预览图: {clean_url[:70]}...")
        except (KeyError, IndexError):
            pass

    if not urls:
        logger.info("  [图片] 此帖无图片")

    return urls[:3]


def _is_image_url(url: str) -> bool:
    """判断 URL 是否指向图片文件。"""
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in
               (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))


# ═══════════════════════════════════════════════════════════════════
#  图片下载
# ═══════════════════════════════════════════════════════════════════

def _download_image(session: requests.Session, url: str,
                    output_dir: str, index: int, img_index: int) -> Optional[str]:
    """下载单张图片，返回本地路径，失败返回 None。"""
    try:
        # Reddit 图片 CDN 需要 Referer 头，否则返回 403
        headers = {"Referer": "https://www.reddit.com/"}
        resp = session.get(url, stream=True, timeout=30, headers=headers)
        resp.raise_for_status()

        # 从 URL 或 Content-Type 确定扩展名
        content_type = resp.headers.get("content-type", "")
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "gif" in content_type:
            ext = ".gif"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            parsed_path = urlparse(url).path.lower()
            for e in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                if parsed_path.endswith(e):
                    ext = e.replace(".jpeg", ".jpg")
                    break

        filename = f"post{index:02d}_img{img_index}{ext}"
        local_path = os.path.join(output_dir, filename)

        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = os.path.getsize(local_path) // 1024
        logger.info(f"  ✅ 图片已保存: {filename} ({size_kb} KB)")
        return local_path

    except Exception as e:
        logger.warning(f"  ⚠️ 图片下载失败 ({url[:60]}...): {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
#  帖子提取
# ═══════════════════════════════════════════════════════════════════

def _extract_post(data: dict, session: requests.Session,
                  delay: float) -> Optional[Dict[str, Any]]:
    """从 Reddit 数据字典提取标准化帖子字段。"""
    try:
        created_utc = data.get("created_utc", 0)
        try:
            created_date = datetime.fromtimestamp(
                float(created_utc), tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        selftext = data.get("selftext", "") or ""
        selftext = html.unescape(selftext)
        selftext = re.sub(r"\n{3,}", "\n\n", selftext).strip()

        image_urls = _extract_image_urls(data, session, delay)

        # 对无正文的链接/图片帖，抓取热门评论补充内容
        comments: List[str] = []
        post_id = data.get("id", "")
        if not selftext and post_id and data.get("num_comments", 0) > 0:
            logger.info(f"  [评论] 正文为空，抓取热门评论补充内容...")
            time.sleep(delay)
            _, comments_raw = _fetch_single_post(session, post_id)
            comments = _extract_top_comments(comments_raw, max_comments=3)
            if comments:
                logger.info(f"  [评论] 获取到 {len(comments)} 条热门评论")

        return {
            "id": post_id,
            "title": html.unescape(data.get("title", "")),
            "selftext": selftext,
            "comments": comments,          # 无正文时的补充内容
            "url": data.get("url", ""),
            "score": data.get("score", 0),
            "upvote_ratio": data.get("upvote_ratio", 0.0),
            "num_comments": data.get("num_comments", 0),
            "created_utc": created_utc,
            "created_date": created_date,
            "author": data.get("author", "Unknown"),
            "is_stickied": bool(data.get("stickied", False)),
            "post_type": _get_post_type(data),
            "image_urls": image_urls,
            "local_images": [],  # 由 download_images() 填充
        }
    except Exception as e:
        logger.warning(f"解析帖子失败，跳过: {e}")
        return None


def _get_post_type(data: dict) -> str:
    if data.get("is_gallery") or "reddit.com/gallery/" in (data.get("url") or ""):
        return "gallery"
    hint = data.get("post_hint", "")
    if hint == "image":
        return "image"
    if data.get("is_self"):
        return "self"
    return "link"


# ═══════════════════════════════════════════════════════════════════
#  图片分析 & 视频信息提取
# ═══════════════════════════════════════════════════════════════════

_CLAUDE_API_URL   = "https://api.anthropic.com/v1/messages"
_CLAUDE_MODEL_DEF = "claude-haiku-4-5-20251001"   # 快速便宜，支持视觉
_VISION_MODEL_DEF = _CLAUDE_MODEL_DEF             # 兼容旧引用
_VISION_PROMPT    = (
    "请详细描述这张图片的内容，用中文回答。"
    "重点说明核心概念、技术要点、图表数据或视觉信息，150字以内。"
)


def _analyze_image(session: requests.Session, image_url: str,
                   api_key: str, model: str = _CLAUDE_MODEL_DEF) -> Optional[str]:
    """调用 Claude API 描述图片内容，返回中文描述，失败返回 None。"""
    payload = {
        "model": model,
        "max_tokens": 400,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "url", "url": image_url},
                },
                {
                    "type": "text",
                    "text": _VISION_PROMPT,
                },
            ],
        }],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        resp = requests.post(_CLAUDE_API_URL, headers=headers,
                             json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.warning(f"  [视觉API] 分析失败，跳过: {e}")
        return None


def _is_youtube_url(url: str) -> bool:
    """判断 URL 是否为 YouTube 视频链接。"""
    return bool(url and ("youtube.com/watch" in url or "youtu.be/" in url))


def _get_youtube_info(session: requests.Session, url: str) -> Optional[dict]:
    """
    通过 YouTube oEmbed API 获取视频基本信息（无需 API Key）。
    返回 {"title": ..., "author_name": ..., "thumbnail_url": ...}
    """
    try:
        oembed_url = "https://www.youtube.com/oembed"
        resp = session.get(oembed_url, params={"url": url, "format": "json"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "title":         data.get("title", ""),
            "author_name":   data.get("author_name", ""),
            "thumbnail_url": data.get("thumbnail_url", ""),
        }
    except Exception as e:
        logger.debug(f"  [YouTube] oEmbed 获取失败: {e}")
        return None


def _fetch_link_content(url: str, session: requests.Session,
                        retries: int = 1) -> str:
    """
    抓取链接帖的外链网页正文（BeautifulSoup）。
    与 seo_scraper.fetch_article_content 逻辑一致。
    返回纯文本（≤4000字），失败返回空字符串。
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return ""

    for attempt in range(retries + 1):
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            logger.info("link_fetch_failed url=%s error=%s", url[:60], e)
            return ""

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "form", "noscript", "iframe"]):
            tag.decompose()
        content_el = (
            soup.find("article") or
            soup.find(class_=re.compile(
                r"(post|entry|content|article)[-_]?(body|content|text)?", re.I)) or
            soup.find("main") or
            soup.body
        )
        if not content_el:
            return ""
        lines = []
        for el in content_el.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
            text = el.get_text(separator=" ").strip()
            if len(text) > 30:
                lines.append(text)
        return "\n\n".join(lines)[:4000]
    except Exception as e:
        logger.info("link_parse_failed url=%s error=%s", url[:60], e)
        return ""


def _enrich_selftext(post: dict, cfg: dict,
                     session: requests.Session, delay: float) -> None:
    """
    分析帖子的图片和视频，将结论追加到 post["selftext"]。
    - 图片：调用 Claude API（需 claude_api_key）
    - YouTube视频：调用 oEmbed API（免费，无需Key）
    修改 post 对象（原地修改），无返回值。
    """
    extra_parts: List[str] = []

    # ── 图片分析 ──────────────────────────────────────
    api_key = cfg.get("claude_api_key", "").strip()
    model   = cfg.get("claude_vision_model", _CLAUDE_MODEL_DEF).strip() or _CLAUDE_MODEL_DEF

    if api_key and post.get("image_urls"):
        descriptions = []
        for i, img_url in enumerate(post["image_urls"], 1):
            if i > 1:
                time.sleep(delay)
            logger.info(f"  [视觉API] 分析图{i}: {img_url[:60]}...")
            desc = _analyze_image(session, img_url, api_key, model)
            if desc:
                descriptions.append(f"图{i}：{desc}")
        if descriptions:
            extra_parts.append("【图片分析】\n" + "\n".join(descriptions))

    # ── YouTube 视频信息 ──────────────────────────────
    if _is_youtube_url(post.get("url", "")):
        logger.info(f"  [YouTube] 获取视频信息...")
        info = _get_youtube_info(session, post["url"])
        if info:
            lines = ["【视频信息】"]
            if info["author_name"]:
                lines.append(f"频道：{info['author_name']}")
            if info["title"]:
                lines.append(f"标题：{info['title']}")
            extra_parts.append("\n".join(lines))

    # ── 链接帖：抓取外链正文（BeautifulSoup）────────────
    url = post.get("url", "")
    selftext_now = (post.get("selftext") or "").strip()
    is_link_post = (
        url
        and "reddit.com" not in url
        and (_is_rss_stub(selftext_now) or len(selftext_now) < 80)
    )
    if is_link_post:
        page_text = _fetch_link_content(url, session)
        if page_text:
            post["selftext"] = page_text
            logger.info("link_content_fetched url=%s len=%d", url[:60], len(page_text))
        else:
            logger.info("link_content_empty url=%s", url[:60])

    # ── 追加到 selftext ───────────────────────────────
    if extra_parts:
        sep = "\n\n" if post.get("selftext") else ""
        post["selftext"] = (post.get("selftext") or "") + sep + "\n\n".join(extra_parts)
        logger.info(f"  [内容增强] 已追加: {', '.join(p.split(chr(10))[0] for p in extra_parts)}")


# ═══════════════════════════════════════════════════════════════════
#  广告过滤
# ═══════════════════════════════════════════════════════════════════

_AD_TITLE_KEYWORDS = [
    "buy now", "on sale", "discount", "coupon", "promo code", "affiliate",
    "check out my", "dm me", "click here", "sign up", "subscribe to",
    "free trial", "limited offer", "get yours", "use code", "sponsored",
    "i made this", "my app", "my tool", "my product", "my service",
    "launching", "pre-order", "waitlist",
]
_AD_TEXT_KEYWORDS = [
    "affiliate link", "referral code", "use my link", "earn commission",
    "not financial advice", "not investment advice",
]

def _is_ad_post(post: dict) -> bool:
    """检测广告/自我推广帖子。标题或正文命中广告词即过滤。"""
    title    = (post.get("title")    or "").lower()
    selftext = (post.get("selftext") or "").lower()
    if any(kw in title for kw in _AD_TITLE_KEYWORDS):
        return True
    if any(kw in selftext for kw in _AD_TEXT_KEYWORDS):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════
#  关键词过滤 / 内容充分性
# ═══════════════════════════════════════════════════════════════════

# RSS 链接帖的空内容占位符（BeautifulSoup 抓取后会覆盖）
_RSS_STUB_RE = re.compile(r"^submitted by /u/\S+", re.I)

def _is_rss_stub(selftext: str) -> bool:
    """判断是否为 RSS 链接帖的空占位符（非真实正文）。"""
    return bool(_RSS_STUB_RE.match(selftext.strip()))


def _has_sufficient_content(post: dict) -> bool:
    """
    内容充分性检查。
    - RSS 链接帖的 "submitted by /u/..." 占位符不算内容，但允许通过
      （后续 _enrich_selftext 会抓取外链正文）
    - 纯图片帖（真正的空 selftext + 无评论 + 无图片链接）过滤
    """
    selftext = (post.get("selftext") or "").strip()
    comments = post.get("comments") or []
    img_urls = post.get("image_urls") or []
    url      = post.get("url", "")

    # RSS 链接帖：占位符 + 有外链 → 放行，后续抓取正文
    if _is_rss_stub(selftext) and url and "reddit.com" not in url:
        return True
    return len(selftext) > 20 or len(comments) > 0 or len(img_urls) > 0


def _relevance_score(post: dict, keywords: List[str]) -> int:
    """计算帖子与 AI 主题的相关分数（关键词命中数）。"""
    if not keywords:
        return 1  # 不过滤时全部保留
    text = (post["title"] + " " + post["selftext"]).lower()
    return sum(1 for kw in keywords if kw in text)


def _compute_composite_score(post: dict, weights: dict, now_ts: float) -> float:
    """
    计算帖子的复合质量评分（0~1）。
    - recency：时效分，线性衰减，7天后归零
    - score：热度分，log归一化（参考上限10000分）
    - comments：讨论分，log归一化（参考上限1000条）
    - relevance：相关性分（关键词命中数，上限5个）
    upvote_ratio 作为乘法系数，降低争议帖排名。
    """
    age_hours = (now_ts - float(post.get("created_utc", now_ts))) / 3600
    recency   = max(0.0, 1.0 - age_hours / 168)
    score_f   = min(1.0, math.log1p(max(0, post.get("score", 0))) / math.log1p(10000))
    comment_f = min(1.0, math.log1p(post.get("num_comments", 0)) / math.log1p(1000))
    relevance_f = min(1.0, post.get("_relevance", 1) / 5)
    raw = (
        weights.get("recency",   0) * recency    +
        weights.get("score",     0) * score_f    +
        weights.get("comments",  0) * comment_f  +
        weights.get("relevance", 0) * relevance_f
    )
    return raw * max(0.5, post.get("upvote_ratio", 0.7))


# ═══════════════════════════════════════════════════════════════════
#  历史去重
# ═══════════════════════════════════════════════════════════════════

def _load_seen_ids(base_dir: str) -> set:
    """加载历史已抓取帖子 ID，避免重复。"""
    seen_file = Path(base_dir) / "seen_posts.json"
    if not seen_file.exists():
        return set()
    try:
        with open(seen_file, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("post_ids", []))
    except Exception as e:
        logger.warning(f"读取历史记录失败: {e}")
        return set()


def _save_seen_ids(base_dir: str, seen: set):
    """保存已抓取帖子 ID（保留最近 200 条，防止文件无限增长）。"""
    seen_file = Path(base_dir) / "seen_posts.json"
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    # 只保留最新的 200 条
    ids_list = list(seen)[-200:]
    try:
        with open(seen_file, "w", encoding="utf-8") as f:
            json.dump({
                "post_ids": ids_list,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"历史记录已保存 ({len(ids_list)} 条): {seen_file}")
    except Exception as e:
        logger.warning(f"保存历史记录失败: {e}")


# ═══════════════════════════════════════════════════════════════════
#  主函数
# ═══════════════════════════════════════════════════════════════════

def _scrape_subreddit(session: requests.Session, subreddit: str,
                      quota: int, seen_ids: set, selected_authors: set,
                      keywords: List[str], delay: float,
                      strategy: dict, cfg: dict = None) -> List[Dict[str, Any]]:
    """
    从单个 subreddit 通过 RSS Feed 抓取候选帖，评分排序后取 quota 条。
    RSS 不提供 score/upvote_ratio，评分以时效性和关键词相关性为主。
    """
    api_mode  = strategy.get("api_mode", "hot")
    max_age_h = strategy.get("max_age_hours", 168)
    # RSS 无点赞数，跳过 min_score / min_upvote_ratio 门槛
    weights   = strategy.get("weights", {"recency": 0.6, "relevance": 0.4,
                                          "score": 0.0, "comments": 0.0})
    now_ts = time.time()

    logger.info("  [%s] 通过 RSS 抓取（mode=%s）...", subreddit, api_mode)
    raw_posts = _fetch_rss_posts(session, subreddit, api_mode)
    if not raw_posts:
        logger.warning("  r/%s 无新帖，跳过", subreddit)
        return []

    # ── 过滤：去重 + 广告 + 年龄 + 关键词 + 内容充分性 ──────────
    candidates: List[Dict[str, Any]] = []
    for post in raw_posts:
        if post["id"] in seen_ids:
            continue
        if post["author"] and post["author"] in selected_authors:
            continue
        if _is_ad_post(post):
            logger.info("  [过滤] 广告帖，跳过: %s", post["title"][:40])
            continue
        age_h = (now_ts - post["created_utc"]) / 3600
        if age_h > max_age_h:
            continue
        rel = _relevance_score(post, keywords)
        if keywords and rel == 0:
            continue
        if not _has_sufficient_content(post):
            logger.info("  [过滤] 内容不足，跳过: %s", post["title"][:40])
            continue
        post["_relevance"] = rel
        candidates.append(post)

    if not candidates:
        logger.info("  r/%s 无候选帖", subreddit)
        return []

    logger.info("  [%s] 候选帖 %d 条，开始评分...", subreddit, len(candidates))

    # ── 评分排序，取前 quota 条 ───────────────────────────
    for post in candidates:
        post["_composite"] = _compute_composite_score(post, weights, now_ts)
    candidates.sort(key=lambda p: p["_composite"], reverse=True)
    picked = candidates[:quota]

    for post in picked:
        selected_authors.add(post.get("author", ""))
        if cfg:
            _enrich_selftext(post, cfg, session, delay)
        logger.info("  ✅ r/%s [评分%.2f] → %s",
                    subreddit, post.get("_composite", 0), post["title"][:50])

    return picked


def scrape(config: dict = None) -> List[Dict[str, Any]]:
    """
    主入口：从多个 subreddit 抓取帖子 + 下载图片，返回帖子列表。

    Args:
        config: 配置字典（不传则使用文件顶部的 CONFIG）

    Returns:
        帖子列表（包含 local_images 本地路径列表）
    """
    cfg = config or CONFIG
    # 支持新的 subreddits 列表，兼容旧的 subreddit 单值
    subreddits = cfg.get("subreddits") or [cfg.get("subreddit", "ThinkingDeeplyAI")]
    limit_min   = int(cfg.get("limit_min", cfg.get("limit", 5)))
    limit_max   = int(cfg.get("limit_max", limit_min))
    limit       = random.randint(limit_min, limit_max)
    logger.info(f"今日目标：{limit} 条（随机范围 {limit_min}~{limit_max}）")
    proxy       = cfg.get("proxy", "")
    delay       = cfg.get("request_delay", 1.5)
    keywords    = [k.lower() for k in cfg.get("ai_keywords", [])]

    # 策略选择（默认 trending）
    strategy_name = cfg.get("strategy", "trending")
    strategy = STRATEGIES.get(strategy_name, STRATEGIES["trending"])
    logger.info(f"抓取策略: {strategy_name}（{strategy['api_mode']} | "
                f"min_score≥{strategy['min_score']} | "
                f"max_age≤{strategy['max_age_hours']}h）")

    # 输出目录：按日期子目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    if cfg.get("output_dir"):
        base_dir   = cfg["output_dir"]
        output_dir = os.path.join(base_dir, date_str, "images")
    else:
        base_dir   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        output_dir = os.path.join(base_dir, date_str, "images")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"图片保存目录: {output_dir}")

    # ── 加载历史记录（去重用）────────────────────────
    seen_ids = _load_seen_ids(base_dir)
    logger.info(f"历史记录: {len(seen_ids)} 条已见过的帖子 ID")

    # ── Reddit OAuth（推荐，2023年后必须）────────────
    client_id     = cfg.get("reddit_client_id", "").strip()
    client_secret = cfg.get("reddit_client_secret", "").strip()
    oauth_token   = _fetch_oauth_token(client_id, client_secret, proxy)
    if not oauth_token:
        logger.warning(
            "no_oauth_token — 请在设置中填写 Reddit Client ID / Secret"
            "（参考：https://www.reddit.com/prefs/apps）"
        )
    session = _make_session(proxy, oauth_token)

    # ── 计算每个社区的配额 ────────────────────────────
    # 例：5条帖子 / 7个社区 → 前5个社区各取1条
    n_subs = len(subreddits)
    base_quota = limit // n_subs          # 每个社区基础配额
    extra      = limit % n_subs           # 余数分给前 extra 个社区
    quotas = [base_quota + (1 if i < extra else 0) for i in range(n_subs)]
    # 过滤配额为0的社区（当社区数 > limit 时）
    active = [(sub, q) for sub, q in zip(subreddits, quotas) if q > 0]

    logger.info(f"本次抓取计划: {len(active)} 个社区，总目标 {limit} 条")
    for sub, q in active:
        logger.info(f"  r/{sub} → {q} 条")

    # ── 逐社区抓取 ────────────────────────────────────
    selected: List[Dict[str, Any]] = []
    selected_authors: set = set()

    for sub, quota in active:
        logger.info(f"\n══ 正在抓取 r/{sub}（目标 {quota} 条）...")
        posts = _scrape_subreddit(
            session, sub, quota,
            seen_ids, selected_authors, keywords, delay,
            strategy=strategy, cfg=cfg
        )
        if posts:
            selected.extend(posts)
            logger.info(f"  r/{sub} 贡献 {len(posts)} 条")
        else:
            logger.warning(f"  r/{sub} 无新帖，跳过")
        time.sleep(delay)

    if not selected:
        logger.error("所有社区均无新帖子，请检查网络或减少历史记录")
        return []

    logger.info(f"\n共选出 {len(selected)} 条帖子（来自 {len(set(p['subreddit'] for p in selected))} 个社区）")

    # ── 下载图片 ──────────────────────────────────────
    logger.info("开始下载配图...")
    for i, post in enumerate(selected, 1):
        logger.info(f"\n── 帖子 {i}/{len(selected)}: {post['title'][:60]}")
        if not post["image_urls"]:
            logger.info("  此帖无图片，跳过")
            continue
        for j, url in enumerate(post["image_urls"], 1):
            time.sleep(delay)
            local_path = _download_image(session, url, output_dir, i, j)
            if local_path:
                post["local_images"].append({"url": url, "local_path": local_path})

    # ── 保存历史记录 ──────────────────────────────────
    seen_ids.update(p["id"] for p in selected)
    _save_seen_ids(base_dir, seen_ids)

    # ── 清理临时字段并返回 ────────────────────────────
    for post in selected:
        post.pop("_relevance", None)
        post.pop("_composite", None)

    logger.info(f"\n{'='*50}")
    logger.info(f"✅ 完成！共处理 {len(selected)} 条帖子")
    total_imgs = sum(len(p["local_images"]) for p in selected)
    logger.info(f"✅ 共下载 {total_imgs} 张图片到 {output_dir}")
    return selected


# ═══════════════════════════════════════════════════════════════════
#  结果输出
# ═══════════════════════════════════════════════════════════════════

def print_summary(posts: List[Dict[str, Any]]) -> None:
    """打印帖子摘要到终端。"""
    print("\n" + "=" * 60)
    print(f"  抓取结果汇总  ({len(posts)} 条帖子)")
    print("=" * 60)
    for i, post in enumerate(posts, 1):
        print(f"\n【帖子 {i}】{post['title']}")
        print(f"  类型: {post['post_type']}  "
              f"热度: {post['score']}  "
              f"评论: {post['num_comments']}")
        print(f"  时间: {post['created_date']}  "
              f"作者: u/{post['author']}")
        print(f"  链接: {post['url']}")
        if post["selftext"]:
            preview = post["selftext"][:120].replace("\n", " ")
            print(f"  内容: {preview}...")
        if post["local_images"]:
            print(f"  图片: {len(post['local_images'])} 张已下载")
            for img in post["local_images"]:
                print(f"    └─ {img['local_path']}")
        else:
            print("  图片: 无")


def save_json(posts: List[Dict[str, Any]], output_dir: str) -> str:
    """将帖子数据保存为 JSON 文件，方便后续处理。"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "output", f"posts_{date_str}.json"
    )
    Path(os.path.dirname(json_path)).mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    logger.info(f"帖子数据已保存: {json_path}")
    return json_path


# ═══════════════════════════════════════════════════════════════════
#  入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    posts = scrape()

    if posts:
        print_summary(posts)
        save_json(posts, CONFIG.get("output_dir", ""))
    else:
        print("\n❌ 未抓取到任何帖子，请检查：")
        print("  1. 网络连接（国内用户请设置 CONFIG['proxy']）")
        print("  2. 代理格式示例：\"http://127.0.0.1:7890\"")
