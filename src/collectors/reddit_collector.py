"""
Reddit 数据收集器 - 使用 RSS Feed
"""
import feedparser
from typing import List, Dict, Any
from datetime import datetime
import logging
import html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedditCollector:
    """Reddit 数据收集器 - 使用 RSS Feed"""

    def __init__(self, config: Dict[str, str] = None):
        """
        初始化 Reddit 收集器（使用 RSS Feed，无需 API 凭证）

        Args:
            config: 配置字典（RSS Feed 方式不需要，保留参数以兼容接口）
        """
        # RSS Feed 不需要配置，保留参数以兼容接口
        self.config = config or {}

    def collect_hot_posts(self, subreddit: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        从指定 subreddit 收集热门帖子（使用 RSS Feed）

        Args:
            subreddit: subreddit 名称（不含 r/）
            limit: 收集帖子数量

        Returns:
            帖子列表，每个帖子包含 id, title, selftext, url, created_utc 等信息
        """
        try:
            logger.info(f"开始从 r/{subreddit} 的 RSS Feed 收集热门帖子...")

            # 构建 RSS Feed URL
            rss_url = f"https://www.reddit.com/r/{subreddit}/.rss"
            logger.info(f"RSS Feed URL: {rss_url}")

            # 解析 RSS Feed
            feed = feedparser.parse(rss_url)

            # 检查解析状态
            if feed.bozo:
                logger.warning(f"RSS Feed 解析可能有警告: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning("RSS Feed 中没有找到帖子")
                # 返回空列表而不是抛出异常
                return []

            posts = []
            for entry in feed.entries[:limit]:
                # 解析帖子内容
                title = entry.get('title', '')
                title = html.unescape(title)  # 解码 HTML 实体

                # 获取摘要内容
                content = entry.get('summary', '')
                content = html.unescape(content)

                # 移除 HTML 标签（简单处理）
                import re
                content = re.sub('<[^<]+?>', '', content)

                # 获取帖子 ID（从 URL 中提取）
                post_id = entry.get('id', '').split('/')[-1]
                if not post_id:
                    post_id = entry.link.split('/')[-1]

                post = {
                    "id": post_id,
                    "title": title,
                    "selftext": content,  # RSS 只有摘要，没有完整内容
                    "url": entry.link,
                    "score": 0,  # RSS 不提供点赞数
                    "num_comments": 0,  # RSS 不提供评论数
                    "created_utc": datetime.now().timestamp(),  # RSS 可能没有时间戳，使用当前时间
                    "created_date": entry.get('published', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "author": entry.get('author', 'Unknown'),
                    "upvote_ratio": 0.0  # RSS 不提供点赞率
                }
                posts.append(post)

            logger.info(f"成功收集 {len(posts)} 条帖子")
            return posts

        except Exception as e:
            logger.error(f"收集帖子失败: {e}")
            # 返回空列表而不是抛出异常
            return []


if __name__ == "__main__":
    # 测试代码（无需配置）
    collector = RedditCollector()
    posts = collector.collect_hot_posts("ThinkingDeeplyAI", limit=3)

    if posts:
        for i, post in enumerate(posts, 1):
            print(f"\n帖子 {i}:")
            print(f"ID: {post['id']}")
            print(f"标题: {post['title']}")
            print(f"内容: {post['selftext'][:100]}...")
            print(f"URL: {post['url']}")
            print(f"时间: {post['created_date']}")
            print(f"作者: {post['author']}")
    else:
        print("未能收集到帖子，可能是网络问题或 RSS Feed 不可用")
