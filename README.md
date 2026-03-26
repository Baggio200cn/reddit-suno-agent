# Reddit + Suno 音乐自媒体自动化系统

## 项目简介

自动从 Reddit 的 r/ThinkingDeeplyAI 社区搜集新闻，生成自媒体文章和 AI 音乐，并自动发布到 GitHub。

## 功能特性

- ✅ 从 Reddit 搜集最新 5 条热门帖子
- ✅ 使用豆包大模型生成标题和文案
- ✅ 使用 Suno API 生成背景音乐
- ✅ 生成 Markdown 格式的自媒体文章
- ✅ 自动推送代码到 GitHub 仓库
- ✅ 邮件通知任务完成状态
- ✅ 定时任务（每天半夜 12 点自动运行）

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
  "reddit": {
    "client_id": "your_reddit_client_id",
    "client_secret": "your_reddit_client_secret",
    "user_agent": "your_user_agent"
  },
  "suno": {
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

### 4. Reddit API 配置

1. 访问 https://www.reddit.com/prefs/apps
2. 点击 "Create App" 或 "Create Another App"
3. 填写应用信息：
   - name: 任意名称
   - type: script
   - description: 任意描述
   - about url: 任意 URL
   - redirect uri: http://localhost:8080
4. 获取 client_id 和 client_secret
5. user_agent 格式：`your_bot_name/1.0 by your_reddit_username`

### 5. Suno API 配置

1. 访问 https://suno.x-mi.cn/
2. 注册/登录账号
3. 获取 x-apiid 和 x-token

### 6. 豆包 API 配置

1. 访问 https://developer.doubao.com/
2. 注册/登录账号
3. 创建应用并获取 API Key

### 7. GitHub Token 配置

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 选择权限：repo（完整仓库权限）
4. 复制生成的 token

### 8. 邮件配置（以 QQ 邮箱为例）

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
│   ├── credentials.json     # API 凭证
│   └── schedule.json        # 定时任务配置
├── src/                     # 源代码目录
│   ├── collectors/          # 数据收集器
│   │   └── reddit_collector.py
│   ├── generators/          # 内容生成器
│   │   ├── script_generator.py
│   │   └── music_generator.py
│   ├── publishers/          # 发布器
│   │   ├── github_publisher.py
│   │   └── email_notifier.py
│   └── utils/               # 工具函数
│       └── file_utils.py
├── output/                  # 输出文件目录
│   ├── articles/            # 生成的文章
│   └── music/               # 生成的音乐
├── logs/                    # 日志文件
├── main.py                  # 主程序入口
├── requirements.txt         # Python 依赖
└── README.md                # 项目说明
```

## 工作流程

1. **数据收集**: 从 Reddit 搜集最新 5 条热门帖子
2. **文案生成**: 使用豆包大模型生成标题和简要文案
3. **音乐生成**: 使用 Suno API 生成背景音乐并下载
4. **文章生成**: 将文案和音乐整合成 Markdown 文章
5. **代码推送**: 将生成的文章和音乐推送到 GitHub 仓库
6. **发送通知**: 通过邮件通知用户任务完成

## 注意事项

- 确保所有 API 凭证已正确配置
- 确保网络连接正常
- 确保磁盘空间充足（用于存储生成的音乐文件）
- GitHub Token 需要定期更新（如果过期）
- Suno API 有配额限制，请合理使用

## 常见问题

### Q: Reddit API 报错 401？
A: 检查 client_id、client_secret 和 user_agent 是否正确

### Q: Suno 音乐生成失败？
A: 检查 x-apiid 和 x-token 是否正确，或查看 API 配额

### Q: 邮件发送失败？
A: 检查 SMTP 配置和授权码是否正确

### Q: GitHub 推送失败？
A: 检查 GitHub Token 权限和仓库地址是否正确

## 许可证

MIT License

## 联系方式

- 作者: Baggio200cn
- 项目地址: https://github.com/Baggio200cn/reddit-suno-agent
