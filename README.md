# Reddit + Suno 音乐自媒体自动化系统

## 项目简介

自动从 Reddit 的 r/ThinkingDeeplyAI 社区搜集新闻，生成自媒体文章和 AI 音乐，并自动发布到 GitHub。

## 功能特性

- ✅ 从 Reddit 搜集最新 5 条热门帖子（使用 RSS Feed，无需 API 凭证）
- ✅ 使用豆包大模型生成标题和文案
- ✅ 使用 Suno API 生成背景音乐
- ✅ 生成 Markdown 格式的自媒体文章
- ✅ 自动推送代码到 GitHub 仓库
- ✅ 邮件通知任务完成状态
- ✅ 定时任务（每天半夜 12 点自动运行）

## ⚡ 重要更新：使用 RSS Feed

**好消息！** 本项目现在使用 **Reddit RSS Feed** 替代 Reddit API：

### ✅ 优势

- ✅ **无需申请**：直接使用，无需 Reddit API 批准
- ✅ **无需凭证**：不需要 client_id、client_secret
- ✅ **完全免费**：无配额限制
- ✅ **稳定可靠**：官方支持的数据源
- ✅ **合法合规**：完全符合 Reddit 政策

### 📌 说明

- ✅ 可以正常获取帖子标题、链接、内容摘要
- ⚠️ 无法获取点赞数、评论数（RSS Feed 不提供这些信息）
- ✅ 完全满足我们的需求（阅读公开帖子内容）

## 环境要求

- Python 3.8+
- Windows/Linux/macOS

## 安装步骤

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

### 4. Suno API 配置

1. 访问 https://suno.x-mi.cn/
2. 登录账号
3. 按 F12 打开浏览器开发者工具
4. 切换到 Network 标签
5. 刷新页面，找到任意请求
6. 在 Request Headers 中找到：
   - `x-apiid`: 一串数字
   - `x-token`: 以 `sk-` 开头的字符串
7. 复制这两个值到配置文件

### 5. 豆包 API 配置

1. 访问 https://developer.doubao.com/
2. 注册/登录账号
3. 创建应用并获取 API Key

### 6. GitHub Token 配置

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 选择权限：repo（完整仓库权限）
4. 复制生成的 token

### 7. 邮件配置（以 QQ 邮箱为例）

1. 登录 QQ 邮箱
2. 进入设置 -> 账户
3. 开启 POP3/SMTP 服务
4. 获取授权码（不是登录密码）

## 运行方式

### 手动运行

```bash
python main.py
```

### 定时运行

编辑 `config/schedule.json` 中的定时任务配置，默认为每天半夜 12 点运行。

```bash
python main.py --schedule
```

## 项目结构

```
reddit-music-publisher/
├── config/                  # 配置文件目录
│   ├── credentials.json     # API 凭证（Reddit 不需要）
│   └── schedule.json        # 定时任务配置
├── src/                     # 源代码目录
│   ├── collectors/          # 数据收集器
│   │   └── reddit_collector.py  # 使用 RSS Feed
│   ├── generators/          # 内容生成器
│   │   ├── script_generator.py
│   │   ├── music_generator.py
│   │   └── article_generator.py
│   ├── publishers/          # 发布器
│   │   ├── github_publisher.py
│   │   └── email_notifier.py
│   └── utils/               # 工具函数
│       └── config_loader.py
├── output/                  # 输出文件目录
│   ├── articles/            # 生成的文章
│   └── music/               # 生成的音乐
├── logs/                    # 日志文件
├── main.py                  # 主程序入口
├── requirements.txt         # Python 依赖
└── README.md                # 项目说明
```

## 工作流程

1. **数据收集**: 从 Reddit RSS Feed 搜集最新 5 条热门帖子
2. **文案生成**: 使用豆包大模型生成标题和简要文案
3. **音乐生成**: 使用 Suno API 生成背景音乐并下载
4. **文章生成**: 将文案和音乐整合成 Markdown 文章
5. **代码推送**: 将生成的文章和音乐推送到 GitHub 仓库
6. **发送通知**: 通过邮件通知用户任务完成

## 注意事项

- ✅ Reddit 使用 RSS Feed，无需配置 API 凭证
- 确保其他 API 凭证已正确配置（Suno、豆包、邮件、GitHub）
- 确保网络连接正常
- 确保磁盘空间充足（用于存储生成的音乐文件）
- GitHub Token 需要定期更新（如果过期）
- Suno API 有配额限制，请合理使用

## 常见问题

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

## 许可证

MIT License

## 联系方式

- 作者: Baggio200cn
- 项目地址: https://github.com/Baggio200cn/reddit-suno-agent
