"""
seo_desktop_agent.py
====================
SEO 学习助手桌面工具 / SEO Learning Assistant Desktop Tool

功能：
  - 一键抓取 Ahrefs / Backlinko 等权威 SEO 博客的新手教程 RSS
  - 调用 Claude API 自动翻译为中文（摘要 + 全文）
  - 中英双语界面，已读 / 未读进度追踪
  - 翻译结果保存到本地 txt（中英对照格式）

依赖安装：
  pip install requests feedparser beautifulsoup4

用法：
  python seo_desktop_agent.py
"""

import json
import logging
import os
import queue
import sys
import threading
import time
import webbrowser
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, List, Optional

# ── 爬虫模块 ────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from seo_scraper import (
        RSS_SOURCES,
        LEARN_KEYWORDS,
        fetch_rss_articles,
        filter_articles,
        translate_article,
        save_article,
        load_read_history,
        save_read_history,
    )
    HAS_SCRAPER = True
except ImportError as _e:
    HAS_SCRAPER = False
    _IMPORT_ERR = str(_e)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = _DIR / "agent_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "claude_api_key": "",
    "proxy":          "",
    "output_dir":     str(Path.home() / "Desktop" / "SEO_学习笔记"),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  日志
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  主窗口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class SEODesktopAgent:
    # ── 颜色主题（深色）──────────────────────────────
    BG       = "#1e1e2e"
    BG2      = "#2a2a3e"
    BG3      = "#313145"
    FG       = "#cdd6f4"
    FG2      = "#a6adc8"
    ACCENT   = "#89b4fa"
    GREEN    = "#a6e3a1"
    YELLOW   = "#f9e2af"
    RED      = "#f38ba8"
    TEAL     = "#94e2d5"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SEO 学习助手 / SEO Learning Assistant")
        self.root.geometry("1100x720")
        self.root.configure(bg=self.BG)
        self.root.minsize(900, 600)

        self.cfg: Dict[str, Any] = self._load_config()
        self.result_q: queue.Queue = queue.Queue()

        # 运行时状态
        self._articles: List[Dict[str, Any]] = []   # 当前会话内抓取的文章
        self._selected_idx: Optional[int] = None
        self._read_urls: set = load_read_history(self.cfg.get("output_dir", "")) if HAS_SCRAPER else set()
        self._busy = False

        self._build_ui()
        self._poll_queue()

    # ─────────────────────────────────────────────
    #  配置 I/O
    # ─────────────────────────────────────────────
    def _load_config(self) -> Dict[str, Any]:
        cfg = dict(DEFAULT_CONFIG)
        if CONFIG_FILE.exists():
            try:
                saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                # Only update known SEO keys; don't clobber Reddit keys
                for k in DEFAULT_CONFIG:
                    if k in saved:
                        cfg[k] = saved[k]
            except Exception:
                pass
        return cfg

    def _save_config(self):
        # Merge with any existing config (to preserve Reddit agent keys)
        existing: Dict[str, Any] = {}
        if CONFIG_FILE.exists():
            try:
                existing = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing.update(self.cfg)
        CONFIG_FILE.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ─────────────────────────────────────────────
    #  UI 构建
    # ─────────────────────────────────────────────
    def _build_ui(self):
        # ── 标题栏 ────────────────────────────────
        title_bar = tk.Frame(self.root, bg=self.BG2, pady=8)
        title_bar.pack(fill="x")
        tk.Label(
            title_bar,
            text="📚 SEO 学习助手 / SEO Learning Assistant",
            bg=self.BG2, fg=self.ACCENT,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left", padx=16)

        # ── 工具栏 ────────────────────────────────
        toolbar = tk.Frame(self.root, bg=self.BG3, pady=6)
        toolbar.pack(fill="x")

        btn_cfg = dict(bg=self.BG2, fg=self.FG, relief="flat",
                       font=("Segoe UI", 9), padx=10, pady=4,
                       activebackground=self.BG3, activeforeground=self.ACCENT,
                       cursor="hand2")

        self.btn_fetch = tk.Button(
            toolbar, text="抓取新文章 / Fetch",
            command=self._on_fetch, **btn_cfg
        )
        self.btn_fetch.pack(side="left", padx=(8, 4))

        self.btn_translate = tk.Button(
            toolbar, text="翻译选中 / Translate",
            command=self._on_translate, state="disabled", **btn_cfg
        )
        self.btn_translate.pack(side="left", padx=4)

        self.btn_read = tk.Button(
            toolbar, text="标记已读 / Mark Read",
            command=self._on_mark_read, state="disabled", **btn_cfg
        )
        self.btn_read.pack(side="left", padx=4)

        self.btn_open = tk.Button(
            toolbar, text="打开原文 / Open URL",
            command=self._on_open_url, state="disabled", **btn_cfg
        )
        self.btn_open.pack(side="left", padx=4)

        self.btn_save = tk.Button(
            toolbar, text="保存笔记 / Save Note",
            command=self._on_save_note, state="disabled", **btn_cfg
        )
        self.btn_save.pack(side="left", padx=4)

        tk.Button(
            toolbar, text="⚙ 设置 / Settings",
            command=self._open_settings, **btn_cfg
        ).pack(side="right", padx=8)

        # ── 主区域（左右分栏）────────────────────
        main = tk.PanedWindow(
            self.root, orient="horizontal",
            bg=self.BG, sashwidth=4, sashrelief="flat",
        )
        main.pack(fill="both", expand=True, padx=8, pady=6)

        # ── 左侧：文章列表 ────────────────────────
        left = tk.Frame(main, bg=self.BG)
        main.add(left, minsize=340)

        tk.Label(
            left, text="文章列表 / Articles",
            bg=self.BG, fg=self.FG2,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=4, pady=(0, 2))

        list_frame = tk.Frame(left, bg=self.BG2, bd=1, relief="flat")
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, bg=self.BG2,
                                  troughcolor=self.BG, relief="flat")
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=self.BG2, fg=self.FG,
            selectbackground=self.BG3,
            selectforeground=self.ACCENT,
            font=("Segoe UI", 9),
            relief="flat", bd=0,
            activestyle="none",
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._on_open_url())

        # ── 右侧：预览 ────────────────────────────
        right = tk.Frame(main, bg=self.BG)
        main.add(right, minsize=400)

        tk.Label(
            right, text="预览 / Preview",
            bg=self.BG, fg=self.FG2,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=4, pady=(0, 2))

        self.preview = scrolledtext.ScrolledText(
            right,
            bg=self.BG2, fg=self.FG,
            font=("Consolas", 9),
            relief="flat", bd=0,
            wrap="word",
            state="disabled",
        )
        self.preview.pack(fill="both", expand=True)

        # ── 日志栏 ────────────────────────────────
        log_frame = tk.Frame(self.root, bg=self.BG2)
        log_frame.pack(fill="x", padx=8, pady=(0, 6))

        tk.Label(
            log_frame, text="日志 / Log",
            bg=self.BG2, fg=self.FG2,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=4, pady=(2, 0))

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            bg=self.BG2, fg=self.FG2,
            font=("Consolas", 8),
            relief="flat", bd=0,
            height=5,
            state="disabled",
        )
        self.log_box.pack(fill="x", padx=4, pady=(0, 4))

        # ── 状态栏 ────────────────────────────────
        status_bar = tk.Frame(self.root, bg=self.BG3, pady=3)
        status_bar.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="就绪 / Ready")
        tk.Label(
            status_bar, textvariable=self.status_var,
            bg=self.BG3, fg=self.FG2,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=8)

        self.count_var = tk.StringVar(value="")
        tk.Label(
            status_bar, textvariable=self.count_var,
            bg=self.BG3, fg=self.FG2,
            font=("Segoe UI", 8),
        ).pack(side="right", padx=8)

    # ─────────────────────────────────────────────
    #  文章列表渲染
    # ─────────────────────────────────────────────
    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for art in self._articles:
            read_mark   = "✓" if art.get("url") in self._read_urls else "○"
            trans_mark  = "译" if art.get("translated") else "  "
            source      = art.get("source_name", "")[:12]
            date        = art.get("published_date", "")[-5:]  # MM-DD
            title       = art.get("title", "")[:46]
            line = f"{read_mark} [{trans_mark}] {source:<12}  {date}  {title}"
            self.listbox.insert("end", line)

        total = len(self._articles)
        read  = sum(1 for a in self._articles if a.get("url") in self._read_urls)
        trans = sum(1 for a in self._articles if a.get("translated"))
        self.count_var.set(
            f"共 {total} 篇 | 已读 {read} | 已译 {trans}"
            f" / Total {total} | Read {read} | Translated {trans}"
        )

    # ─────────────────────────────────────────────
    #  预览区
    # ─────────────────────────────────────────────
    def _show_preview(self, art: Dict[str, Any]):
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")

        lines = []
        lines.append(f"标题：{art.get('title', '')}")
        lines.append(f"Title: {art.get('title', '')}")
        lines.append(f"来源 / Source: {art.get('source_name', '')}")
        lines.append(f"日期 / Date: {art.get('published_date', '')}")
        lines.append(f"URL: {art.get('url', '')}")
        lines.append("─" * 60)
        lines.append("")

        if art.get("zh_summary"):
            lines.append("【中文摘要】")
            lines.append(art["zh_summary"])
            lines.append("")

        if art.get("summary"):
            lines.append("【English Summary】")
            lines.append(art["summary"])
            lines.append("")

        if art.get("zh_content"):
            lines.append("【中文全文翻译】")
            lines.append(art["zh_content"])
            lines.append("")
        elif not art.get("translated"):
            lines.append("（尚未翻译 — 点击「翻译选中」获取中文内容）")
            lines.append("(Not yet translated — click 'Translate' to get Chinese content)")

        self.preview.insert("1.0", "\n".join(lines))
        self.preview.config(state="disabled")

    # ─────────────────────────────────────────────
    #  日志
    # ─────────────────────────────────────────────
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")
        logger.info(msg)

    # ─────────────────────────────────────────────
    #  按钮事件
    # ─────────────────────────────────────────────
    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._articles):
            return
        self._selected_idx = idx
        art = self._articles[idx]
        self._show_preview(art)
        for btn in (self.btn_translate, self.btn_read, self.btn_open, self.btn_save):
            btn.config(state="normal")

    def _on_fetch(self):
        if self._busy:
            return
        if not HAS_SCRAPER:
            messagebox.showerror(
                "导入错误 / Import Error",
                f"seo_scraper.py 无法加载：{_IMPORT_ERR}\n\n"
                "请先安装依赖：pip install feedparser beautifulsoup4"
            )
            return
        self._set_busy(True, "正在抓取 RSS... / Fetching RSS...")
        proxy = self.cfg.get("proxy", "")
        t = threading.Thread(target=self._do_fetch, args=(proxy,), daemon=True)
        t.start()

    def _do_fetch(self, proxy: str):
        try:
            raw = fetch_rss_articles(RSS_SOURCES, proxy=proxy)
            filtered = filter_articles(raw, LEARN_KEYWORDS)
            # Deduplicate against read history
            new_articles = [a for a in filtered if a["url"] not in self._read_urls]
            self.result_q.put({
                "type": "fetch_done",
                "articles": new_articles,
                "total_raw": len(raw),
                "total_filtered": len(filtered),
            })
        except Exception as e:
            self.result_q.put({"type": "error", "msg": f"抓取失败: {e}"})

    def _on_translate(self):
        if self._busy or self._selected_idx is None:
            return
        art = self._articles[self._selected_idx]
        api_key = self.cfg.get("claude_api_key", "").strip()
        if not api_key:
            messagebox.showwarning(
                "API Key 缺失 / API Key Missing",
                "请在「设置」中填写 Claude API Key。\n\nPlease enter your Claude API Key in Settings."
            )
            return
        self._set_busy(True, f"正在翻译... / Translating: {art['title'][:40]}")
        proxy = self.cfg.get("proxy", "")
        t = threading.Thread(
            target=self._do_translate,
            args=(self._selected_idx, api_key, proxy),
            daemon=True,
        )
        t.start()

    def _do_translate(self, idx: int, api_key: str, proxy: str):
        import requests as _req
        sess = _req.Session()
        sess.headers.update({"User-Agent": "Mozilla/5.0"})
        if proxy:
            sess.proxies.update({"http": proxy, "https": proxy})
        try:
            art = self._articles[idx]
            updated = translate_article(art, api_key, sess)
            self.result_q.put({"type": "translate_done", "idx": idx, "article": updated})
        except Exception as e:
            self.result_q.put({"type": "error", "msg": f"翻译失败: {e}"})

    def _on_mark_read(self):
        if self._selected_idx is None:
            return
        art = self._articles[self._selected_idx]
        self._read_urls.add(art["url"])
        art["read"] = True
        save_read_history(self.cfg.get("output_dir", str(Path.home() / "Desktop")), self._read_urls)
        self._refresh_list()
        self._log(f"已标记已读: {art['title'][:50]}")

    def _on_open_url(self):
        if self._selected_idx is None:
            return
        url = self._articles[self._selected_idx].get("url", "")
        if url:
            webbrowser.open(url)

    def _on_save_note(self):
        if self._selected_idx is None:
            return
        art = self._articles[self._selected_idx]
        out_dir = self.cfg.get("output_dir", str(Path.home() / "Desktop" / "SEO_学习笔记"))
        try:
            path = save_article(art, out_dir)
            if path:
                self._log(f"已保存笔记: {Path(path).name}")
                messagebox.showinfo(
                    "保存成功 / Saved",
                    f"笔记已保存至 / Note saved to:\n{path}"
                )
        except Exception as e:
            messagebox.showerror("保存失败 / Save Failed", str(e))

    # ─────────────────────────────────────────────
    #  后台任务结果处理
    # ─────────────────────────────────────────────
    def _poll_queue(self):
        try:
            while True:
                msg = self.result_q.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass
        self.root.after(150, self._poll_queue)

    def _handle_message(self, msg: Dict[str, Any]):
        mtype = msg.get("type")

        if mtype == "fetch_done":
            new_arts = msg["articles"]
            self._articles = new_arts
            self._refresh_list()
            self._log(
                f"抓取完成: RSS 共 {msg['total_raw']} 篇, "
                f"过滤后 {msg['total_filtered']} 篇, "
                f"新增 {len(new_arts)} 篇（已去重）"
            )
            self._set_busy(False, "就绪 / Ready")

        elif mtype == "translate_done":
            idx = msg["idx"]
            self._articles[idx] = msg["article"]
            art = self._articles[idx]
            self._refresh_list()
            if idx == self._selected_idx:
                self._show_preview(art)
            status = "成功" if art.get("translated") else "失败（未返回译文）"
            self._log(f"翻译{status}: {art['title'][:50]}")
            self._set_busy(False, "就绪 / Ready")

        elif mtype == "error":
            self._log(f"ERROR: {msg['msg']}")
            self._set_busy(False, "错误 / Error")

    def _set_busy(self, busy: bool, status: str):
        self._busy = busy
        self.status_var.set(status)
        state = "disabled" if busy else "normal"
        self.btn_fetch.config(state=state)
        if not busy and self._selected_idx is not None:
            for btn in (self.btn_translate, self.btn_read, self.btn_open, self.btn_save):
                btn.config(state="normal")

    # ─────────────────────────────────────────────
    #  设置对话框
    # ─────────────────────────────────────────────
    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置 / Settings")
        win.configure(bg=self.BG)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        # ── 辅助函数 ──────────────────────────────
        def _row(parent, label_cn: str, label_en: str, row: int) -> tk.Entry:
            tk.Label(
                parent,
                text=f"{label_cn} / {label_en}",
                bg=self.BG, fg=self.FG2,
                font=("Segoe UI", 9),
                width=22, anchor="w",
            ).grid(row=row, column=0, padx=(12, 4), pady=6, sticky="w")
            entry = tk.Entry(
                parent,
                bg=self.BG2, fg=self.FG,
                insertbackground=self.FG,
                relief="flat", bd=4,
                font=("Segoe UI", 9),
                width=42,
            )
            entry.grid(row=row, column=1, padx=(0, 12), pady=6)
            return entry

        # ── 字段 ──────────────────────────────────
        frm = tk.Frame(win, bg=self.BG)
        frm.pack(padx=4, pady=4)

        e_key = _row(frm, "Claude API Key", "Claude API Key", 0)
        e_key.insert(0, self.cfg.get("claude_api_key", ""))
        e_key.config(show="*")

        e_proxy = _row(frm, "代理地址", "HTTP Proxy", 1)
        e_proxy.insert(0, self.cfg.get("proxy", ""))

        e_outdir = _row(frm, "保存目录", "Output Directory", 2)
        e_outdir.insert(0, self.cfg.get("output_dir", ""))

        # ── 保存按钮 ──────────────────────────────
        def _save():
            self.cfg["claude_api_key"] = e_key.get().strip()
            self.cfg["proxy"]          = e_proxy.get().strip()
            self.cfg["output_dir"]     = e_outdir.get().strip()
            self._save_config()
            key_hint = (self.cfg["claude_api_key"][:8] + "...") if self.cfg["claude_api_key"] else "（未填写）"
            self._log(f"设置已保存 | API Key: {key_hint}")
            win.destroy()

        tk.Button(
            win, text="保存 / Save",
            command=_save,
            bg=self.ACCENT, fg=self.BG,
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=20, pady=6,
            cursor="hand2",
        ).pack(pady=(4, 12))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    root = tk.Tk()
    # 使图标正常显示（Windows任务栏）
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = SEODesktopAgent(root)

    def _on_close():
        # 保存已读历史
        if HAS_SCRAPER:
            try:
                save_read_history(
                    app.cfg.get("output_dir", str(Path.home() / "Desktop")),
                    app._read_urls,
                )
            except Exception:
                pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
