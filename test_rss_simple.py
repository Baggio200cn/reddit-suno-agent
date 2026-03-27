"""
简单测试 RSS Feed
"""
import feedparser

def test_rss():
    """测试 RSS Feed"""
    rss_url = "https://www.reddit.com/r/ThinkingDeeplyAI/.rss"
    print(f"正在解析 RSS Feed: {rss_url}")

    try:
        feed = feedparser.parse(rss_url)

        print(f"\nFeed 状态:")
        print(f"  - bozo: {feed.bozo}")
        print(f"  - bozo_exception: {feed.bozo_exception}")
        print(f"  - feed.title: {feed.get('feed', {}).get('title', 'N/A')}")
        print(f"  - entries 数量: {len(feed.entries)}")

        if feed.bozo:
            print(f"\n⚠️ Feed 解析警告: {feed.bozo_exception}")

        if not feed.entries:
            print("\n❌ Feed 中没有条目")
            return False

        print(f"\n✅ 成功解析 {len(feed.entries)} 条条目")

        # 显示前 3 条
        for i, entry in enumerate(feed.entries[:3], 1):
            print(f"\n{'=' * 50}")
            print(f"条目 {i}")
            print(f"{'=' * 50}")
            print(f"标题: {entry.get('title', 'N/A')}")
            print(f"链接: {entry.get('link', 'N/A')}")
            print(f"作者: {entry.get('author', 'N/A')}")
            print(f"发布时间: {entry.get('published', 'N/A')}")
            print(f"摘要: {entry.get('summary', 'N/A')[:100]}...")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_rss()
