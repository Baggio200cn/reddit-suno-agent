"""
测试不同的 RSS Feed
"""
import feedparser

def test_feeds():
    """测试多个 RSS Feed"""
    feeds = [
        "https://www.reddit.com/r/ThinkingDeeplyAI/.rss",
        "https://www.reddit.com/r/technology/.rss",
        "https://www.reddit.com/.rss",
        "http://feeds.bbci.co.uk/news/rss.xml",  # BBC News
    ]

    for i, url in enumerate(feeds, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}: {url}")
        print(f"{'=' * 60}")

        try:
            feed = feedparser.parse(url)

            print(f"✅ 成功解析")
            print(f"  - 标题: {feed.get('feed', {}).get('title', 'N/A')}")
            print(f"  - 条目数: {len(feed.entries)}")
            print(f"  - bozo: {feed.bozo}")

            if feed.bozo:
                print(f"  - 警告: {feed.bozo_exception}")

            if feed.entries:
                print(f"  - 第一条: {feed.entries[0].get('title', 'N/A')}")

        except Exception as e:
            print(f"❌ 失败: {e}")

if __name__ == "__main__":
    test_feeds()
