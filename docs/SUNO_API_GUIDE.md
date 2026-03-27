# Suno 音乐生成模块使用指南

## 概述

本系统支持两种 Suno API 方式：
1. **官方 API** (https://api.sunoapi.org) - 稳定可靠，功能完整
2. **非官方 API** (https://suno.x-mi.cn) - 免费使用，功能有限

## 官方 API

### 获取 API Key

1. 访问 https://sunoapi.org/api-key
2. 注册/登录账号
3. 创建 API Key

### 配置示例

```json
{
  "suno": {
    "api_type": "official",
    "api_key": "sk-xxxxxxxxxxxxxxxx"
  }
}
```

### 功能特性

✅ 支持歌词生成
✅ 支持多种模型版本（V4, V4_5, V4_5PLUS, V4_5ALL, V5）
✅ 支持自定义模式（style, title）
✅ 支持音乐扩展
✅ 支持人声分离
✅ 支持积分查询
✅ 音频文件保存 15 天

### 使用示例

```python
from src.generators.music_generator import SunoMusicGenerator

# 初始化官方 API
generator = SunoMusicGenerator(
    api_type="official",
    api_key="sk-xxxxxxxxxxxxxxxx"
)

# 生成音乐
results = generator.generate_music(
    prompt="一首轻松愉快的电子音乐",
    style="electronic",
    title="我的音乐",
    instrumental=False,
    model="V4_5"
)

# 生成歌词
lyrics = generator.generate_lyrics(
    prompt="一首关于冒险和发现的歌曲"
)

# 查询剩余积分
credits = generator.get_remaining_credits()
print(f"剩余积分: {credits}")
```

---

## 非官方 API

### 获取凭证

1. 访问 https://suno.x-mi.cn/
2. 登录账号（ID: 33883701）
3. 打开浏览器开发者工具（F12）
4. 切换到 Network 标签
5. 找到请求，查看 Request Headers
6. 复制 `x-apiid` 和 `x-token`

### 配置示例

```json
{
  "suno": {
    "api_type": "unofficial",
    "api_id": "your_x-apiid",
    "token": "your_x-token"
  }
}
```

### 功能特性

✅ 免费使用
✅ 基础音乐生成
❌ 不支持歌词生成
❌ 不支持音乐扩展
❌ 不支持人声分离

### 使用示例

```python
from src.generators.music_generator import SunoMusicGenerator

# 初始化非官方 API
generator = SunoMusicGenerator(
    api_type="unofficial",
    api_id="your_x-apiid",
    token="your_x-token"
)

# 生成音乐
results = generator.generate_music(
    prompt="一首轻松愉快的电子音乐",
    style="electronic"
)
```

---

## API 对比

| 功能 | 官方 API | 非官方 API |
|------|----------|-------------|
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 费用 | 按次付费 | 免费 |
| 歌词生成 | ✅ | ❌ |
| 音乐扩展 | ✅ | ❌ |
| 人声分离 | ✅ | ❌ |
| 模型版本 | 5 种 | 1 种 |
| 自定义参数 | ✅ | 有限 |
| 积分查询 | ✅ | ❌ |
| 音频保存期 | 15 天 | 不确定 |

---

## 模型版本说明

### 官方 API

| 模型 | 特点 | 最长时长 |
|------|------|----------|
| V4 | 高质量，最佳音频质量 | 4 分钟 |
| V4_5 | 高级功能，卓越的流派融合 | 8 分钟 |
| V4_5PLUS | 更丰富音色 | 8 分钟 |
| V4_5ALL | 更好的歌曲结构 | 8 分钟 |
| V5 | 生成速度更快 | 8 分钟 |

### 非官方 API

| 模型 | 特点 |
|------|------|
| chirp-v4 | 基础模型 |

---

## 参数说明

### generate_music 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | str | ✅ | 音乐描述（歌词或灵感） |
| style | str | ❌ | 音乐风格（自定义模式） |
| title | str | ❌ | 歌曲标题（自定义模式） |
| instrumental | bool | ❌ | 是否纯音乐（默认 False） |
| model | str | ❌ | 模型版本（默认 V4_5） |
| output_dir | str | ❌ | 输出目录（默认 output/music） |

### 返回格式

```python
[
  {
    "id": "audio_id",
    "title": "歌曲标题",
    "audio_url": "https://xxx.mp3",
    "local_path": "/path/to/music_xxx.mp3",
    "duration": 180.5,
    "style": "风格标签",
    "lyric": "歌词文本"  # 仅非官方 API
  }
]
```

---

## 最佳实践

### 1. 提示词优化

- 📝 **详细描述**：描述音乐风格、情绪、乐器、人声
- 🎯 **具体明确**：避免模糊或复杂的描述
- 🎵 **指定风格**：如"电子、流行、爵士、摇滚"
- 🎤 **人声要求**：如"男声、女声、合唱、无"

### 2. 模型选择

- 🎨 **追求质量**：使用 V4
- 🚀 **快速生成**：使用 V5
- 🎼 **长时间音乐**：使用 V4_5、V4_5PLUS 或 V4_5ALL
- 🎭 **流派融合**：使用 V4_5

### 3. 错误处理

```python
results = generator.generate_music(prompt="...")

if not results:
    print("音乐生成失败")
    # 尝试重试或使用备用方案
else:
    for track in results:
        print(f"生成成功: {track['local_path']}")
```

---

## 常见问题

### Q1: 官方 API 提示积分不足怎么办？

A: 访问 https://sunoapi.org/api-key 购买积分。

### Q2: 非官方 API 提示 401 错误？

A: 检查 x-apiid 和 x-token 是否正确，可能需要重新获取。

### Q3: 音乐生成很慢怎么办？

A: 音乐生成通常需要 30-120 秒，请耐心等待。

### Q4: 下载的音乐无法播放？

A: 检查网络连接和存储空间，尝试重新下载。

### Q5: 如何生成纯音乐？

A: 设置 `instrumental=True`。

---

## 参考资料

- [Suno 官方 API 文档](https://docs.sunoapi.org)
- [opencli-plugin-suno](https://github.com/joeseesun/opencli-plugin-suno)
- [Suno-API 项目](https://gitcode.com/GitHub_Trending/su/Suno-API)

---

## 更新日志

### v2.0.0 (2026-03-26)

- ✅ 新增官方 API 支持
- ✅ 支持歌词生成
- ✅ 支持多种模型版本
- ✅ 支持自定义参数
- ✅ 改进错误处理
- ✅ 优化下载逻辑
