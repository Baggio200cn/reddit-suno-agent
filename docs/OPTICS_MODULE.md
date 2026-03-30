# 光学/机器视觉模块使用指南

## 📚 模块简介

光学/机器视觉新闻收集器是 Reddit+Suno 音乐自媒体系统的核心组件之一，用于自动收集光学、机器视觉、计算机视觉领域的最新新闻和论文。

## 🎯 功能特性

### 数据来源

1. **arXiv** - 计算机视觉论文
   - URL: https://export.arxiv.org/rss/cs.CV
   - 收集最新的计算机视觉研究论文

2. **MIT Technology Review** - 科技新闻
   - URL: https://www.technologyreview.com/feed/
   - 收集前沿科技新闻

3. **Photonics Media** - 光学新闻
   - URL: https://www.photonics.com/rss
   - 收集光学领域专业新闻

### 自动筛选

支持中英文关键词自动筛选 AI/光学相关内容：

**英文关键词：**
- AI, artificial intelligence
- machine learning, deep learning
- neural network
- computer vision, image recognition
- optical, vision, imaging
- 光场, 成像

**中文关键词：**
- 人工智能, 机器学习
- 深度学习, 神经网络
- 计算机视觉, 图像识别
- 目标检测, 语义分割
- 光场, 成像, 镜头, 传感器

## 🚀 快速开始

### 基本使用

```python
from src.collectors.optics_news_collector import OpticsNewsCollector

# 创建收集器实例
collector = OpticsNewsCollector()

# 收集新闻（默认 5 条）
news = collector.collect_all(total_limit=5)

# 输出结果
for item in news:
    print(f"来源: {item['source']}")
    print(f"标题: {item['title']}")
    print(f"摘要: {item['summary'][:100]}...")
    print(f"链接: {item['url']}")
    print("-" * 50)
```

### 自定义收集

```python
# 只收集 arXiv 论文
papers = collector.collect_from_arxiv(limit=3)

# 只收集特定 RSS 源
news = collector.collect_from_rss("MIT Tech Review", "https://www.technologyreview.com/feed/", limit=2)
```

## 📊 输出格式

每条新闻包含以下字段：

```python
{
    "source": "arXiv",              # 来源名称
    "title": "论文标题",           # 标题
    "summary": "论文摘要",         # 摘要（限制 500 字符）
    "url": "https://arxiv.org/...",  # 原文链接
    "date": "2026-03-30"           # 收集日期
}
```

## ⚙️ 配置说明

### 依赖项

```bash
pip install requests feedparser
```

### 无需配置

光学收集器使用公开 RSS Feed，无需 API 密钥或认证。

## 🔍 工作原理

1. **数据获取** - 从多个 RSS Feed 获取最新内容
2. **关键词匹配** - 检查标题和摘要是否包含 AI/光学相关关键词
3. **内容过滤** - 移除 HTML 标签，提取纯文本
4. **长度限制** - 将摘要限制在合理长度内
5. **去重合并** - 合并多个来源的新闻

## 📝 示例输出

```text
正在从 arXiv 收集论文...
从 arXiv 收集到 2 篇论文
正在从 MIT Tech Review 收集新闻...
从 MIT Tech Review 收集到 1 条新闻
正在从 Photonics Media 收集新闻...
从 Photonics Media 收集到 1 条新闻
总共收集到 4 条新闻
```

## ⚠️ 注意事项

1. **网络要求** - 需要能够访问 arXiv、MIT Tech Review、Photonics Media
2. **更新频率** - RSS Feed 更新频率因网站而异
3. **内容限制** - 部分网站可能对访问频率有限制
4. **语言支持** - 支持中英文混合内容

## 🎓 适用场景

- 科技媒体编辑
- 研究人员跟踪前沿
- 行业资讯收集
- 内容创作素材来源

## 📞 技术支持

如有问题，请查看：
- 主文档: README.md
- 问题反馈: GitHub Issues

---

**版本**: 1.0.0  
**最后更新**: 2026-03-30
