"""
光学/机器视觉新闻收集器 - 从多个来源爬取科技前沿
"""
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
import feedparser
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpticsNewsCollector:
    """光学/机器视觉新闻收集器"""

    def __init__(self):
        """初始化新闻收集器"""
        self.sources = {
            "arXiv": "https://export.arxiv.org/rss/cs.CV",  # 计算机视觉
            "MIT Tech Review": "https://www.technologyreview.com/feed/",
            "Photonics Media": "https://www.photonics.com/rss",
        }

        # AI 相关关键词
        self.ai_keywords = [
            "AI", "artificial intelligence", "machine learning", "deep learning",
            "neural network", "computer vision", "image recognition",
            "人工智能", "机器学习", "深度学习", "神经网络", "计算机视觉",
            "图像识别", "目标检测", "语义分割", "光场", "成像",
            "optical", "vision", "imaging", "lens", "camera", "sensor"
        ]

    def is_ai_related(self, text: str) -> bool:
        """
        检查内容是否与 AI 相关

        Args:
            text: 文本内容

        Returns:
            是否与 AI 相关
        """
        text_lower = text.lower()
        for keyword in self.ai_keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    def collect_from_arxiv(self, limit: int = 5) -> List[Dict]:
        """
        从 arXiv 收集论文

        Args:
            limit: 收集数量

        Returns:
            论文列表
        """
        papers = []
        try:
            logger.info("正在从 arXiv 收集论文...")
            url = "https://export.arxiv.org/api/query?"
            params = {
                "search_query": "cat:cs.CV OR cat:cs.AI",
                "start": 0,
                "max_results": limit * 2  # 多获取一些，筛选后再返回
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # 解析 XML 响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                if len(papers) >= limit:
                    break

                title = entry.find("{http://www.w3.org/2005/Atom}title").text
                summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
                link = entry.find("{http://www.w3.org/2005/Atom}id").text

                # 检查是否与 AI 相关
                if self.is_ai_related(title + " " + summary):
                    papers.append({
                        "source": "arXiv",
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })

            logger.info(f"从 arXiv 收集到 {len(papers)} 篇论文")

        except Exception as e:
            logger.error(f"从 arXiv 收集失败: {e}")

        return papers

    def collect_from_rss(self, source_name: str, rss_url: str, limit: int = 2) -> List[Dict]:
        """
        从 RSS Feed 收集新闻

        Args:
            source_name: 来源名称
            rss_url: RSS URL
            limit: 收集数量

        Returns:
            新闻列表
        """
        news = []
        try:
            logger.info(f"正在从 {source_name} 收集新闻...")
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:limit * 2]:  # 多获取一些
                if len(news) >= limit:
                    break

                title = entry.get('title', '')
                summary = entry.get('summary', '')
                link = entry.get('link', '')

                # 移除 HTML 标签
                summary = re.sub('<[^<]+?>', '', summary)

                # 检查是否与 AI 相关
                if self.is_ai_related(title + " " + summary):
                    news.append({
                        "source": source_name,
                        "title": title,
                        "summary": summary[:500],  # 限制长度
                        "url": link,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })

            logger.info(f"从 {source_name} 收集到 {len(news)} 条新闻")

        except Exception as e:
            logger.error(f"从 {source_name} 收集失败: {e}")

        return news

    def collect_all(self, total_limit: int = 5) -> List[Dict]:
        """
        从所有来源收集新闻

        Args:
            total_limit: 总共收集数量

        Returns:
            新闻列表
        """
        all_news = []

        # 从 arXiv 收集
        arxiv_papers = self.collect_from_arxiv(limit=2)
        all_news.extend(arxiv_papers)

        # 从其他来源收集
        limit_per_source = max(1, (total_limit - len(all_news)) // 3)

        for source_name, rss_url in self.sources.items():
            if source_name == "arXiv":
                continue

            if len(all_news) >= total_limit:
                break

            news = self.collect_from_rss(source_name, rss_url, limit=limit_per_source)
            all_news.extend(news)

        # 按来源分组
        all_news = all_news[:total_limit]

        logger.info(f"总共收集到 {len(all_news)} 条新闻")
        return all_news


if __name__ == "__main__":
    # 测试代码
    collector = OpticsNewsCollector()
    news = collector.collect_all(total_limit=5)

    if news:
        for i, item in enumerate(news, 1):
            print(f"\n新闻 {i}:")
            print(f"  来源: {item['source']}")
            print(f"  标题: {item['title']}")
            print(f"  摘要: {item['summary'][:100]}...")
            print(f"  链接: {item['url']}")
