"""
组件独立测试脚本
"""
import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_loader import config_loader
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


def test_components():
    """测试各个组件"""
    logger.info("=" * 70)
    logger.info("组件独立测试")
    logger.info("=" * 70)

    # 测试数据
    test_posts = [
        {
            "id": "1",
            "title": "AI 技术的最新进展：大语言模型的突破",
            "selftext": "人工智能技术正在快速发展，尤其是大语言模型的突破，使得 AI 在自然语言处理方面取得了显著进展。GPT、BERT 等模型的出现，为各种应用场景带来了新的可能。",
            "url": "https://reddit.com/r/test/post1",
            "score": 100,
            "num_comments": 50,
            "created_utc": datetime.now().timestamp(),
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "author": "tech_user",
            "upvote_ratio": 0.9
        },
        {
            "id": "2",
            "title": "机器学习在医疗领域的应用案例",
            "selftext": "机器学习技术正在改变医疗行业，从疾病诊断到药物研发，AI 都在发挥着重要作用。本文将介绍几个成功的应用案例。",
            "url": "https://reddit.com/r/test/post2",
            "score": 85,
            "num_comments": 30,
            "created_utc": datetime.now().timestamp(),
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "author": "med_ai",
            "upvote_ratio": 0.85
        },
        {
            "id": "3",
            "title": "深度学习模型的优化策略",
            "selftext": "如何优化深度学习模型的性能？本文分享了模型压缩、量化、知识蒸馏等技术的实践经验。",
            "url": "https://reddit.com/r/test/post3",
            "score": 120,
            "num_comments": 45,
            "created_utc": datetime.now().timestamp(),
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "author": "ml_expert",
            "upvote_ratio": 0.92
        }
    ]

    try:
        # ========== 测试 1: 豆包文案生成 ==========
        logger.info("\n【测试 1】豆包文案生成...")

        doubao_config = config_loader.get_doubao_config()
        logger.info(f"API Key: {doubao_config['api_key'][:20]}...")

        script_generator = ScriptGenerator(doubao_config["api_key"])

        logger.info("正在生成文章标题...")
        title = script_generator.generate_article_title(test_posts)
        logger.info(f"✅ 标题: {title}")

        logger.info("正在生成文章摘要...")
        summary = script_generator.generate_article_summary(test_posts, title)
        logger.info(f"✅ 摘要: {summary[:200]}...")

        # ========== 测试 2: 文章生成 ==========
        logger.info("\n【测试 2】Markdown 文章生成...")

        article_generator = ArticleGenerator()
        article_path = article_generator.generate_article(
            title=title,
            summary=summary,
            posts=test_posts,
            music_path=None
        )

        logger.info(f"✅ 文章已生成: {article_path}")

        # ========== 读取文章内容 ==========
        logger.info("\n【验证】读取生成的文章...")
        with open(article_path, 'r', encoding='utf-8') as f:
            article_content = f.read()

        logger.info(f"文章长度: {len(article_content)} 字符")
        logger.info(f"\n文章预览（前500字符）:\n{article_content[:500]}")

        # ========== 完成 ==========
        logger.info("\n" + "=" * 70)
        logger.info("✅ 组件测试成功！")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        logger.error("错误详情:", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_components()
    sys.exit(0 if success else 1)
