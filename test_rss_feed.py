"""
测试 RSS Feed 收集器
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.collectors.reddit_collector import RedditCollector

def test_rss_feed():
    """测试 RSS Feed 收集"""
    print("=" * 50)
    print("测试 Reddit RSS Feed 收集器")
    print("=" * 50)

    try:
        # 创建收集器（无需配置）
        collector = RedditCollector()

        # 收集帖子
        print("\n正在从 r/ThinkingDeeplyAI 收集帖子...")
        posts = collector.collect_hot_posts("ThinkingDeeplyAI", limit=3)

        if not posts:
            print("❌ 没有收集到帖子")
            return False

        print(f"\n✅ 成功收集 {len(posts)} 条帖子")

        # 显示帖子信息
        for i, post in enumerate(posts, 1):
            print(f"\n{'=' * 50}")
            print(f"帖子 {i}")
            print(f"{'=' * 50}")
            print(f"ID: {post['id']}")
            print(f"标题: {post['title']}")
            print(f"URL: {post['url']}")
            print(f"时间: {post['created_date']}")
            print(f"作者: {post['author']}")
            print(f"内容摘要: {post['selftext'][:150]}...")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rss_feed()
    sys.exit(0 if success else 1)
