"""
Reddit 数据收集器 - 使用 JSON API（无需 API 凭证）
"""
import html
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reddit JSON API 要求设置 User-Agent，否则会被限流
_DEFAULT_USER_AGENT = "python:reddit-suno-agent:v1.0"
_BASE_URL = "https://www.reddit.com"


class RedditCollector:
    """Reddit 数据收集器 - 使用无认证 JSON API"""

    def __init__(self, config: Dict[str, str] = None):
        """
        初始化 Reddit 收集器（无需 API 凭证）

        Args:
            config: 配置字典，支持以下可选字段：
                    - proxy: HTTP 代理地址，如 "http://127.0.0.1:7890"（中国大陆用户需要）
        """
        self.config = config or {}
        proxy_url = self.config.get("proxy") or None
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": _DEFAULT_USER_AGENT})
        if self.proxies:
            self.session.proxies.update(self.proxies)
            logger.info(f"使用代理: {proxy_url}")

    def collect_hot_posts(
        self, subreddit: str, limit: int = 5, mode: str = "hot"
    ) -> List[Dict[str, Any]]:
        """
        从指定 subreddit 收集热门/最热帖子

        Args:
            subreddit: subreddit 名称（不含 r/）
            limit: 收集帖子数量
            mode: "hot"（热门，置顶帖排最前）或 "top"（今日最热）

        Returns:
            帖子列表，每个帖子包含：
            id, title, selftext, url, score, num_comments,
            created_utc, created_date, author, upvote_ratio,
            image_urls, is_stickied, post_type
        """
        try:
            logger.info(f"开始从 r/{subreddit} 的 JSON API 收集 {mode} 帖子...")

            if mode == "top":
                endpoint = f"/r/{subreddit}/top.json"
                params = {"limit": 25, "t": "day"}
            else:
                endpoint = f"/r/{subreddit}/hot.json"
                params = {"limit": 25}

            children = self._fetch_json(endpoint, params)
            if not children:
                logger.warning("JSON API 中没有找到帖子")
                return []

            posts = []
            for child in children:
                if len(posts) >= limit:
                    break
                data = child.get("data", {})
                post = self._extract_post(data)
                if post:
                    posts.append(post)

            logger.info(f"成功收集 {len(posts)} 条帖子")
            return posts

        except Exception as e:
            logger.error(f"收集帖子失败: {e}")
            return []

    # ------------------------------------------------------------------
    # 私有方法
    # ------------------------------------------------------------------

    def _fetch_json(self, endpoint: str, params: dict = None) -> List[dict]:
        """调用 Reddit JSON API 并返回 children 列表"""
        url = f"{_BASE_URL}{endpoint}"
        logger.info(f"请求 Reddit JSON API: {url}")
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("children", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Reddit JSON API 请求失败: {e}")
            return []

    def _extract_post(self, data: dict) -> Optional[Dict[str, Any]]:
        """从帖子 data 字典提取标准化字段"""
        try:
            # 发布时间
            created_utc = data.get("created_utc", 0)
            try:
                created_date = datetime.fromtimestamp(
                    created_utc, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 正文（自帖）
            selftext = data.get("selftext", "") or ""
            selftext = html.unescape(selftext)
            # 移除 markdown 中的多余空行
            selftext = re.sub(r"\n{3,}", "\n\n", selftext).strip()

            return {
                "id": data.get("id", ""),
                "title": html.unescape(data.get("title", "")),
                "selftext": selftext,
                "url": data.get("url", ""),
                "score": data.get("score", 0),
                "num_comments": data.get("num_comments", 0),
                "created_utc": created_utc,
                "created_date": created_date,
                "author": data.get("author", "Unknown"),
                "upvote_ratio": data.get("upvote_ratio", 0.0),
                "is_stickied": bool(data.get("stickied", False)),
                "post_type": self._get_post_type(data),
                "image_urls": self._extract_image_urls(data),
            }
        except Exception as e:
            logger.warning(f"解析帖子数据失败，跳过: {e}")
            return None

    def _get_post_type(self, data: dict) -> str:
        """判断帖子类型"""
        if data.get("is_gallery"):
            return "gallery"
        hint = data.get("post_hint", "")
        if hint == "image":
            return "image"
        if data.get("is_self"):
            return "self"
        return "link"

    def _extract_image_urls(self, data: dict) -> List[str]:
        """从帖子 data 中提取图片 URL（最多3张）"""
        urls = []
        try:
            post_hint = data.get("post_hint", "")

            # 1. 直接图片帖
            if post_hint == "image":
                url = data.get("url", "")
                if url:
                    urls.append(url)

            # 2. 图片集（gallery）
            if data.get("is_gallery") and data.get("media_metadata"):
                # gallery_data.items 保留顺序
                gallery_order = []
                if data.get("gallery_data") and data["gallery_data"].get("items"):
                    gallery_order = [
                        item["media_id"]
                        for item in data["gallery_data"]["items"]
                    ]
                else:
                    gallery_order = list(data["media_metadata"].keys())

                for media_id in gallery_order:
                    if len(urls) >= 3:
                        break
                    item = data["media_metadata"].get(media_id, {})
                    if item.get("status") == "valid" and "s" in item:
                        raw_url = item["s"].get("u", "")
                        if raw_url:
                            urls.append(html.unescape(raw_url))

            # 3. 预览图（link 帖 / self 帖中嵌入图片）
            if not urls and "preview" in data:
                try:
                    raw_url = data["preview"]["images"][0]["source"]["url"]
                    urls.append(html.unescape(raw_url))
                except (KeyError, IndexError):
                    pass

        except Exception as e:
            logger.debug(f"提取图片 URL 时出现异常（已忽略）: {e}")

        return urls[:3]


if __name__ == "__main__":
    # 测试代码（无需配置）
    # 如需代理，传入: RedditCollector({"proxy": "http://127.0.0.1:7890"})
    collector = RedditCollector()
    posts = collector.collect_hot_posts("ThinkingDeeplyAI", limit=3)

    if posts:
        for i, post in enumerate(posts, 1):
            print(f"\n帖子 {i}:")
            print(f"  ID: {post['id']}")
            print(f"  类型: {post['post_type']}  置顶: {post['is_stickied']}")
            print(f"  标题: {post['title']}")
            print(f"  分数: {post['score']}  评论: {post['num_comments']}")
            print(f"  图片: {post['image_urls']}")
            print(f"  URL: {post['url']}")
            print(f"  时间: {post['created_date']}")
    else:
        print("未能收集到帖子，可能是网络问题（中国大陆用户需要代理）")
