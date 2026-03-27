"""
文章生成器（Markdown 格式）
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleGenerator:
    """文章生成器"""

    def __init__(self, output_dir: str = "output/articles"):
        """
        初始化文章生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_article(
        self,
        title: str,
        summary: str,
        posts: List[Dict[str, Any]],
        music_path: Optional[str] = None
    ) -> str:
        """
        生成 Markdown 文章

        Args:
            title: 文章标题
            summary: 文章摘要
            posts: 帖子列表
            music_path: 音乐文件路径（可选）

        Returns:
            生成的文章文件路径
        """
        # 生成文件名（使用日期）
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"article_{date_str}.md"
        file_path = os.path.join(self.output_dir, filename)

        # 构建 Markdown 内容
        markdown_content = self._build_markdown(title, summary, posts, music_path)

        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"文章生成成功: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"生成文章失败: {e}")
            raise

    def _build_markdown(
        self,
        title: str,
        summary: str,
        posts: List[Dict[str, Any]],
        music_path: Optional[str]
    ) -> str:
        """
        构建 Markdown 内容

        Args:
            title: 文章标题
            summary: 文章摘要
            posts: 帖子列表
            music_path: 音乐文件路径

        Returns:
            Markdown 格式的文章内容
        """
        lines = []

        # 标题
        lines.append(f"# {title}\n")

        # 摘要
        lines.append(f"## 摘要\n")
        lines.append(f"{summary}\n")

        # 音乐（如果有）
        if music_path:
            music_filename = os.path.basename(music_path)
            music_relative_path = f"../music/{music_filename}"
            lines.append(f"## 背景音乐\n")
            lines.append(f"[🎵 点击播放背景音乐]({music_relative_path})\n")

        # 热门话题列表
        lines.append(f"## 热门话题\n")
        lines.append(f"本期精选了来自 r/ThinkingDeeplyAI 的 {len(posts)} 条热门话题，带你了解最新趋势和深度思考。\n\n")

        for i, post in enumerate(posts, 1):
            lines.append(f"### {i}. {post['title']}\n")

            # 分数和评论数
            lines.append(f"**🔥 热度**: {post['score']} 分 | 💬 评论: {post['num_comments']} 条\n")

            # 时间和作者
            lines.append(f"**📅 时间**: {post['created_date']} | **👤 作者**: {post['author']}\n")

            # 内容（如果有）
            if post.get('selftext'):
                content = post['selftext'][:500] + "..." if len(post['selftext']) > 500 else post['selftext']
                lines.append(f"\n**内容**:\n{content}\n")

            # 图片及中文描述（如果有）
            image_descriptions = post.get('image_descriptions', [])
            if image_descriptions:
                lines.append(f"\n**配图内容**:\n")
                for img_data in image_descriptions:
                    url = img_data.get('url', '')
                    desc = img_data.get('description', '')
                    if url:
                        lines.append(f"![配图]({url})\n")
                    if desc:
                        lines.append(f"> {desc}\n")

            # 原始链接
            lines.append(f"**🔗 原文链接**: {post['url']}\n")

            lines.append("\n---\n")

        # 底部信息
        lines.append(f"## 说明\n")
        lines.append(f"本文由 Reddit Suno 音乐自媒体系统自动生成。\n")
        lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"- **数据来源**: r/ThinkingDeeplyAI\n")
        lines.append(f"- **音乐来源**: Suno AI\n")

        return "\n".join(lines)


if __name__ == "__main__":
    # 测试代码
    generator = ArticleGenerator()

    # 测试数据
    test_posts = [
        {
            "title": "AI 技术的最新突破",
            "selftext": "这是关于 AI 技术最新突破的详细内容...",
            "score": 1000,
            "num_comments": 50,
            "created_date": "2024-01-01 00:00:00",
            "author": "AI_Expert",
            "url": "https://reddit.com/r/xxx"
        },
        {
            "title": "深度学习模型的优化方法",
            "selftext": "",
            "score": 800,
            "num_comments": 30,
            "created_date": "2024-01-01 01:00:00",
            "author": "DeepLearner",
            "url": "https://reddit.com/r/yyy"
        }
    ]

    # 生成文章
    article_path = generator.generate_article(
        title="Reddit 热门资讯精选",
        summary="本期精选了 Reddit 上最热门的 AI 相关话题。",
        posts=test_posts,
        music_path=None
    )

    print(f"文章生成成功: {article_path}")
