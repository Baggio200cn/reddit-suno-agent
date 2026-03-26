"""
主程序入口
"""
import argparse
import sys
import os
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_loader import config_loader
from src.collectors.reddit_collector import RedditCollector
from src.generators.script_generator import ScriptGenerator
from src.generators.music_generator import MusicGenerator
from src.generators.article_generator import ArticleGenerator
from src.publishers.github_publisher import GitHubPublisher
from src.publishers.email_notifier import EmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RedditSunoAgent:
    """Reddit Suno 音乐自媒体代理"""

    def __init__(self):
        """初始化代理"""
        self.config = config_loader
        self.reddit_collector = None
        self.script_generator = None
        self.music_generator = None
        self.article_generator = None
        self.github_publisher = None
        self.email_notifier = None

    def initialize(self):
        """初始化所有组件"""
        try:
            logger.info("初始化 Reddit Suno 音乐自媒体代理...")

            # 加载配置
            reddit_config = self.config.get_reddit_config()
            suno_config = self.config.get_suno_config()
            doubao_config = self.config.get_doubao_config()
            email_config = self.config.get_email_config()
            github_config = self.config.get_github_config()

            # 初始化组件
            self.reddit_collector = RedditCollector(reddit_config)
            self.script_generator = ScriptGenerator(doubao_config["api_key"])
            self.music_generator = MusicGenerator(suno_config["api_id"], suno_config["token"])
            self.article_generator = ArticleGenerator()
            self.github_publisher = GitHubPublisher(github_config, project_dir=".")
            self.email_notifier = EmailNotifier(email_config)

            logger.info("初始化完成")

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    def run(self):
        """运行主流程"""
        try:
            logger.info("=" * 50)
            logger.info("开始执行任务")
            logger.info("=" * 50)

            # 1. 搜集 Reddit 帖子
            logger.info("步骤 1/6: 搜集 Reddit 帖子...")
            posts = self.reddit_collector.collect_hot_posts("ThinkingDeeplyAI", limit=5)
            if not posts:
                raise Exception("未能收集到任何帖子")

            # 2. 生成文章标题和摘要
            logger.info("步骤 2/6: 生成文章标题和摘要...")
            title = self.script_generator.generate_article_title(posts)
            summary = self.script_generator.generate_article_summary(posts, title)

            # 3. 生成背景音乐
            logger.info("步骤 3/6: 生成背景音乐...")
            music_idea = f"一首轻松愉快的电子音乐，适合作为'{title}'的背景音乐"
            music_path = self.music_generator.generate_music(music_idea, style="electronic")

            if not music_path:
                logger.warning("音乐生成失败，继续生成文章（无背景音乐）")
                music_path = None

            # 4. 生成 Markdown 文章
            logger.info("步骤 4/6: 生成 Markdown 文章...")
            article_path = self.article_generator.generate_article(
                title=title,
                summary=summary,
                posts=posts,
                music_path=music_path
            )

            # 5. 推送到 GitHub
            logger.info("步骤 5/6: 推送到 GitHub...")
            commit_message = f"发布文章: {title} - {datetime.now().strftime('%Y-%m-%d')}"
            self.github_publisher.push_to_github(commit_message)

            # 6. 发送通知邮件
            logger.info("步骤 6/6: 发送通知邮件...")
            self.email_notifier.send_success_notification(
                article_title=title,
                article_path=article_path,
                music_path=music_path
            )

            logger.info("=" * 50)
            logger.info("✅ 任务执行完成！")
            logger.info("=" * 50)
            logger.info(f"文章路径: {article_path}")
            if music_path:
                logger.info(f"音乐路径: {music_path}")
            logger.info(f"GitHub 仓库: https://github.com/{self.config.get_github_config()['repo']}")

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            logger.error(f"错误详情: {str(e)}", exc_info=True)

            # 发送失败通知
            try:
                self.email_notifier.send_failure_notification(str(e))
            except:
                pass

            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Reddit Suno 音乐自媒体系统")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="启用定时任务模式"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试模式（不实际调用 API）"
    )
    args = parser.parse_args()

    if args.schedule:
        # 定时任务模式
        logger.info("启动定时任务模式...")

        schedule_config = config_loader.load_schedule()

        if not schedule_config["enabled"]:
            logger.info("定时任务未启用，退出")
            return

        # 创建调度器
        scheduler = BlockingScheduler(timezone=pytz.timezone(schedule_config["timezone"]))

        # 添加定时任务
        scheduler.add_job(
            run_once,
            'cron',
            hour=schedule_config["cron"]["hour"],
            minute=schedule_config["cron"]["minute"],
            id='reddit_suno_task',
            name='Reddit Suno 音乐自媒体任务'
        )

        logger.info(f"定时任务已设置：每天 {schedule_config['cron']['hour']:02d}:{schedule_config['cron']['minute']:02d} 执行")

        # 启动调度器
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("定时任务已停止")
            scheduler.shutdown()
    else:
        # 单次执行模式
        run_once()


def run_once():
    """单次执行任务"""
    agent = RedditSunoAgent()

    try:
        agent.initialize()
        agent.run()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
