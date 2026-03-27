"""
快速测试脚本（不生成音乐）
"""
import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_loader import config_loader
from src.collectors.reddit_collector import RedditCollector
from src.generators.script_generator import ScriptGenerator
from src.generators.article_generator import ArticleGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_quick():
    """快速测试（不生成音乐）"""
    logger.info("=" * 70)
    logger.info("快速测试 - 不生成音乐")
    logger.info("=" * 70)

    try:
        # ========== 步骤 1: 收集 Reddit 帖子 ==========
        logger.info("\n【步骤 1/4】从 Reddit 收集帖子...")

        reddit_collector = RedditCollector()
        posts = reddit_collector.collect_hot_posts("ThinkingDeeplyAI", limit=3)

        if not posts:
            logger.warning("⚠️ 未收集到帖子，使用测试数据")
            posts = [
                {
                    "id": "test1",
                    "title": "AI 技术的最新进展",
                    "selftext": "这是一个测试帖子。",
                    "url": "https://reddit.com/r/test/test1",
                    "score": 0,
                    "num_comments": 0,
                    "created_utc": datetime.now().timestamp(),
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": "test_user",
                    "upvote_ratio": 0.0
                }
            ]
        else:
            logger.info(f"✅ 成功收集 {len(posts)} 条帖子")
            for i, post in enumerate(posts, 1):
                logger.info(f"  [{i}] {post['title']}")

        # ========== 步骤 2: 生成文案 ==========
        logger.info("\n【步骤 2/4】生成标题和摘要...")

        doubao_config = config_loader.get_doubao_config()
        script_generator = ScriptGenerator(doubao_config["api_key"])

        logger.info("正在生成文章标题...")
        title = script_generator.generate_article_title(posts)
        logger.info(f"✅ 文章标题: {title}")

        logger.info("正在生成文章摘要...")
        summary = script_generator.generate_article_summary(posts, title)
        logger.info(f"✅ 摘要长度: {len(summary)} 字符")

        # ========== 步骤 3: 生成文章 ==========
        logger.info("\n【步骤 3/4】生成 Markdown 文章...")

        article_generator = ArticleGenerator()
        article_path = article_generator.generate_article(
            title=title,
            summary=summary,
            posts=posts,
            music_path=None  # 不使用音乐
        )

        logger.info(f"✅ 文章生成成功: {article_path}")

        # ========== 完成 ==========
        logger.info("\n" + "=" * 70)
        logger.info("✅ 快速测试成功！")
        logger.info("=" * 70)
        logger.info(f"📄 文章路径: {article_path}")

        return True

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        logger.error("错误详情:", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_quick()
    sys.exit(0 if success else 1)
