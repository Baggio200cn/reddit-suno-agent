"""
图片处理器 - 使用豆包视觉模型将图片内容转换为中文描述
"""
import logging
import time
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_VISION_MODEL = "doubao-vision-pro-32k-241265"
_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
_DESCRIBE_PROMPT = (
    "请详细描述这张图片的内容，用中文回答。"
    "重点说明图片中展示的核心概念、技术要点、图表数据或视觉信息，100字以内。"
)


class ImageProcessor:
    """图片处理器 - 调用豆包视觉 API 生成中文图片描述"""

    def __init__(
        self,
        api_key: str,
        vision_model: str = _DEFAULT_VISION_MODEL,
        proxy: Optional[str] = None,
        delay_between_calls: float = 1.0,
    ):
        """
        初始化图片处理器

        Args:
            api_key: 豆包 API Key（与文案生成器共用同一 key）
            vision_model: 视觉模型名称，默认 doubao-vision-pro-32k-241265
            proxy: 可选 HTTP 代理地址，如 "http://127.0.0.1:7890"
            delay_between_calls: 每次视觉 API 调用之间的间隔秒数（避免限流）
        """
        self.api_key = api_key
        self.vision_model = vision_model
        self.delay_between_calls = delay_between_calls
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        logger.info(f"图片处理器初始化完成，使用模型: {vision_model}")

    def describe_image(self, image_url: str) -> Optional[str]:
        """
        调用豆包视觉 API 描述图片内容（中文）

        Args:
            image_url: 图片 URL（直接传给视觉 API，无需下载到本地）

        Returns:
            图片的中文描述文本，失败时返回 None
        """
        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                        {
                            "type": "text",
                            "text": _DESCRIBE_PROMPT,
                        },
                    ],
                }
            ],
            "max_tokens": 300,
        }

        try:
            logger.info(f"调用视觉 API 描述图片: {image_url[:80]}...")
            resp = requests.post(
                _API_URL,
                headers=self.headers,
                json=payload,
                proxies=self.proxies,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            description = result["choices"][0]["message"]["content"].strip()
            logger.info(f"图片描述成功（{len(description)} 字）")
            return description
        except requests.exceptions.RequestException as e:
            logger.warning(f"视觉 API 请求失败，跳过该图片: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.warning(f"视觉 API 响应格式异常，跳过该图片: {e}")
            return None

    def process_post_images(self, post: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        处理单个帖子的所有图片

        Args:
            post: 帖子字典，需包含 image_urls 字段

        Returns:
            图片描述列表，每项格式：{"url": "...", "description": "..."}
            description 为 None 的图片会被排除
        """
        image_urls = post.get("image_urls", [])
        if not image_urls:
            return []

        results = []
        for i, url in enumerate(image_urls):
            if i > 0:
                time.sleep(self.delay_between_calls)
            description = self.describe_image(url)
            if description:
                results.append({"url": url, "description": description})
            else:
                logger.warning(f"帖子「{post.get('title', '')}」的第 {i+1} 张图片描述失败，跳过")

        return results

    def process_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理帖子列表中所有帖子的图片，将 image_descriptions 字段写入每个帖子

        Args:
            posts: 帖子列表（会在原地追加 image_descriptions 字段）

        Returns:
            追加了 image_descriptions 字段的帖子列表（同一对象引用）
        """
        total_images = sum(len(p.get("image_urls", [])) for p in posts)
        logger.info(f"开始处理 {len(posts)} 个帖子中的 {total_images} 张图片...")

        for post in posts:
            post["image_descriptions"] = self.process_post_images(post)

        described_count = sum(len(p.get("image_descriptions", [])) for p in posts)
        logger.info(f"图片处理完成：成功描述 {described_count}/{total_images} 张图片")
        return posts


if __name__ == "__main__":
    # 测试代码：需要配置豆包 API Key
    import json
    import os

    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "credentials.json"
    )
    try:
        with open(config_path, encoding="utf-8") as f:
            creds = json.load(f)
        api_key = creds["doubao"]["api_key"]
        vision_model = creds["doubao"].get("vision_model", _DEFAULT_VISION_MODEL)
        proxy = creds.get("reddit", {}).get("proxy") or None
    except FileNotFoundError:
        print("请先配置 config/credentials.json")
        exit(1)

    processor = ImageProcessor(api_key, vision_model=vision_model, proxy=proxy)

    # 用公开图片测试
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg"
    print(f"测试图片 URL: {test_url}")
    desc = processor.describe_image(test_url)
    print(f"描述结果: {desc}")
