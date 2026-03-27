# 本地测试指南

## 📋 前置要求

- Python 3.8+
- Git
- 稳定的网络连接

---

## 🚀 快速开始（推荐）

### 步骤 1：克隆项目

```bash
# 克隆你的 GitHub 仓库
git clone https://github.com/Baggio200cn/reddit-suno-agent.git
cd reddit-suno-agent
```

### 步骤 2：创建虚拟环境

```bash
# Windows
python -m venv venv

# 或使用 conda
conda create -n reddit-suno python=3.10
conda activate reddit-suno
```

### 步骤 3：激活虚拟环境

```bash
# Windows (CMD)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### 步骤 4：安装依赖

```bash
# 如果有 uv（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 步骤 5：配置凭证

```bash
# 复制示例配置文件
copy config\credentials.json.example config\credentials.json

# 编辑 config\credentials.json，填写你的 API 密钥
# - Suno API（如果需要音乐生成）
# - 豆包 API（必需）
# - GitHub Token（必需）
```

**注意**：`credentials.json` 已加入 `.gitignore`，不会提交到 GitHub。

### 步骤 6：创建必要的目录

```bash
# 创建输出目录
mkdir output\articles
mkdir output\music

# 创建日志目录
mkdir logs
```

---

## 🧪 测试方案

### 方案 A：测试轻量版（推荐，无需 Suno 配额）

运行轻量版主程序（不生成音乐）：

```bash
python main_lite.py
```

**预期输出**：
- ✅ 收集 Reddit 帖子
- ✅ 生成标题和摘要
- ✅ 生成 Markdown 文章
- ✅ 推送到 GitHub

---

### 方案 B：测试完整版（需要 Suno 配额）

如果你有 Suno 配额：

```bash
python main.py
```

**预期输出**：
- ✅ 收集 Reddit 帖子
- ✅ 生成标题和摘要
- ✅ 生成背景音乐（需要 2-3 分钟）
- ✅ 生成 Markdown 文章
- ✅ 推送到 GitHub

---

### 方案 C：测试各个组件

#### 1. 测试 Reddit 收集

```bash
python test_rss_feed.py
```

#### 2. 测试文案生成

```bash
python test_components.py
```

#### 3. 测试音乐生成（需要 Suno 配额）

```bash
python test_music_generation.py
```

#### 4. 测试豆包 API

```bash
python test_doubao_api.py
```

---

## 📊 预期结果

### 成功标志

#### 轻量版（main_lite.py）

```
======================================================================
✅ 任务执行完成！
======================================================================
文章路径: output/articles/article_YYYYMMDD.md
GitHub 仓库: https://github.com/Baggio200cn/reddit-suno-agent
```

#### 完整版（main.py）

```
======================================================================
✅ 任务执行完成！
======================================================================
文章路径: output/articles/article_YYYYMMDD.md
音乐路径: output/music/music_xxxxx.mp3
GitHub 仓库: https://github.com/Baggio200cn/reddit-suno-agent
```

---

### 查看生成的文件

#### 查看文章

```bash
# Windows
type output\articles\article_YYYYMMDD.md

# Linux/Mac
cat output/articles/article_YYYYMMDD.md
```

#### 查看日志

```bash
# Windows
type logs\app.log

# Linux/Mac
cat logs/app.log
```

---

## ⚠️ 常见问题

### Q1: Reddit 收集失败

**原因**：网络问题或 RSS Feed 不可用

**解决**：
- 检查网络连接
- 稍后重试
- 使用代理或 VPN

---

### Q2: 豆包 API 调用失败

**错误**：`401 Unauthorized` 或 `400 Bad Request`

**解决**：
- 检查 API Key 是否正确
- 检查网络连接
- 查看 `test_doubao_api.py` 的测试结果

---

### Q3: Suno 音乐生成失败

**错误**：`剩余的积分已不够，充值可获得更多积分`

**解决**：
- 充值 Suno 账号：https://suno.x-mi.cn/
- 或使用轻量版（跳过音乐生成）

---

### Q4: GitHub 推送失败

**错误**：`403 Forbidden` 或 `Permission denied`

**解决**：
- 检查 GitHub Token 是否正确
- 检查 Token 权限（需要 `repo` 权限）
- 检查仓库名称是否正确

---

### Q5: Python 依赖安装失败

**错误**：`ModuleNotFoundError` 或 `pip install failed`

**解决**：
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用 uv（推荐）
pip install uv
uv pip install -r requirements.txt

# 或使用清华镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🎯 推荐测试流程

### 第一次测试（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Baggio200cn/reddit-suno-agent.git
cd reddit-suno-agent

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
uv pip install -r requirements.txt

# 4. 配置凭证
copy config\credentials.json.example config\credentials.json
# 编辑 config\credentials.json

# 5. 测试轻量版
python main_lite.py

# 6. 查看结果
type output\articles\article_*.md
```

---

## 📝 配置文件示例

### config/credentials.json

```json
{
  "_comment_reddit": "Reddit 现在使用 RSS Feed，无需 API 凭证！",
  "suno": {
    "api_type": "unofficial",
    "api_id": "你的 Suno API ID",
    "token": "你的 Suno Token"
  },
  "doubao": {
    "api_key": "你的豆包 API Key"
  },
  "email": {
    "enabled": false,
    "smtp_server": "",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "receiver_email": ""
  },
  "github": {
    "token": "你的 GitHub Token",
    "repo": "Baggio200cn/reddit-suno-agent"
  }
}
```

---

## 🚀 下一步

### 成功测试后

1. **设置定时任务**（可选）
   - 编辑 `config/schedule.json`
   - 使用 `python main.py --schedule` 启动定时任务

2. **配置邮件通知**（可选）
   - 在 `config/credentials.json` 中配置 SMTP
   - 启用邮件通知功能

3. **充值 Suno 账号**（可选）
   - 如果需要音乐生成功能
   - 访问：https://suno.x-mi.cn/

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`logs/app.log`
2. 运行组件测试：`python test_components.py`
3. 查看文档：`README.md`、`docs/CONFIGURATION_GUIDE.md`

---

**祝你测试顺利！** 🎉
