"""
Reddit AI 资讯助手 - Windows 桌面工具
=====================================
Designed by Claude Code

功能：
  - 每天定时自动抓取 r/ThinkingDeeplyAI 热门帖子
  - 下载配图到本地
  - 结果一键复制给 Coze Agent 使用
  - 系统托盘常驻，开机自启

用法：
  python reddit_desktop_agent.py

依赖安装：
  pip install requests pystray Pillow schedule
"""

import json
import logging
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

# ── 第三方库（可选，缺失时功能降级）──────────────────
try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# ── 爬虫模块 ────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from reddit_scraper import scrape as _scrape_reddit
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = _DIR / "agent_config.json"

DEFAULT_CONFIG = {
    "subreddits": [
        "ThinkingDeeplyAI",
        "AgentsOfAI",
        "aiArt",
        "aivideo",
        "ClaudeCode",
        "Teachers",
        "books",
    ],
    "limit_min":          5,
    "limit_max":          8,
    "proxy":              "",
    "run_time":           "08:00",
    "output_dir":         str(Path.home() / "Desktop" / "Reddit_AI_资讯"),
    "claude_api_key":        "",   # Claude API Key（留空跳过图片分析）
    "claude_vision_model":   "claude-haiku-4-5-20251001",
    "reddit_client_id":      "",   # Reddit App Client ID
    "reddit_client_secret":  "",   # Reddit App Client Secret
    "strategy":              "trending",  # trending / quality / fresh / hot
    "ai_keywords": [
        "llm", "large language model", "agent", "machine learning",
        "claude", "openai", "codex", "deepseek", "kimi", "veo", "gemini",
        "gpt", "diffusion", "transformer", "neural", "algorithm",
        "fine-tuning", "rag", "multimodal", "reasoning", "inference",
        "model", "ai", "artificial intelligence",
        "art", "teacher", "book", "education", "creative",
        # SEO / 外链
        "seo", "search engine optimization", "backlink", "link building",
        "external link", "outreach", "anchor text", "domain authority",
        "guest post", "dofollow", "nofollow", "serp", "organic traffic",
        "pagerank", "link profile", "off-page", "link juice",
    ],
}

