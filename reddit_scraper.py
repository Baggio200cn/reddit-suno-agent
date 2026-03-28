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
    # Reddit 目标版块（不含 r/）
    "subreddit": "ThinkingDeeplyAI",

    # 获取帖子数量
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
                   params: dict = None) -> List[dict]:
    """请求 Reddit 列表接口，返回 children 列表。"""
    url = f"{_BASE_URL}{endpoint}"
    try:
        resp = session.get(url, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("children", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败 {url}: {e}")
        return []


def _fetch_single_post(session: requests.Session, post_id: str) -> Optional[dict]:
    """
    请求单条帖子的完整 JSON（含 media_metadata）。
    Reddit 的列表接口(hot.json)不包含 media_metadata，
    必须通过此接口单独获取 Gallery 图片。
    """
    url = f"{_BASE_URL}/comments/{post_id}.json"
    try:
        resp = session.get(url, params={"limit": 1}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        # 响应结构: [帖子列表, 评论列表]
        return data[0]["data"]["children"][0]["data"]
    except Exception as e:
        logger.debug(f"获取单帖失败 (id={post_id}): {e}")
        return None


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
                full_data = _fetch_single_post(session, post_id)
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

        return {
            "id": data.get("id", ""),
            "title": html.unescape(data.get("title", "")),
            "selftext": selftext,
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
#  关键词过滤
# ═══════════════════════════════════════════════════════════════════

def _relevance_score(post: dict, keywords: List[str]) -> int:
    """计算帖子与 AI 主题的相关分数（关键词命中数）。"""
    if not keywords:
        return 1  # 不过滤时全部保留
    text = (post["title"] + " " + post["selftext"]).lower()
    return sum(1 for kw in keywords if kw in text)


# ═══════════════════════════════════════════════════════════════════
#  主函数
# ═══════════════════════════════════════════════════════════════════

def scrape(config: dict = None) -> List[Dict[str, Any]]:
    """
    主入口：抓取帖子 + 下载图片，返回帖子列表。

    Args:
        config: 配置字典（不传则使用文件顶部的 CONFIG）

    Returns:
        帖子列表（包含 local_images 本地路径列表）
    """
    cfg = config or CONFIG
    subreddit   = cfg["subreddit"]
    limit       = cfg["limit"]
    mode        = cfg["mode"]
    proxy       = cfg.get("proxy", "")
    delay       = cfg.get("request_delay", 1.5)
    keywords    = [k.lower() for k in cfg.get("ai_keywords", [])]

    # 输出目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    if cfg.get("output_dir"):
        output_dir = cfg["output_dir"]
    else:
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "output", "images", date_str
        )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"图片保存目录: {output_dir}")

    session = _make_session(proxy)

    # ── 1. 请求 Reddit 列表 ───────────────────────────
    logger.info(f"正在从 r/{subreddit} 抓取 {mode} 帖子（扫描前25条）...")
    if mode == "top":
        endpoint = f"/r/{subreddit}/top.json"
        params = {"limit": 25, "t": "day"}
    else:
        endpoint = f"/r/{subreddit}/hot.json"
        params = {"limit": 25}

    children = _fetch_listing(session, endpoint, params)
    if not children:
        logger.error("未获取到任何帖子，请检查网络或代理设置")
        return []

    logger.info(f"API 返回 {len(children)} 条原始数据，开始过滤和解析...")

    # ── 2. 解析并过滤 ─────────────────────────────────
    all_posts = []
    for child in children:
        data = child.get("data", {})
        post = _extract_post(data, session, delay)
        if post:
            post["_relevance"] = _relevance_score(post, keywords)
            all_posts.append(post)
        time.sleep(0.1)  # 轻微间隔

    # 按相关度排序（keyword 匹配数降序），过滤掉完全不相关的
    if keywords:
        relevant = [p for p in all_posts if p["_relevance"] > 0]
        if not relevant:
            logger.warning("无 AI 相关帖子，使用全部帖子")
            relevant = all_posts
        relevant.sort(key=lambda p: p["_relevance"], reverse=True)
        logger.info(f"AI 相关帖子: {len(relevant)}/{len(all_posts)} 条")
    else:
        relevant = all_posts

    selected = relevant[:limit]

    # ── 3. 下载图片 ───────────────────────────────────
    logger.info(f"开始下载 {len(selected)} 条帖子的配图...")
    for i, post in enumerate(selected, 1):
        logger.info(f"\n── 帖子 {i}/{len(selected)}: {post['title'][:60]}")
        if not post["image_urls"]:
            logger.info("  此帖无图片，跳过")
            continue
        for j, url in enumerate(post["image_urls"], 1):
            time.sleep(delay)
            local_path = _download_image(session, url, output_dir, i, j)
            if local_path:
                post["local_images"].append({
                    "url": url,
                    "local_path": local_path,
                })

    # ── 4. 清理临时字段并返回 ─────────────────────────
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
