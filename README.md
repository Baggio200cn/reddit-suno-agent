# Reddit + Suno 音乐自媒体自动化系统

<div align="center">

![AI Tech](https://img.shields.io/badge/AI-Tech-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![GitHub](https://img.shields.io/badge/GitHub-Auto%20Publish-lightgrey)

**自动化内容创作 | AI 音乐生成 | 智能发布**

</div>

---

## 🎯 项目简介

这是一个智能化的自媒体自动化系统，能够自动从 Reddit 社区搜集最新的 AI 技术资讯，使用大模型生成高质量文章，结合 AI 生成的原创音乐，实现全流程自动化内容创作和发布。

---

## ✨ 核心功能

- 🤖 **智能数据收集**: 从 Reddit r/ThinkingDeeplyAI 自动搜集热门帖子（使用 RSS Feed，无需 API）
- ✍️ **AI 文章生成**: 使用豆包大模型生成标题和高质量文案
- 🎵 **AI 音乐创作**: 集成 x-mi.cn API 生成原创背景音乐（支持自定义歌词）
- 📝 **文章整合**: 将文案和音乐整合成 Markdown 格式的自媒体文章
- 🚀 **自动发布**: 一键推送到 GitHub 仓库，支持版本管理
- 📧 **邮件通知**: 任务完成后自动发送邮件通知
- ⏰ **定时任务**: 支持定时自动运行（默认每天半夜 12 点）

---

## 📊 案例展示

以下是一个真实的 AI 生成案例（2026年3月29日），展示系统能力的同时，你也可以直接查看效果。

### 📰 今日资讯

#### 1. 🎨 我在ChatGPT中测试了全新版本的Photoshop

> 作者：Beginning-Willow-801

TLDR - ChatGPT内置的Photoshop功能变得更加专业了。这不再只是一个给图片添加滤镜的玩具。最新的Adobe公开文档显示，ChatGPT版Photoshop现在支持在ChatGPT内进行生成式AI编辑，包括添加、移除和替换元素，交换或生成背景，编辑特定对象或人物，然后用经典的Photoshop风格调整和效果继续优化图像。

Adobe还表示免费用户也可以试用，Adobe每天提供10次免费生成。这使得它与大多数AI图像工具相比与众不同，它结合了两件事：对话式编辑和选择性控制。你可以进行定向编辑，而不是每次都重新生成整个图像。更换背景而不重新生成主体。移除背景中的随机游客而不破坏前面的人物...

![配图展示](https://via.placeholder.com/300x200/667eea/ffffff?text=AI+Photoshop)

#### 2. 💰 搭建了一个MCP服务器，用于分析政客和公司内部人士的股票交易

> 作者：Due_Patient_2650

嘿！我搭建了一个MCP服务器，你可以在上面分析政客（国会和特朗普政府成员）和企业内部人士的股票交易。它有助于解答这类问题：有哪些可能从伊朗战争中获益的股票出现了重要的内部人士买入？美国政府官员持有的股票表现如何？哪些政治家在交易科技股票方面有最佳记录？重大事件前是否有内幕买入聚集？

MCP暴露的工具允许AI模型查询：国会交易、政客组合估计回报率、延迟调整表现（基于交易公开时间的回报）、特朗普政府的估计投资组合、企业内部人士交易（SEC表格4）、汇总的政客/内部人士情绪。我几天前启动了MCP服务器，已经获得了7个年度订阅，这真令人惊讶。

#### 3. 🎨 r/aiArt 盲视：我在四个月内失去90%视力时的视觉描绘

> 作者：EJMac11

几年前，由于白内障迅速发展，我失去了90%以上的视力。我让ChatGPT生成一张我的照片，以概括我生命中的那段时期。"生成一张从概念上表现我视力丧失的照片——当时我失去了90%以上的视力。让眼睛看起来像是在融化并从脸上流下，如果可能的话，试着让它们有一定的'深度'，也许是暗色的。"

![视觉描绘](https://via.placeholder.com/300x200/764ba2/ffffff?text=Vision+Loss+Art)

#### 4. ⚔️ 武士跳楼

> 作者：16x98

这是一张具有**赛博朋克风格**的数字艺术作品。画面展现了一个身穿黑色服装、戴着传统**斗笠**的神秘人物形象。

**核心视觉元素：**
- **对比融合**: 传统东方斗笠与现代科幻城市背景的结合
- **背景设定**: 高耸的摩天大楼、霓虹灯光、暗蓝色调的夜间都市场景
- **人物特征**: 面部被阴影遮挡，显得神秘莫测；着装融合古代与现代元素
- **氛围营造**: 运用光影、焦点模糊等技术营造出神秘、冷酷的未来感

这种"古今结合、东西融汇"的设计风格在当代数字艺术和游戏设计中较为流行。

![赛博朋克武士](https://via.placeholder.com/300x200/667eea/ffffff?text=Cyberpunk+Samurai)

#### 5. ⚠️ Opus 4.6 目前处于无法使用的状态

> 作者：vntrx

编辑：我说我用的是和上周完全一样的设置，意思是：相同的.mds文件、相同的项目文件夹、相同的提示词、相同的技能，以及一个全新的会话。我100%确定Opus被严重削弱了，或者目前就是无法正常工作。我加载了编码项目的备份，复制粘贴了上周使用的完全相同的提示词，结果却远不如上周的。这简直就像在使用某个2022年版本的ChatGPT，简单的单句提示词给出了绝对糟糕的结果。

例如：我给了一个GUI元素的新x和y变量，告诉它硬编码进去。几周来我一直这样做，总是使用Sonnet。现在我需要Opus，但即使这样，它也不做。有时它会更改一个完全不相关的脚本中的完全不同的变量，有时使用错误的数字，其他时候什么都不做并说完成了...

这怎么能合法？？？我每月支付110欧元给一个AI，它现在只处于支持聊天机器人的水平... ANTHROPIC 修复你的产品！！！

---

### 📊 今日总结

**趋势观察：**
- 🎯 AI与专业设计工具的深度集成（如ChatGPT+Photoshop）
- 📈 AI驱动的金融数据挖掘与分析工具发展
- 🎨 多模态AI在艺术创作中的情感化表达
- ⚖️ 大模型性能稳定性与用户体验的平衡

---

### 🎵 原创歌词：AI修图革命

```text
# 《AI修图革命》

（前奏：电吉他失真轰鸣，鼓点砸出棱角，贝斯低吼如暗流）

**主歌1**
滤镜早成老黄历 别再翻那旧抽屉
ChatGPT揣着新家伙 掀翻PS的老规矩
生成式的手术刀 精准得像把剃刀
添个月亮换片海 游客滚出我的镜头外
经典调整它全明白 不用你再瞎胡猜
免费的午餐每天十份 够你把那灵感炖

**副歌**
嘿！对话里的修图师 握着选择的尺子
身份钉死不跑偏 细节抠到骨头尖
语义懂你每句话 多效叠出花
撤销键是后悔药 日常修图不用熬！
（重复副歌）
嘿！对话里的修图师 握着选择的尺子
身份钉死不跑偏 细节抠到骨头尖
语义懂你每句话 多效叠出花
撤销键是后悔药 日常修图不用熬！

**主歌2**
产品图要亮堂堂 背景换成金殿堂
游客乱入别慌张 一键让他去流浪
不是瞎蒙的野路子 是AI攥着精准的钥匙
对话里敲几个字 画面就按你意思来事
免费额度揣兜里 不用再看谁脸色行事
老PS的架子塌了 新规则由咱来立着

**副歌重复**
嘿！对话里的修图师 握着选择的尺子
身份钉死不跑偏 细节抠到骨头尖
语义懂你每句话 多效叠出花
撤销键是后悔药 日常修图不用熬！
（再重复副歌）
嘿！对话里的修图师 握着选择的尺子
身份钉死不跑偏 细节抠到骨头尖
语义懂你每句话 多效叠出花
撤销键是后悔药 日常修图不用熬！

**桥段**
别跟我说什么传统 那套早该进坟冢
AI的锤子砸破旧笼 修图的自由握在手中
没有复杂的菜单 只有我和它的对白
想要的画面立刻来 这才是新时代的节拍

**结尾**
（电吉他渐弱，鼓点慢下来，只剩贝斯闷响）
滤镜的时代过去了 生成式的风刮起来了
免费的机会攥紧了 修图的革命开始了
（最后一声吉他失真劈裂空气，戛然而止）
```

---

### 🎶 AI生成的原创歌曲

**歌曲信息：**
- ⏱️ 时长：约3分钟
- 🎨 风格：U2 + 说唱
- 🤖 生成者：reddit-sunno-agent

> 💡 **提示**：完整版音频和高清图片已嵌入在 [demo_final.html](./demo_final.html) 中，下载后可直接用浏览器打开查看完整案例，包含可播放的音频播放器。

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Baggio200cn/reddit-suno-agent.git
cd reddit-suno-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `config/credentials.json.example` 为 `config/credentials.json`，并填写以下信息：

```json
{
  "_comment_reddit": "Reddit 现在使用 RSS Feed，无需 API 凭证！",
  "suno": {
    "api_type": "unofficial",
    "api_id": "your_suno_api_id",
    "token": "your_suno_token"
  },
  "doubao": {
    "api_key": "your_doubao_api_key"
  },
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "sender_email": "your_email@qq.com",
    "sender_password": "your_smtp_password",
    "receiver_email": "receiver@qq.com"
  },
  "github": {
    "token": "your_github_personal_access_token",
    "repo": "Baggio200cn/reddit-suno-agent"
  }
}
```

### 4. 运行程序

```bash
# 手动运行
python main.py

# 定时运行（每天半夜 12 点）
python main.py --schedule
```

---

## 📚 详细文档

### 📖 教师指南

**《Coze 智能体开发入门指南——给职业院校老师的实用手册》**

适合职业院校老师阅读，手把手教你如何开发智能体项目。

- ✅ 通俗易懂的语言
- ✅ 完整的开发流程
- ✅ 详细的对话示例
- ✅ 常见问题解答

📄 **阅读指南**: [Teacher_Guide.md](./Teacher_Guide.md)

### 🎨 完整案例展示

下载 [demo_final.html](./demo_final.html) (14MB) 查看包含所有资源的完整案例展示：

- 📝 5篇 AI 技术文章
- 🖼️ 5张高清配图（已嵌入）
- 🎵 完整歌词
- 🎶 可播放的 AI 生成歌曲（已嵌入音频）

**特点**：
- ✅ 一个文件包含所有内容
- ✅ 无需任何外部依赖
- ✅ 直接用浏览器打开即可

---

## ⚙️ 环境要求

- Python 3.8+
- Windows/Linux/macOS
- 稳定的网络连接

---

## 🔧 配置说明

### Suno API 配置

1. 访问 https://suno.x-mi.cn/
2. 登录账号
3. 按 F12 打开浏览器开发者工具
4. 切换到 Network 标签
5. 刷新页面，找到任意请求
6. 在 Request Headers 中找到：
   - `x-apiid`: 一串数字
   - `x-token`: 以 `sk-` 开头的字符串
7. 复制这两个值到配置文件

### 豆包 API 配置

1. 访问 https://developer.doubao.com/
2. 注册/登录账号
3. 创建应用并获取 API Key

### GitHub Token 配置

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 选择权限：repo（完整仓库权限）
4. 复制生成的 token

### 邮件配置（以 QQ 邮箱为例）

1. 登录 QQ 邮箱
2. 进入设置 -> 账户
3. 开启 POP3/SMTP 服务
4. 获取授权码（不是登录密码）

---

## 📁 项目结构

```
reddit-suno-agent/
├── config/                      # 配置文件目录
│   ├── credentials.json         # API 凭证（Reddit 不需要）
│   └── schedule.json            # 定时任务配置
├── src/                         # 源代码目录
│   ├── collectors/              # 数据收集器
│   │   └── reddit_collector.py  # 使用 RSS Feed
│   ├── generators/              # 内容生成器
│   │   ├── script_generator.py
│   │   ├── music_generator.py
│   │   └── article_generator.py
│   ├── processors/              # 处理器
│   │   └── image_processor.py
│   ├── publishers/              # 发布器
│   │   ├── github_publisher.py
│   │   └── email_notifier.py
│   └── utils/                   # 工具函数
│       └── config_loader.py
├── assets/                      # 资源文件
│   └── image.png                # 项目截图
├── docs/                        # 文档目录
├── main.py                      # 主程序入口
├── requirements.txt             # Python 依赖
├── README.md                    # 项目说明
├── Teacher_Guide.md             # 教师指南
├── demo_final.html              # 完整案例展示（14MB）
└── demo.html                    # 原始案例展示
```

---

## 🔄 工作流程

```mermaid
graph LR
    A[Reddit RSS Feed] --> B[数据收集]
    B --> C[豆包大模型]
    C --> D[生成标题和文案]
    D --> E[歌词生成器]
    E --> F[AI 音乐生成]
    F --> G[文章整合]
    G --> H[GitHub 发布]
    H --> I[邮件通知]
```

---

## ❓ 常见问题

### Q: Reddit 需要配置 API 吗？
A: 不需要！现在使用 RSS Feed，无需任何配置。

### Q: 为什么看不到点赞数和评论数？
A: RSS Feed 不提供这些信息，但我们不需要这些信息来完成自媒体发布。

### Q: Suno 音乐生成失败？
A: 检查 x-apiid 和 x-token 是否正确，或查看 API 配额

### Q: 豆包 API 调用失败？
A: 检查 API Key 是否有效，是否有足够额度

### Q: 邮件发送失败？
A: 检查 SMTP 配置和授权码是否正确

### Q: GitHub 推送失败？
A: 检查 GitHub Token 权限和仓库地址是否正确

---

## 🎓 技术栈

- **语言**: Python 3.8+
- **数据收集**: feedparser（RSS Feed）
- **AI 模型**: 豆包大模型
- **音乐生成**: x-mi.cn API
- **版本控制**: Git
- **发布平台**: GitHub

---

## 📝 更新日志

### v2.0.0 (最新版本)
- ✅ 使用 RSS Feed 替代 Reddit API
- ✅ 集成教师指南和案例展示
- ✅ 优化文章生成器（AI 博主风格）
- ✅ 优化歌词生成器（支持 3 分钟以上歌曲）
- ✅ 修复音乐生成 API 查询端点

### v1.0.0
- ✅ 初始版本
- ✅ 支持 Reddit API
- ✅ 支持文章和音乐生成
- ✅ 支持自动发布

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 👨‍💻 作者

- Baggio200cn
- 项目地址: https://github.com/Baggio200cn/reddit-suno-agent

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

**🎉 感谢使用 Reddit + Suno 音乐自媒体自动化系统！**

</div>
