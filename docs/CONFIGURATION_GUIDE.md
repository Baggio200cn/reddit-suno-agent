# Reddit Suno 音乐自媒体系统 - 配置指南

## ⚡ 重要更新：使用 RSS Feed，无需配置 Reddit API！

**好消息！** 本项目现在使用 **Reddit RSS Feed**，无需申请和配置 Reddit API。

### ✅ 优势
- ✅ 无需申请 API 访问权限
- ✅ 无需获取 client_id、client_secret
- ✅ 完全免费，无配额限制
- ✅ 稳定可靠，官方支持

### 📌 说明
- ✅ 可以正常获取帖子标题、链接、内容摘要
- ⚠️ 无法获取点赞数、评论数（RSS Feed 不提供这些信息）
- ✅ 完全满足我们的需求（阅读公开帖子内容）

---

## 📋 需要获取的凭证（只需 4 项）

现在只需要配置以下 4 项：

1. ✅ Suno API
2. ✅ 豆包 API
3. ✅ 邮件配置
4. ✅ GitHub Token

---

### 1. Suno API（非官方，免费）

#### 步骤：
1. 访问：https://suno.x-mi.cn/
2. 登录你的账号（ID: 33883701）
3. 按 **F12** 打开浏览器开发者工具
4. 切换到 **Network（网络）** 标签
5. 刷新页面
6. 找到任意一个请求
7. 点击该请求，查看 **Request Headers（请求头）**
8. 复制以下信息：
   - `x-apiid`: 一串数字和字母（如：155358095076248003）
   - `x-token`: 以 `sk-` 开头的字符串（如：sk-1E04222C99044971AEA4C850D95F6B0F）

#### 示例：
```
api_id: "155358095076248003"
token: "sk-1E04222C99044971AEA4C850D95F6B0F"
```

---

### 2. 豆包 API

#### 步骤：
1. 访问：https://developer.doubao.com/
2. 注册/登录账号
3. 进入控制台
4. 创建应用
5. 获取 API Key（以 `sk-` 开头的长字符串）

#### 示例：
```
api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

---

### 3. 邮件配置（QQ 邮箱示例）

#### 步骤：
1. 登录 QQ 邮箱
2. 进入 **设置 → 账户**
3. 找到 **POP3/SMTP 服务**
4. 点击 **开启**
5. 按提示发送短信验证
6. 获取 **授权码**（16 位字符）
7. 填写配置：
   ```
   smtp_server: smtp.qq.com
   smtp_port: 587
   sender_email: 你的QQ邮箱@qq.com
   sender_password: 你的QQ邮箱授权码（不是登录密码）
   receiver_email: 接收者邮箱@qq.com
   ```

#### 示例：
```
smtp_server: "smtp.qq.com"
smtp_port: 587
sender_email: "123456789@qq.com"
sender_password: "abcdefg1234567890"
receiver_email: "987654321@qq.com"
```

---

### 4. GitHub Token

#### 步骤：
1. 访问：https://github.com/settings/tokens
2. 点击 **"Generate new token (classic)"**
3. 填写信息：
   - **Note**: `RedditSunoBot`
   - **Expiration**: `No expiration`
4. 勾选权限：
   - ✅ `repo`（完整仓库权限）
5. 点击 **Generate token**
6. **立即复制** token（格式：`ghp_xxxxxxxxxxxxxxxxxxxx`）

#### 示例：
```
token: "ghp_xxxxxxxxxxxxxxxxxxxx"
repo: "Baggio200cn/reddit-suno-agent"
```

---

## 📝 配置文件模板

获取所有凭证后，填写 `config/credentials.json`：

```json
{
  "_comment_reddit": "Reddit 现在使用 RSS Feed，无需 API 凭证！",
  "suno": {
    "api_type": "unofficial",
    "api_id": "你的 Suno x-apiid",
    "token": "你的 Suno x-token"
  },
  "doubao": {
    "api_key": "你的豆包 API Key"
  },
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "sender_email": "你的邮箱@qq.com",
    "sender_password": "你的邮箱授权码",
    "receiver_email": "接收者邮箱@qq.com"
  },
  "github": {
    "token": "你的 GitHub Token",
    "repo": "Baggio200cn/reddit-suno-agent"
  }
}
```

---

## ✅ 配置完成后

### 1. 测试运行

```powershell
cd C:\Users\Zhaol\reddit-suno-agent
python main.py
```

### 2. 预期输出

程序会自动完成以下步骤：

1. **📥 收集数据**: 从 Reddit r/ThinkingDeeplyAI 的 RSS Feed 搜集 5 条热门帖子
2. **✍️ 生成文案**: 使用豆包生成标题和摘要
3. **🎵 生成音乐**: 使用 Suno 生成背景音乐并下载
4. **📄 生成文章**: 整合成 Markdown 文章
5. **📦 推送到 GitHub**: 自动提交并推送
6. **📧 发送通知**: 邮件通知你任务完成

### 3. 输出文件位置

```
reddit-suno-agent/
├── output/
│   ├── articles/
│   │   └── article_20240326.md  # 生成的文章
│   └── music/
│       └── music_123456.mp3     # 生成的音乐
└── logs/
    └── app.log                   # 运行日志
```

---

## ⚠️ 常见问题

### Q1: Reddit 需要配置 API 吗？
A: 不需要！现在使用 RSS Feed，无需任何配置。

### Q2: 为什么看不到点赞数和评论数？
A: RSS Feed 不提供这些信息，但我们不需要这些信息来完成自媒体发布。

### Q3: Suno 音乐生成失败？
A: 检查 `x-apiid` 和 `x-token` 是否正确

### Q4: 豆包 API 调用失败？
A: 检查 API Key 是否有效，是否有足够额度

### Q5: 邮件发送失败？
A: 检查 SMTP 配置和授权码是否正确（QQ 邮箱需要使用授权码）

### Q6: GitHub 推送失败？
A: 检查 GitHub Token 权限（需要 `repo` 权限）

---

## 🎯 下一步

1. ✅ 按照《配置指南》获取所有凭证（只需 4 项）
2. ✅ 填写 `config/credentials.json`
3. ✅ 运行 `python main.py`
4. ✅ 查看输出文件和日志

---

## 📞 获取帮助

如果遇到问题：
- 查看日志：`logs/app.log`
- 查看文档：`README.md`、`QUICKSTART.md`、`docs/SUNO_API_GUIDE.md`

---

**准备好所有凭证后，就可以运行 agent 得到第一次结果了！** 🚀
