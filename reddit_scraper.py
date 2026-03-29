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
    # 多社区抓取（每天从不同社区各取1条，提高内容多样性）
    "subreddits": [
        "ThinkingDeeplyAI",
        "AgentsOfAI",
        "aiArt",
        "aivideo",
        "ClaudeCode",
        "Teachers",
        "books",
    ],

    # 获取帖子总数量（会均分到各社区）
    "limit": 5,

    # 抓取模式："hot"=热门(置顶帖靠前) / "top"=今日最热
    "mode": "hot",

    # 代理（国内用户必须填，留空则直连）
    # 示例："http://127.0.0.1:7890"
    "proxy": "",

    # 图片保存目录（留空则保存到脚本同目录下的 output/images/{日期}/）
    "output_dir": "",

    # 每次 API 请求之间的间隔（秒），避免触发限流
    "request_delay": 1.5,

    # AI 主题关键词过滤（留空列表则不过滤）
    "ai_keywords": [
        "llm", "large language model", "agent", "machine learning",
        "claude", "openai", "codex", "deepseek", "kimi", "veo", "gemini",
        "gpt", "diffusion", "transformer", "neural", "algorithm",
        "fine-tuning", "rag", "multimodal", "reasoning", "inference",
        "model", "ai", "artificial intelligence",
        "art", "teacher", "book", "education", "creative",
    ],
}
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_BASE_URL = "https://www.reddit.com"
_USER_AGENT = "python:reddit-ai-scraper:v2.0 (standalone)"


# ═══════════════════════════════════════════════════════════════════
#  HTTP 会话
# ═══════════════════════════════════════════════════════════════════

def _make_session(proxy: str) -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"User-Agent": _USER_AGENT})
    if proxy:
        sess.proxies.update({"http": proxy, "https": proxy})
        logger.info(f"使用代理: {proxy}")
    return sess


# ═══════════════════════════════════════════════════════════════════
#  Reddit API 调用
# ═══════════════════════════════════════════════════════════════════

def _fetch_listing(session: requests.Session, endpoint: str,
                   params: dict = None) -> tuple:
    """请求 Reddit 列表接口，返回 (children列表, after游标)。"""
    url = f"{_BASE_URL}{endpoint}"
    try:
        resp = session.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        children = data.get("children", [])
        after = data.get("after")  # 下一页游标，None 表示没有更多
        return children, after
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败 {url}: {e}")
        return [], None


def _fetch_single_post(session: requests.Session, post_id: str) -> Optional[dict]:
    """
    请求单条帖子的完整 JSON（含 media_metadata 和评论）。
    Reddit 的列表接口(hot.json)不包含 media_metadata，
    必须通过此接口单独获取 Gallery 图片。
    返回 (post_data, comments_list)
    """
    url = f"{_BASE_URL}/comments/{post_id}.json"
    try:
        resp = session.get(url, params={"limit": 10, "depth": 1}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        # 响应结构: [帖子列表, 评论列表]
        post_data = data[0]["data"]["children"][0]["data"]
        comments_raw = data[1]["data"]["children"] if len(data) > 1 else []
        return post_data, comments_raw
    except Exception as e:
        logger.debug(f"获取单帖失败 (id={post_id}): {e}")
        return None, []


def _extract_top_comments(comments_raw: list, max_comments: int = 3) -> List[str]:
    """从评论列表中提取热门评论文本（按点赞数排序，过滤掉机器人/删除评论）。"""
    comments = []
    for child in comments_raw:
        if child.get("kind") != "t1":
            continue
        d = child.get("data", {})
        body = d.get("body", "").strip()
        score = d.get("score", 0)
        author = d.get("author", "")
        # 跳过已删除、机器人、太短的评论
        if not body or body in ("[deleted]", "[removed]"):
            continue
        if author in ("AutoModerator", "reddit-bot"):
            continue
        if len(body) < 20:
            continue
        comments.append((score, html.unescape(body)))
    # 按点赞数降序，取前 max_comments 条
    comments.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in comments[:max_comments]]


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
        resp = session.get(url, stream=True, timeout=30)
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

    # ── 追加到 selftext ───────────────────────────────
    if extra_parts:
        sep = "\n\n" if post.get("selftext") else ""
        post["selftext"] = (post.get("selftext") or "") + sep + "\n\n".join(extra_parts)
        logger.info(f"  [内容增强] 已追加: {', '.join(p.split(chr(10))[0] for p in extra_parts)}")


# ═══════════════════════════════════════════════════════════════════
#  关键词过滤
# ═══════════════════════════════════════════════════════════════════

def _relevance_score(post: dict, keywords: List[str]) -> int:
    """计算帖子与 AI 主题的相关分数（关键词命中数）。"""
    if not keywords:
        return 1  # 不过滤时全部保留
    text = (post["title"] + " " + post["selftext"]).lower()
    return sum(1 for kw in keywords if kw in text)


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

def _scrape_subreddit(session: requests.Session, subreddit: str, mode: str,
                      quota: int, seen_ids: set, selected_authors: set,
                      keywords: List[str], delay: float,
                      cfg: dict = None) -> List[Dict[str, Any]]:
    """
    从单个 subreddit 抓取最多 quota 条新帖（跳过已见过的ID和已选过的作者）。
    """
    if mode == "top":
        endpoint = f"/r/{subreddit}/top.json"
        base_params = {"limit": 25, "t": "week"}
    else:
        endpoint = f"/r/{subreddit}/hot.json"
        base_params = {"limit": 25}

    picked: List[Dict[str, Any]] = []
    after_cursor = None
    max_pages = 3  # 每个社区最多翻3页

    for page in range(max_pages):
        params = dict(base_params)
        if after_cursor:
            params["after"] = after_cursor

        logger.info(f"  [{subreddit}] 第{page+1}页...")
        children, after_cursor = _fetch_listing(session, endpoint, params)

        if not children:
            break

        for child in children:
            if len(picked) >= quota:
                break
            data = child.get("data", {})
            post_id = data.get("id", "")
            author  = data.get("author", "")

            if post_id in seen_ids:
                continue
            if author and author in selected_authors:
                continue

            post = _extract_post(data, session, delay)
            if not post:
                continue

            score = _relevance_score(post, keywords)
            if keywords and score == 0:
                continue

            post["_relevance"] = score
            post["subreddit"] = subreddit  # 记录来源社区

            # ── 图片分析 + 视频信息（丰富 selftext）────
            if cfg:
                _enrich_selftext(post, cfg, session, delay)

            picked.append(post)
            selected_authors.add(author)
            logger.info(f"  ✅ r/{subreddit} → {post['title'][:55]}")
            time.sleep(0.1)

        if len(picked) >= quota:
            break
        if not after_cursor:
            break
        time.sleep(delay)

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
    limit       = cfg["limit"]
    mode        = cfg["mode"]
    proxy       = cfg.get("proxy", "")
    delay       = cfg.get("request_delay", 1.5)
    keywords    = [k.lower() for k in cfg.get("ai_keywords", [])]

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

    session = _make_session(proxy)

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
            session, sub, mode, quota,
            seen_ids, selected_authors, keywords, delay,
            cfg=cfg
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
