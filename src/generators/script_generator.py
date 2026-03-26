"""
文案生成器（使用豆包 API）
"""
import requests
import json
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptGenerator:
    """文案生成器"""

    def __init__(self, api_key: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"):
        """
        初始化文案生成器

        Args:
            api_key: 豆包 API Key
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def generate_article_title(self, posts: List[Dict[str, Any]]) -> str:
        """
        根据帖子生成文章标题

        Args:
            posts: 帖子列表

        Returns:
            生成的文章标题
        """
        prompt = f"""请根据以下 5 条 Reddit 帖子，生成一个吸引人的文章标题。

帖子列表：
{json.dumps(posts, ensure_ascii=False, indent=2)}

要求：
1. 标题要简洁有力，突出热点话题
2. 使用中文
3. 标题长度在 20-50 字之间
4. 只返回标题，不要其他内容
"""

        try:
            response = self._call_api(prompt)
            title = response.strip()
            logger.info(f"生成的文章标题: {title}")
            return title
        except Exception as e:
            logger.error(f"生成文章标题失败: {e}")
            return f"Reddit 热门资讯精选 - {posts[0]['created_date']}"

    def generate_article_summary(self, posts: List[Dict[str, Any]], title: str) -> str:
        """
        生成文章摘要

        Args:
            posts: 帖子列表
            title: 文章标题

        Returns:
            生成的文章摘要
        """
        prompt = f"""请根据以下文章标题和 Reddit 帖子列表，生成一段吸引人的文章摘要。

文章标题：{title}

帖子列表：
{json.dumps(posts, ensure_ascii=False, indent=2)}

要求：
1. 摘要要概括文章的主要内容
2. 使用中文
3. 摘要长度在 100-200 字之间
4. 只返回摘要内容，不要其他内容
"""

        try:
            response = self._call_api(prompt)
            summary = response.strip()
            logger.info(f"生成的文章摘要: {summary}")
            return summary
        except Exception as e:
            logger.error(f"生成文章摘要失败: {e}")
            return "本期精选了 Reddit 上最热门的 AI 相关话题，带你了解最新趋势和深度思考。"

    def _call_api(self, prompt: str) -> str:
        """
        调用豆包 API

        Args:
            prompt: 提示词

        Returns:
            API 返回的文本
        """
        payload = {
            "model": "doubao-pro-32k",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"调用 API 失败: {e}")
            raise


if __name__ == "__main__":
    # 测试代码
    config = {
        "api_key": "your_api_key"
    }

    generator = ScriptGenerator(config["api_key"])

    # 测试数据
    test_posts = [
        {
            "title": "AI 技术的最新突破",
            "score": 1000,
            "created_date": "2024-01-01 00:00:00"
        },
        {
            "title": "深度学习模型的优化方法",
            "score": 800,
            "created_date": "2024-01-01 01:00:00"
        }
    ]

    title = generator.generate_article_title(test_posts)
    print(f"标题: {title}")

    summary = generator.generate_article_summary(test_posts, title)
    print(f"摘要: {summary}")
