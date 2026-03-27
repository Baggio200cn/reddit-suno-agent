"""
文案生成器（使用豆包 API - 火山方舟）
"""
import requests
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptGenerator:
    """文案生成器 - 使用火山方舟豆包 API"""

    def __init__(self, api_key: str, model_name: str = "doubao-seed-2-0-mini-260215"):
        """
        初始化文案生成器

        Args:
            api_key: 豆包 API Key
            model_name: 模型名称，默认 doubao-seed-2-0-mini-260215
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_article_title(self, posts: List[Dict[str, Any]]) -> str:
        """
        根据帖子生成文章标题

        Args:
            posts: 帖子列表

        Returns:
            生成的文章标题
        """
        # 提取帖子标题
        titles = [post.get("title", "") for post in posts[:5]]
        titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])

        system_prompt = """你是一位专业的自媒体编辑，擅长为技术文章生成吸引人的标题。
请根据提供的 Reddit 帖子标题，生成一个简洁有力、突出热点话题的文章标题。

要求：
1. 标题要简洁有力，突出热点话题
2. 使用中文
3. 标题长度在 20-50 字之间
4. 只返回标题，不要其他内容"""

        user_prompt = f"""请根据以下 Reddit 帖子标题，生成一个吸引人的文章标题：

{titles_text}

请生成标题："""

        try:
            response = self._call_api(system_prompt, user_prompt)
            title = response.strip()
            logger.info(f"生成的文章标题: {title}")
            return title
        except Exception as e:
            logger.error(f"生成文章标题失败: {e}")
            return f"Reddit 热门资讯精选 - {posts[0].get('created_date', '')}"

    def generate_article_summary(self, posts: List[Dict[str, Any]], title: str) -> str:
        """
        生成文章摘要

        Args:
            posts: 帖子列表
            title: 文章标题

        Returns:
            生成的文章摘要
        """
        # 提取帖子标题和内容
        posts_text = ""
        for i, post in enumerate(posts[:5], 1):
            posts_text += f"\n帖子 {i}: {post.get('title', '')}\n"
            posts_text += f"内容: {post.get('selftext', '')[:200]}...\n"

        system_prompt = """你是一位专业的自媒体编辑，擅长为技术文章生成吸引人的摘要。
请根据文章标题和帖子内容，生成一段吸引人的文章摘要。

要求：
1. 摘要要概括文章的主要内容
2. 使用中文
3. 摘要长度在 100-200 字之间
4. 只返回摘要内容，不要其他内容"""

        user_prompt = f"""请根据以下信息生成文章摘要：

文章标题：{title}

帖子内容：
{posts_text}

请生成摘要："""

        try:
            response = self._call_api(system_prompt, user_prompt)
            summary = response.strip()
            logger.info(f"生成的文章摘要: {summary}")
            return summary
        except Exception as e:
            logger.error(f"生成文章摘要失败: {e}")
            return "本期精选了 Reddit 上最热门的 AI 相关话题，带你了解最新趋势和深度思考。"

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用火山方舟 API

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            API 返回的文本
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            logger.info(f"调用火山方舟 API: {self.base_url}")
            logger.info(f"使用模型: {self.model_name}")

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 从响应中提取内容
            content = result["choices"][0]["message"]["content"]
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"调用 API 失败: {e}")
            raise


if __name__ == "__main__":
    # 测试代码
    api_key = "056d2839-c0d6-490c-9227-d7acb6a188fd"

    generator = ScriptGenerator(api_key)

    # 测试数据
    test_posts = [
        {
            "title": "AI 技术的最新突破",
            "selftext": "人工智能技术正在快速发展，尤其是大语言模型的突破，使得 AI 在自然语言处理方面取得了显著进展。GPT、BERT 等模型的出现，为各种应用场景带来了新的可能。",
            "created_date": "2024-01-01 00:00:00"
        },
        {
            "title": "深度学习模型的优化方法",
            "selftext": "如何优化深度学习模型的性能？本文分享了模型压缩、量化、知识蒸馏等技术的实践经验。",
            "created_date": "2024-01-01 01:00:00"
        }
    ]

    print("测试生成标题...")
    title = generator.generate_article_title(test_posts)
    print(f"标题: {title}")

    print("\n测试生成摘要...")
    summary = generator.generate_article_summary(test_posts, title)
    print(f"摘要: {summary}")