# 颜色主题
COLORS = {
    "bg":        "#1e1e2e",   # 深蓝黑
    "panel":     "#2a2a3e",   # 面板背景
    "accent":    "#7c6af7",   # 紫色强调
    "accent2":   "#56b6c2",   # 青色
    "success":   "#98c379",   # 绿色
    "warning":   "#e5c07b",   # 黄色
    "error":     "#e06c75",   # 红色
    "text":      "#abb2bf",   # 主文字
    "text_dim":  "#5c6370",   # 次要文字
    "text_hi":   "#ffffff",   # 高亮文字
    "border":    "#3e3e5a",   # 边框
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  配置读写
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            cfg = {**DEFAULT_CONFIG, **saved}
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  托盘图标生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _make_tray_icon() -> "Image.Image":
    """程序生成一个紫色圆形图标（不依赖外部图片文件）"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 紫色圆形背景
    draw.ellipse([2, 2, size - 2, size - 2], fill=(124, 106, 247, 255))
    # 白色 "R" 字母
    try:
        draw.text((18, 14), "R", fill="white", font=ImageFont.truetype("arial.ttf", 36))
    except Exception:
        draw.text((20, 16), "R", fill="white")
    return img


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Windows 桌面通知
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _win_notify(title: str, message: str):
    """发送 Windows 桌面通知（仅 Windows，失败静默忽略）"""
    if platform.system() != "Windows":
        return
    try:
        from ctypes import windll
        windll.user32.MessageBeep(0)
    except Exception:
        pass
    try:
        # 使用 PowerShell 发送 Toast 通知
        ps_script = (
            f'Add-Type -AssemblyName System.Windows.Forms;'
            f'$n = New-Object System.Windows.Forms.NotifyIcon;'
            f'$n.Icon = [System.Drawing.SystemIcons]::Information;'
            f'$n.Visible = $true;'
            f'$n.ShowBalloonTip(4000, "{title}", "{message}", '
            f'[System.Windows.Forms.ToolTipIcon]::Info);'
            f'Start-Sleep -s 5; $n.Dispose()'
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  开机自启注册
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def register_startup():
    """将本程序注册到 Windows 开机启动"""
    if platform.system() != "Windows":
        return False, "仅支持 Windows"
    try:
        startup = Path(os.environ["APPDATA"]) / \
            "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        bat_src = _DIR / "run_agent.bat"
        bat_dst = startup / "reddit_ai_agent.bat"
        bat_dst.write_text(
            f'@echo off\ncd /d "{_DIR}"\npython "{_DIR / "reddit_desktop_agent.py"}"\n',
            encoding="utf-8"
        )
        return True, f"已注册开机自启:\n{bat_dst}"
    except Exception as e:
        return False, str(e)


def unregister_startup():
    """取消开机自启"""
    if platform.system() != "Windows":
        return
    try:
        startup = Path(os.environ["APPDATA"]) / \
            "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        dst = startup / "reddit_ai_agent.bat"
        if dst.exists():
            dst.unlink()
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  主应用 GUI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RedditAgentApp:
    """Reddit AI 资讯助手主窗口"""

    VERSION = "v1.0"
    TITLE   = "Reddit AI 资讯助手"

    def __init__(self):
        self.cfg        = load_config()
        self.posts      = []          # 最近一次爬取结果
        self.log_queue  = queue.Queue()
        self.running    = False
        self.tray_icon  = None
        self._next_run  = None

        self._build_window()
        self._start_scheduler()
        self._poll_log()

    # ── 窗口构建 ──────────────────────────────────────

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title(f"{self.TITLE}  {self.VERSION}  —  Designed by Claude Code")
        self.root.geometry("720x660")
        self.root.minsize(620, 560)
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 尝试设置图标
        try:
            self.root.iconbitmap(str(_DIR / "agent.ico"))
        except Exception:
            pass

        self._build_header()
        self._build_status_bar()
        self._build_action_bar()
        self._build_log_panel()
        self._build_posts_panel()
        self._build_settings_panel()
        self._build_footer()

    def _label(self, parent, text, fg=None, bg=None, font=None, **kw):
        return tk.Label(
            parent, text=text,
            fg=fg or COLORS["text"],
            bg=bg or COLORS["bg"],
            font=font or ("Segoe UI", 10),
            **kw
        )

    def _btn(self, parent, text, cmd, bg=None, fg=None, width=12):
        bg = bg or COLORS["accent"]
        fg = fg or COLORS["text_hi"]
        b = tk.Button(
            parent, text=text, command=cmd,
            bg=bg, fg=fg, activebackground=COLORS["accent2"],
            activeforeground=COLORS["text_hi"],
            relief="flat", cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            width=width, pady=6,
        )
        b.bind("<Enter>", lambda e: b.configure(bg=COLORS["accent2"]))
        b.bind("<Leave>", lambda e: b.configure(bg=bg))
        return b

    def _build_header(self):
        f = tk.Frame(self.root, bg=COLORS["panel"], pady=12)
        f.pack(fill="x")
        tk.Label(
            f, text="🤖  Reddit AI 资讯助手",
            fg=COLORS["text_hi"], bg=COLORS["panel"],
            font=("Segoe UI", 16, "bold")
        ).pack()
        tk.Label(
            f, text="Designed by Claude Code  ·  r/ThinkingDeeplyAI",
            fg=COLORS["accent"], bg=COLORS["panel"],
            font=("Segoe UI", 9)
        ).pack()

    def _build_status_bar(self):
        f = tk.Frame(self.root, bg=COLORS["bg"], pady=6)
        f.pack(fill="x", padx=16)

        self._status_dot = tk.Label(f, text="●", fg=COLORS["success"],
                                    bg=COLORS["bg"], font=("Segoe UI", 14))
        self._status_dot.pack(side="left")

        self._status_lbl = self._label(f, "就绪", font=("Segoe UI", 10, "bold"))
        self._status_lbl.pack(side="left", padx=(4, 24))

        self._label(f, "上次运行：").pack(side="left")
        self._last_run_lbl = self._label(f, "—", fg=COLORS["text_dim"])
        self._last_run_lbl.pack(side="left", padx=(0, 20))

        self._label(f, "下次运行：").pack(side="left")
        self._next_run_lbl = self._label(f, "—", fg=COLORS["accent2"])
        self._next_run_lbl.pack(side="left")

    def _build_action_bar(self):
        f = tk.Frame(self.root, bg=COLORS["bg"], pady=4)
        f.pack(fill="x", padx=16)

        self._run_btn = self._btn(f, "▶  立即运行", self._on_run_now)
        self._run_btn.pack(side="left", padx=(0, 8))

        self._btn(f, "📁 打开文件夹", self._open_output, bg=COLORS["panel"]).pack(side="left", padx=(0, 8))
        self._btn(f, "📋 复制结果", self._copy_result, bg=COLORS["panel"]).pack(side="left", padx=(0, 8))
        self._btn(f, "⚙  开机自启", self._register_startup, bg=COLORS["panel"], width=10).pack(side="right")

    def _build_log_panel(self):
        f = tk.Frame(self.root, bg=COLORS["bg"])
        f.pack(fill="both", expand=False, padx=16, pady=(4, 0))

        self._label(f, "📋  运行日志", font=("Segoe UI", 10, "bold"),
                    fg=COLORS["text_hi"]).pack(anchor="w")

        self._log_text = scrolledtext.ScrolledText(
            f, height=7, bg=COLORS["panel"], fg=COLORS["text"],
            insertbackground=COLORS["text"],
            font=("Consolas", 9), relief="flat",
            wrap="word", state="disabled"
        )
        self._log_text.pack(fill="both", expand=True, pady=(2, 0))

        # 配色标签
        self._log_text.tag_configure("ok",   foreground=COLORS["success"])
        self._log_text.tag_configure("warn", foreground=COLORS["warning"])
        self._log_text.tag_configure("err",  foreground=COLORS["error"])
        self._log_text.tag_configure("info", foreground=COLORS["accent2"])
        self._log_text.tag_configure("dim",  foreground=COLORS["text_dim"])

    def _build_posts_panel(self):
        f = tk.Frame(self.root, bg=COLORS["bg"])
        f.pack(fill="both", expand=True, padx=16, pady=(8, 0))

        hdr = tk.Frame(f, bg=COLORS["bg"])
        hdr.pack(fill="x")
        self._posts_title = self._label(
            hdr, "📰  今日帖子（0 条）",
            font=("Segoe UI", 10, "bold"), fg=COLORS["text_hi"]
        )
        self._posts_title.pack(side="left")

        self._posts_list = tk.Listbox(
            f, bg=COLORS["panel"], fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            font=("Segoe UI", 10), relief="flat",
            activestyle="none", cursor="hand2",
            height=5
        )
        self._posts_list.pack(fill="both", expand=True, pady=(2, 0))
        self._posts_list.bind("<Double-Button-1>", self._open_post_url)

        sb = tk.Scrollbar(f, command=self._posts_list.yview,
                          bg=COLORS["panel"], troughcolor=COLORS["bg"])
        sb.pack(side="right", fill="y")
        self._posts_list.configure(yscrollcommand=sb.set)

    def _build_settings_panel(self):
        f = tk.LabelFrame(
            self.root, text="⚙  设置",
            fg=COLORS["accent"], bg=COLORS["bg"],
            font=("Segoe UI", 9), relief="flat",
            bd=1, highlightbackground=COLORS["border"]
        )
        f.pack(fill="x", padx=16, pady=8)

        row = tk.Frame(f, bg=COLORS["bg"])
        row.pack(fill="x", padx=8, pady=4)

        self._label(row, "运行时间：", bg=COLORS["bg"]).pack(side="left")
        self._time_var = tk.StringVar(value=self.cfg.get("run_time", "08:00"))
        tk.Entry(row, textvariable=self._time_var, width=6,
                 bg=COLORS["panel"], fg=COLORS["text_hi"],
                 insertbackground=COLORS["text"], relief="flat",
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 20))

        self._label(row, "代理（留空走 Veee）：", bg=COLORS["bg"]).pack(side="left")
        self._proxy_var = tk.StringVar(value=self.cfg.get("proxy", ""))
        tk.Entry(row, textvariable=self._proxy_var, width=18,
                 bg=COLORS["panel"], fg=COLORS["text_hi"],
                 insertbackground=COLORS["text"], relief="flat",
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        # 第二行：Reddit OAuth + Claude API Key
        row2 = tk.Frame(f, bg=COLORS["bg"])
        row2.pack(fill="x", padx=8, pady=(0, 4))
        self._label(row2, "Reddit Client ID：", bg=COLORS["bg"]).pack(side="left")
        self._reddit_id_var = tk.StringVar(value=self.cfg.get("reddit_client_id", ""))
        tk.Entry(row2, textvariable=self._reddit_id_var, width=18,
                 bg=COLORS["panel"], fg=COLORS["text_hi"],
                 insertbackground=COLORS["text"], relief="flat",
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))
        self._label(row2, "Client Secret：", bg=COLORS["bg"]).pack(side="left")
        self._reddit_secret_var = tk.StringVar(value=self.cfg.get("reddit_client_secret", ""))
        tk.Entry(row2, textvariable=self._reddit_secret_var, width=22,
                 bg=COLORS["panel"], fg=COLORS["text_hi"],
                 insertbackground=COLORS["text"], relief="flat",
                 font=("Segoe UI", 10), show="*").pack(side="left", padx=(0, 12))

        row2b = tk.Frame(f, bg=COLORS["bg"])
        row2b.pack(fill="x", padx=8, pady=(0, 4))
        self._label(row2b, "Claude API Key（留空跳过图片分析）：", bg=COLORS["bg"]).pack(side="left")
        self._claude_key_var = tk.StringVar(value=self.cfg.get("claude_api_key", ""))
        tk.Entry(row2b, textvariable=self._claude_key_var, width=36,
                 bg=COLORS["panel"], fg=COLORS["text_hi"],
                 insertbackground=COLORS["text"], relief="flat",
                 font=("Segoe UI", 10), show="*").pack(side="left", padx=(0, 12))
        self._btn(row2b, "保存", self._save_settings, width=6).pack(side="left")

        # 第三行：抓取策略
        row3 = tk.Frame(f, bg=COLORS["bg"])
        row3.pack(fill="x", padx=8, pady=(0, 4))
        self._label(row3, "抓取策略：", bg=COLORS["bg"]).pack(side="left")
        self._strategy_var = tk.StringVar(value=self.cfg.get("strategy", "trending"))
        strategy_menu = tk.OptionMenu(row3, self._strategy_var,
                                      "trending", "quality", "fresh", "hot")
        strategy_menu.configure(bg=COLORS["panel"], fg=COLORS["text_hi"],
                                activebackground=COLORS["accent"],
                                activeforeground=COLORS["text_hi"],
                                relief="flat", font=("Segoe UI", 10), width=10)
        strategy_menu["menu"].configure(bg=COLORS["panel"], fg=COLORS["text_hi"],
                                        activebackground=COLORS["accent"])
        strategy_menu.pack(side="left", padx=(0, 8))
        self._label(row3,
                    "trending=近48h热帖  quality=高赞精品  fresh=24h新帖  hot=兼容旧版",
                    fg=COLORS["text_dim"], bg=COLORS["bg"],
                    font=("Segoe UI", 8)).pack(side="left")

    def _build_footer(self):
        f = tk.Frame(self.root, bg=COLORS["panel"], pady=4)
        f.pack(fill="x", side="bottom")
        self._label(
            f, "双击帖子在浏览器中打开  ·  关闭窗口后程序在托盘继续运行",
            fg=COLORS["text_dim"], bg=COLORS["panel"], font=("Segoe UI", 8)
        ).pack()

    # ── 状态更新 ───────────────────────────────────────

    def _set_status(self, text: str, color: str = None):
        self._status_lbl.configure(text=text, fg=color or COLORS["text"])
        self._status_dot.configure(fg=color or COLORS["text"])

    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((f"[{ts}] {msg}\n", tag))

    def _poll_log(self):
        try:
            while True:
                text, tag = self.log_queue.get_nowait()
                self._log_text.configure(state="normal")
                self._log_text.insert("end", text, tag or ())
                self._log_text.see("end")
                self._log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(150, self._poll_log)

    def _update_posts_list(self):
        self._posts_list.delete(0, "end")
        for i, p in enumerate(self.posts, 1):
            imgs = len(p.get("local_images", []))
            img_tag = f" 🖼×{imgs}" if imgs else ""
            self._posts_list.insert("end",
                f"  {i}. {p['title'][:70]}{img_tag}")
        self._posts_title.configure(text=f"📰  今日帖子（{len(self.posts)} 条）")

    # ── 爬取逻辑 ───────────────────────────────────────

    def _do_scrape(self):
        """在后台线程中执行爬取"""
        self.running = True
        self.root.after(0, lambda: self._run_btn.configure(state="disabled"))
        self.root.after(0, lambda: self._set_status("运行中…", COLORS["warning"]))
        subs = self.cfg.get("subreddits") or [self.cfg.get("subreddit", "ThinkingDeeplyAI")]
        strategy = self.cfg.get("strategy", "trending")
        self._log(f"开始抓取 {len(subs)} 个社区（策略：{strategy}）...", "info")

        try:
            if not HAS_SCRAPER:
                raise ImportError("找不到 reddit_scraper.py，请确保与本文件在同一目录")

            date_str = datetime.now().strftime("%Y-%m-%d")

            scrape_cfg = {
                "subreddits":          subs,
                "limit_min":           self.cfg.get("limit_min", 5),
                "limit_max":           self.cfg.get("limit_max", 8),
                "proxy":               self.cfg.get("proxy", ""),
                "output_dir":          self.cfg["output_dir"],
                "request_delay":       1.5,
                "ai_keywords":         self.cfg.get("ai_keywords", []),
                "claude_api_key":      self.cfg.get("claude_api_key", ""),
                "claude_vision_model":   self.cfg.get("claude_vision_model", "claude-haiku-4-5-20251001"),
                "reddit_client_id":      self.cfg.get("reddit_client_id", ""),
                "reddit_client_secret":  self.cfg.get("reddit_client_secret", ""),
                "strategy":              strategy,
            }

            # 重定向 logging 到 GUI 日志
            _gui_handler = _GUILogHandler(self._log)
            logging.getLogger().addHandler(_gui_handler)

            posts = _scrape_reddit(scrape_cfg)

            logging.getLogger().removeHandler(_gui_handler)

            if posts:
                self.posts = posts
                total_imgs = sum(len(p.get("local_images", [])) for p in posts)
                self._log(f"✅ 完成！{len(posts)} 条帖子，{total_imgs} 张图片", "ok")
                self.root.after(0, self._update_posts_list)

                # 保存 JSON 结果
                self._save_result_json(posts, date_str)

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.root.after(0, lambda: self._last_run_lbl.configure(
                    text=now_str, fg=COLORS["success"]))

                _win_notify("Reddit AI 资讯助手",
                            f"✅ 抓取完成：{len(posts)} 条帖子，{total_imgs} 张图片")
                self.root.after(0, lambda: self._set_status("完成", COLORS["success"]))
            else:
                self._log("⚠️ 未获取到帖子，请检查网络或 Veee 是否连接", "warn")
                self.root.after(0, lambda: self._set_status("失败", COLORS["error"]))

        except Exception as e:
            self._log(f"❌ 错误: {e}", "err")
            self.root.after(0, lambda: self._set_status("出错", COLORS["error"]))
        finally:
            self.running = False
            self.root.after(0, lambda: self._run_btn.configure(state="normal"))

    def _save_result_json(self, posts: list, date_str: str):
        out = Path(self.cfg["output_dir"]) / date_str
        out.mkdir(parents=True, exist_ok=True)
        path = out / "posts.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        self._log(f"📄 结果已保存: {path}", "dim")

    # ── 按钮回调 ───────────────────────────────────────

    def _on_run_now(self):
        if self.running:
            return
        threading.Thread(target=self._do_scrape, daemon=True).start()

    def _open_output(self):
        path = Path(self.cfg["output_dir"])
        path.mkdir(parents=True, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(str(path))
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _open_post_url(self, event):
        sel = self._posts_list.curselection()
        if not sel or not self.posts:
            return
        idx = sel[0]
        if idx < len(self.posts):
            url = self.posts[idx].get("url", "")
            if url:
                import webbrowser
                webbrowser.open(url)

    def _copy_result(self):
        if not self.posts:
            messagebox.showinfo("提示", "还没有抓取结果，请先点「立即运行」")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        subs = self.cfg.get("subreddits") or [self.cfg.get("subreddit", "ThinkingDeeplyAI")]
        lines = [f"=== Reddit AI 资讯  {date_str} ===\n",
                 f"来源社区: {', '.join('r/'+s for s in subs)}\n\n"]
        for i, p in enumerate(self.posts, 1):
            sub_tag = f"[r/{p.get('subreddit', '?')}] " if p.get("subreddit") else ""
            lines.append(f"【帖子 {i}】{sub_tag}{p['title']}\n")
            if p.get("selftext"):
                lines.append(f"内容：{p['selftext'][:500]}\n")
            elif p.get("comments"):
                lines.append("内容（热门评论）：\n")
                for j, c in enumerate(p["comments"], 1):
                    lines.append(f"  评论{j}：{c[:300]}\n")
            lines.append(f"链接：{p['url']}\n")
            for img in p.get("local_images", []):
                lines.append(f"图片：{img['local_path']}\n")
            lines.append("\n")
        text = "".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("✅ 已复制", "结果已复制到剪贴板，可直接粘贴给 Coze！")

    def _save_settings(self):
        self.cfg["run_time"]               = self._time_var.get().strip() or "08:00"
        self.cfg["proxy"]                  = self._proxy_var.get().strip()
        self.cfg["claude_api_key"]         = self._claude_key_var.get().strip()
        self.cfg["reddit_client_id"]       = self._reddit_id_var.get().strip()
        self.cfg["reddit_client_secret"]   = self._reddit_secret_var.get().strip()
        self.cfg["strategy"]               = self._strategy_var.get()
        save_config(self.cfg)
        self._restart_scheduler()
        has_claude  = bool(self.cfg.get("claude_api_key"))
        has_reddit  = bool(self.cfg.get("reddit_client_id"))
        strategy    = self.cfg.get("strategy", "trending")
        self._log(
            f"✅ 设置已保存（每天 {self.cfg['run_time']} 运行，策略：{strategy}，"
            f"Reddit OAuth：{'✓' if has_reddit else '✗ 未填（可能被403）'}，"
            f"图片分析：{'开启' if has_claude else '关闭'}）",
            "ok"
        )

    def _register_startup(self):
        ok, msg = register_startup()
        if ok:
            messagebox.showinfo("✅ 开机自启", msg)
        else:
            messagebox.showerror("失败", msg)

    # ── 调度器 ────────────────────────────────────────

    def _start_scheduler(self):
        if not HAS_SCHEDULE:
            self._log("⚠️ schedule 库未安装，定时功能不可用。运行: pip install schedule", "warn")
            return
        self._schedule_thread = threading.Thread(
            target=self._run_scheduler, daemon=True)
        self._schedule_thread.start()
        self._update_next_run_label()

    def _run_scheduler(self):
        schedule.clear()
        run_time = self.cfg.get("run_time", "08:00")
        schedule.every().day.at(run_time).do(self._scheduled_run)
        while True:
            schedule.run_pending()
            time.sleep(30)

    def _scheduled_run(self):
        if not self.running:
            self._log(f"⏰ 定时触发（{self.cfg['run_time']}）", "info")
            threading.Thread(target=self._do_scrape, daemon=True).start()

    def _restart_scheduler(self):
        if HAS_SCHEDULE:
            schedule.clear()
            run_time = self.cfg.get("run_time", "08:00")
            schedule.every().day.at(run_time).do(self._scheduled_run)
            self._update_next_run_label()

    def _update_next_run_label(self):
        run_time = self.cfg.get("run_time", "08:00")
        now = datetime.now()
        h, m = map(int, run_time.split(":"))
        nxt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if nxt <= now:
            nxt += timedelta(days=1)
        self._next_run_lbl.configure(text=nxt.strftime("%m-%d %H:%M"))

    # ── 托盘 ──────────────────────────────────────────

    def _setup_tray(self):
        if not HAS_TRAY:
            return
        icon_img = _make_tray_icon()
        menu = pystray.Menu(
            pystray.MenuItem("打开主窗口",  self._show_window, default=True),
            pystray.MenuItem("立即运行",    lambda: self._on_run_now()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出",       self._quit_app),
        )
        self.tray_icon = pystray.Icon(
            "reddit_agent", icon_img,
            f"Reddit AI 资讯助手 {self.VERSION}", menu
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_window(self, *_):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def _on_close(self):
        if HAS_TRAY and self.tray_icon:
            self.root.withdraw()   # 最小化到托盘
        else:
            self._quit_app()

    def _quit_app(self, *_):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.root.destroy()

    # ── 启动 ──────────────────────────────────────────

    def run(self):
        self._setup_tray()
        self._log(f"程序已启动，每天 {self.cfg.get('run_time', '08:00')} 自动运行", "info")
        if not HAS_SCRAPER:
            self._log("⚠️ 未找到 reddit_scraper.py，请与本文件放在同一目录", "warn")
        self.root.mainloop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  logging → GUI 日志桥接
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class _GUILogHandler(logging.Handler):
    _TAG_MAP = {
        logging.WARNING:  "warn",
        logging.ERROR:    "err",
        logging.CRITICAL: "err",
    }

    def __init__(self, log_fn):
        super().__init__()
        self._log_fn = log_fn

    def emit(self, record):
        tag = self._TAG_MAP.get(record.levelno, "")
        self._log_fn(self.format(record), tag)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    # 检查缺失的依赖并给出提示
    missing = []
    if not HAS_SCHEDULE:
        missing.append("schedule")
    if not HAS_TRAY:
        missing.append("pystray  Pillow")

    if missing:
        print("=" * 50)
        print("⚠️  部分功能依赖未安装，请运行：")
        print(f"   pip install {' '.join(missing)}")
        print("程序将以有限功能启动...")
        print("=" * 50)

    app = RedditAgentApp()
    app.run()
