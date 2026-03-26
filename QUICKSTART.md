# 快速开始指南

## 🎯 项目概述

Reddit Suno 音乐自媒体系统是一个自动化工具，能够：
- ✅ 从 Reddit 搜集最新 5 条热门帖子
- ✅ 使用豆包大模型生成标题和文案
- ✅ 使用 Suno API 生成背景音乐
- ✅ 生成 Markdown 格式的自媒体文章
- ✅ 自动推送代码到 GitHub 仓库
- ✅ 邮件通知任务完成状态
- ✅ 定时任务（每天半夜 12 点自动运行）

## 📋 前置要求

1. **Python 环境**: Python 3.8+
2. **Reddit 账号**: 用于获取 API 密钥
3. **Suno 账号**: 用于生成音乐（账号 ID: 33883701）
4. **豆包开发者账号**: 用于生成文案
5. **GitHub 账号**: 用于推送代码
6. **邮箱账号**: 用于接收通知

## 🚀 快速开始（5 步搞定）

### 第 1 步：安装依赖

```bash
cd reddit-music-publisher
pip install -r requirements.txt
```

### 第 2 步：获取 Reddit API 密钥

1. 访问 https://www.reddit.com/prefs/apps
2. 点击 "Create App"
3. 填写信息：
   - name: `RedditSunoBot`
   - type: `script`
   - about url: `http://localhost:8080`
   - redirect uri: `http://localhost:8080`
4. 复制 `client_id` 和 `client_secret`
5. `user_agent` 格式：`RedditSunoBot/1.0 by your_reddit_username`

### 第 3 步：获取 Suno API 密钥

1. 访问 https://suno.x-mi.cn/
2. 登录你的账号（ID: 33883701）
3. 使用浏览器开发者工具获取 `x-apiid` 和 `x-token`

### 第 4 步：获取豆包 API 密钥

1. 访问 https://developer.doubao.com/
2. 注册/登录账号
3. 创建应用并获取 API Key

### 第 5 步：配置环境

编辑 `config/credentials.json`：

```json
{
  "reddit": {
    "client_id": "你的 Reddit client_id",
    "client_secret": "你的 Reddit client_secret",
    "user_agent": "RedditSunoBot/1.0 by your_reddit_username"
  },
  "suno": {
    "api_id": "你的 Suno API ID",
    "token": "你的 Suno Token"
  },
  "doubao": {
    "api_key": "你的豆包 API Key"
  },
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "sender_email": "你的邮箱@qq.com",
    "sender_password": "你的 QQ 邮箱授权码",
    "receiver_email": "接收者邮箱@qq.com"
  },
  "github": {
    "token": "你的 GitHub Personal Access Token",
    "repo": "Baggio200cn/reddit-suno-agent"
  }
}
```

## 🎬 运行方式

### 单次运行（立即执行）

```bash
python main.py
```

### 定时运行（每天半夜 12 点）

```bash
python main.py --schedule
```

## 📦 项目结构

```
reddit-music-publisher/
├── config/              # 配置文件
│   ├── credentials.json         # API 凭证（需要填写）
│   ├── credentials.json.example # 配置模板
│   └── schedule.json            # 定时任务配置
├── src/                 # 源代码
│   ├── collectors/       # 数据收集器
│   ├── generators/      # 内容生成器
│   ├── publishers/      # 发布器
│   └── utils/           # 工具函数
├── output/              # 输出文件
│   ├── articles/        # 生成的文章
│   └── music/           # 生成的音乐
├── logs/                # 日志文件
├── main.py              # 主程序
├── requirements.txt     # Python 依赖
└── README.md            # 项目说明
```

## 🔧 常见问题

### Q1: Reddit API 报错 401？
**A**: 检查 `credentials.json` 中的 Reddit 配置是否正确。

### Q2: Suno 音乐生成失败？
**A**:
1. 检查 Suno API 配额是否充足
2. 检查 `x-apiid` 和 `x-token` 是否正确
3. 查看日志文件 `logs/app.log` 了解详细错误

### Q3: 豆包 API 调用失败？
**A**:
1. 检查 API Key 是否有效
2. 检查 API Key 是否有足够的调用额度
3. 检查网络连接

### Q4: 邮件发送失败？
**A**:
1. 检查 SMTP 配置是否正确
2. QQ 邮箱需要使用授权码，不是登录密码
3. 检查邮箱是否开启了 SMTP 服务

### Q5: GitHub 推送失败？
**A**:
1. 检查 GitHub Token 权限（需要 `repo` 权限）
2. 检查仓库地址是否正确
3. 确保本地 Git 仓库已初始化

## 📊 工作流程

1. **数据收集**: 从 Reddit 搜集 5 条热门帖子
2. **文案生成**: 使用豆包生成标题和摘要
3. **音乐生成**: 使用 Suno 生成背景音乐
4. **文章生成**: 整合成 Markdown 文章
5. **代码推送**: 推送到 GitHub 仓库
6. **发送通知**: 邮件通知用户

## 🔐 安全提示

⚠️ **重要**：
1. 不要将 `config/credentials.json` 提交到 Git 仓库
2. 不要在代码中硬编码 API 密钥
3. 定期更新 API 密钥
4. GitHub Token 建议设置过期时间

## 📞 获取帮助

- 项目地址: https://github.com/Baggio200cn/reddit-suno-agent
- 问题反馈: 通过 GitHub Issues

## 🎉 开始使用

现在你已经准备好了！运行以下命令开始第一次自动化：

```bash
python main.py
```

祝你使用愉快！🚀
