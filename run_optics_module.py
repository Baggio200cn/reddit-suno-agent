"""
光学模块真实运行脚本
演示光学收集器的实际工作流程
"""
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.collectors.optics_news_collector import OpticsNewsCollector

# 配置日志
import logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/optics_run.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("光学/机器视觉模块 - 真实运行演示")
    logger.info("=" * 60)
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建收集器
    collector = OpticsNewsCollector()

    # 收集新闻
    logger.info("\n步骤 1: 收集光学/机器视觉新闻...")
    news_list = collector.collect_all(total_limit=5)

    if not news_list:
        logger.error("未能收集到任何新闻")
        return False

    logger.info(f"\n✅ 成功收集到 {len(news_list)} 条新闻\n")

    # 保存到文件
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"output/optics/{today}"
    os.makedirs(output_dir, exist_ok=True)

    # 保存原始数据
    output_file = os.path.join(output_dir, "news.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)
    logger.info(f"原始数据已保存到: {output_file}")

    # 生成 Markdown 文件
    md_file = os.path.join(output_dir, "news.md")
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# 光学/机器视觉新闻事实调查 - {today}\n\n")
        f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        for i, news in enumerate(news_list, 1):
            f.write(f"## {i}. {news['title']}\n\n")
            f.write(f"**来源**: {news['source']}\n\n")
            f.write(f"**链接**: [{news['url']}]({news['url']})\n\n")
            f.write(f"**摘要**:\n\n{news['summary']}\n\n")
            f.write("---\n\n")

    logger.info(f"Markdown 文件已保存到: {md_file}")

    # 显示结果
    logger.info("\n" + "=" * 60)
    logger.info("收集结果预览:")
    logger.info("=" * 60)

    for i, news in enumerate(news_list, 1):
        logger.info(f"\n新闻 {i}:")
        logger.info(f"  来源: {news['source']}")
        logger.info(f"  标题: {news['title']}")
        logger.info(f"  摘要: {news['summary'][:100]}...")
        logger.info(f"  链接: {news['url']}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 光学模块运行完成！")
    logger.info("=" * 60)
    logger.info(f"\n输出目录: {output_dir}")
    logger.info(f"- 原始数据: news.json")
    logger.info(f"- Markdown 文件: news.md")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
