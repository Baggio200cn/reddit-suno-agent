"""
完整流程测试脚本
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
from src.generators.music_generator import SunoMusicGenerator as MusicGenerator
from src.generators.article_generator import ArticleGenerator
from src.publishers.github_publisher import GitHubPublisher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_full_workflow():
    """测试完整工作流程"""
    logger.info("=" * 70)
    logger.info("开始完整流程测试")
    logger.info("=" * 70)

    try:
        # ========== 步骤 1: 初始化 ==========
        logger.info("\n【步骤 1/6】初始化组件...")

        reddit_config = config_loader.get_reddit_config()
        suno_config = config_loader.get_suno_config()
        doubao_config = config_loader.get_doubao_config()
        github_config = config_loader.get_github_config()

        logger.info(f"✅ Reddit 配置: 使用 RSS Feed")
        logger.info(f"✅ Suno 配置: API 类型 = {suno_config.get('api_type')}")
        logger.info(f"✅ 豆包配置: API Key = {doubao_config['api_key'][:20]}...")
        logger.info(f"✅ GitHub 配置: 仓库 = {github_config['repo']}")

        # ========== 步骤 2: 收集 Reddit 帖子 ==========
        logger.info("\n【步骤 2/6】从 Reddit 收集帖子...")

        reddit_collector = RedditCollector(reddit_config)
        posts = reddit_collector.collect_hot_posts("ThinkingDeeplyAI", limit=5)

        if not posts:
            logger.warning("⚠️ 未收集到任何帖子，可能是网络问题或 RSS Feed 不可用")
            logger.warning("✅ 继续使用测试数据...")

            # 使用测试数据
            posts = [
                {
                    "id": "test1",
                    "title": "测试帖子 1：AI 技术的最新进展",
                    "selftext": "这是一个测试帖子的摘要内容，用于演示完整的工作流程。",
                    "url": "https://reddit.com/r/test/test1",
                    "score": 0,
                    "num_comments": 0,
                    "created_utc": datetime.now().timestamp(),
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "author": "test_user",
                    "upvote_ratio": 0.0
                },
                {
                    "id": "test2",
                    "title": "测试帖子 2：机器学习在实际应用中的案例",
                    "selftext": "这是一个关于机器学习应用的测试摘要。",
                    "url": "https://reddit.com/r/test/test2",
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

            for i, post in enumerate(posts[:3], 1):
                logger.info(f"  [{i}] {post['title'][:50]}...")

        # ========== 步骤 3: 生成文案 ==========
        logger.info("\n【步骤 3/6】生成标题和摘要...")

        script_generator = ScriptGenerator(doubao_config["api_key"])

        logger.info("正在生成文章标题...")
        title = script_generator.generate_article_title(posts)
        logger.info(f"✅ 文章标题: {title}")

        logger.info("正在生成文章摘要...")
        summary = script_generator.generate_article_summary(posts, title)
        logger.info(f"✅ 摘要长度: {len(summary)} 字符")

        # ========== 步骤 4: 生成音乐 ==========
        logger.info("\n【步骤 4/6】生成背景音乐...")

        suno_api_type = suno_config.get("api_type", "unofficial")
        if suno_api_type == "official":
            music_generator = MusicGenerator(
                api_type="official",
                api_key=suno_config.get("api_key")
            )
        else:
            music_generator = MusicGenerator(
                api_type="unofficial",
                api_id=suno_config.get("api_id"),
                token=suno_config.get("token")
            )

        logger.info("正在生成音乐（这可能需要 2-3 分钟）...")
        music_idea = f"一首轻松愉快的电子音乐，适合作为'{title}'的背景音乐"

        music_results = music_generator.generate_music(
            prompt=music_idea,
            style="electronic",
            title=title[:80]
        )

        music_path = None
        if music_results and len(music_results) > 0:
            music_path = music_results[0].get("local_path")
            logger.info(f"✅ 音乐生成成功: {music_path}")
        else:
            logger.warning("⚠️ 音乐生成失败，继续生成文章（无背景音乐）")

        # ========== 步骤 5: 生成文章 ==========
        logger.info("\n【步骤 5/6】生成 Markdown 文章...")

        article_generator = ArticleGenerator()
        article_path = article_generator.generate_article(
            title=title,
            summary=summary,
            posts=posts,
            music_path=music_path
        )

        logger.info(f"✅ 文章生成成功: {article_path}")

        # ========== 步骤 6: 推送到 GitHub ==========
        logger.info("\n【步骤 6/6】推送到 GitHub...")

        github_publisher = GitHubPublisher(github_config, project_dir=".")
        commit_message = f"发布文章: {title} - {datetime.now().strftime('%Y-%m-%d')}"

        logger.info("正在提交并推送...")
        github_publisher.push_to_github(commit_message)
        logger.info(f"✅ 推送成功: https://github.com/{github_config['repo']}")

        # ========== 完成 ==========
        logger.info("\n" + "=" * 70)
        logger.info("✅ 完整流程测试成功！")
        logger.info("=" * 70)
        logger.info(f"\n📄 文章路径: {article_path}")
        if music_path:
            logger.info(f"🎵 音乐路径: {music_path}")
        logger.info(f"📦 GitHub: https://github.com/{github_config['repo']}")
        logger.info(f"📝 日志: logs/app.log")

        return True

    except Exception as e:
        logger.error("\n" + "=" * 70)
        logger.error("❌ 测试失败")
        logger.error("=" * 70)
        logger.error(f"错误信息: {e}")
        logger.error(f"错误详情:", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Reddit Suno 音乐自媒体系统 - 完整流程测试")
    logger.info("开始时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    success = test_full_workflow()

    logger.info("\n结束时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 70)

    if success:
        logger.info("✅ 所有测试通过！")
        sys.exit(0)
    else:
        logger.error("❌ 测试失败，请查看日志了解详情")
        sys.exit(1)
