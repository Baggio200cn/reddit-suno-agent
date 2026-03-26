"""
Reddit 数据收集器
"""
import praw
from typing import List, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedditCollector:
    """Reddit 数据收集器"""

    def __init__(self, config: Dict[str, str]):
        """
        初始化 Reddit 收集器

        Args:
            config: Reddit 配置字典，包含 client_id, client_secret, user_agent
        """
        self.reddit = praw.Reddit(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            user_agent=config["user_agent"],
            read_only=True
        )

    def collect_hot_posts(self, subreddit: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        从指定 subreddit 收集热门帖子

        Args:
            subreddit: subreddit 名称（不含 r/）
            limit: 收集帖子数量

        Returns:
            帖子列表，每个帖子包含 id, title, selftext, url, score, created_utc 等信息
        """
        try:
            logger.info(f"开始从 r/{subreddit} 收集热门帖子...")

            posts = []
            subreddit_obj = self.reddit.subreddit(subreddit)

            for submission in subreddit_obj.hot(limit=limit):
                post = {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "url": submission.url,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "created_date": datetime.fromtimestamp(submission.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "upvote_ratio": submission.upvote_ratio
                }
                posts.append(post)

            logger.info(f"成功收集 {len(posts)} 条帖子")
            return posts

        except Exception as e:
            logger.error(f"收集帖子失败: {e}")
            raise


if __name__ == "__main__":
    # 测试代码
    config = {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "user_agent": "test_bot/1.0 by your_username"
    }

    collector = RedditCollector(config)
    posts = collector.collect_hot_posts("ThinkingDeeplyAI", limit=3)

    for i, post in enumerate(posts, 1):
        print(f"\n帖子 {i}:")
        print(f"标题: {post['title']}")
        print(f"分数: {post['score']}")
        print(f"评论数: {post['num_comments']}")
        print(f"时间: {post['created_date']}")
        print(f"作者: {post['author']}")
