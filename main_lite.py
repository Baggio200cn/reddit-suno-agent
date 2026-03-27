"""
轻量版主程序（跳过音乐生成）
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
from src.publishers.github_publisher import GitHubPublisher
from src.publishers.email_notifier import EmailNotifier

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


class RedditSunoAgentLite:
    """Reddit 音乐自媒体代理（轻量版 - 无音乐生成）"""

    def __init__(self):
        """初始化代理"""
        self.config = config_loader
        self.reddit_collector = None
        self.script_generator = None
        self.article_generator = None
        self.github_publisher = None
        self.email_notifier = None

    def initialize(self):
        """初始化所有组件"""
        try:
            logger.info("初始化 Reddit Suno 音乐自媒体代理（轻量版）...")

            # 加载配置
            reddit_config = self.config.get_reddit_config()
            doubao_config = self.config.get_doubao_config()
            email_config = self.config.get_email_config()
            github_config = self.config.get_github_config()

            # 初始化组件
            self.reddit_collector = RedditCollector(reddit_config)
            self.script_generator = ScriptGenerator(doubao_config["api_key"])
            self.article_generator = ArticleGenerator()
            self.github_publisher = GitHubPublisher(github_config, project_dir=".")
            self.email_notifier = EmailNotifier(email_config)

            logger.info("初始化完成（轻量版，不包含音乐生成）")

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    def run(self):
        """运行主流程（轻量版）"""
        try:
            logger.info("=" * 50)
            logger.info("开始执行任务（轻量版）")
            logger.info("=" * 50)

            # 1. 搜集 Reddit 帖子
            logger.info("步骤 1/5: 搜集 Reddit 帖子...")
            posts = self.reddit_collector.collect_hot_posts("ThinkingDeeplyAI", limit=5)
            if not posts:
                raise Exception("未能收集到任何帖子")

            # 2. 生成文章标题和摘要
            logger.info("步骤 2/5: 生成文章标题和摘要...")
            title = self.script_generator.generate_article_title(posts)
            summary = self.script_generator.generate_article_summary(posts, title)

            # 3. 跳过音乐生成
            logger.info("步骤 3/5: 跳过音乐生成（轻量版）...")
            music_path = None

            # 4. 生成 Markdown 文章
            logger.info("步骤 4/5: 生成 Markdown 文章...")
            article_path = self.article_generator.generate_article(
                title=title,
                summary=summary,
                posts=posts,
                music_path=music_path  # 不使用音乐
            )

            # 5. 推送到 GitHub
            logger.info("步骤 5/5: 推送到 GitHub...")
            commit_message = f"发布文章: {title} - {datetime.now().strftime('%Y-%m-%d')}"
            self.github_publisher.push_to_github(commit_message)

            # 6. 发送通知邮件（如果启用）
            if self.email_notifier.enabled:
                logger.info("步骤 6/5: 发送通知邮件...")
                self.email_notifier.send_success_notification(
                    article_title=title,
                    article_path=article_path,
                    music_path=music_path
                )

            logger.info("=" * 50)
            logger.info("✅ 任务执行完成！")
            logger.info("=" * 50)
            logger.info(f"文章路径: {article_path}")
            logger.info(f"GitHub 仓库: https://github.com/{self.config.get_github_config()['repo']}")

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            logger.error(f"错误详情: {str(e)}", exc_info=True)

            # 发送失败通知
            try:
                if self.email_notifier.enabled:
                    self.email_notifier.send_failure_notification(str(e))
            except:
                pass

            raise


def main():
    """主函数"""
    agent = RedditSunoAgentLite()

    try:
        agent.initialize()
        agent.run()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
