"""
飞书 Agent 图形化启动器
双击运行，弹出功能菜单，不会出现黑色终端窗口
依赖：Python 标准库（tkinter）
"""
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

CLR_BG = "#F0F4FF"
CLR_CARD = "#FFFFFF"
CLR_BLUE = "#3370FF"
CLR_TEXT = "#1F2329"
CLR_GRAY = "#8F959E"
CLR_BORDER = "#DEE0E3"


def run_cmd(cmd_args, output_widget):
    def _run():
        output_widget.config(state="normal")
        output_widget.delete(1.0, tk.END)
        output_widget.insert(tk.END, f"▶ 执行: {' '.join(cmd_args)}\n{'─'*60}\n")
        output_widget.config(state="disabled")
        env = os.environ.copy()
        env["PYTHONHTTPSVERIFY"] = "0"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            proc = subprocess.Popen(
                cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=BASE_DIR, env=env, encoding="utf-8", errors="replace",
            )
            for line in proc.stdout:
                output_widget.config(state="normal")
                output_widget.insert(tk.END, line)
                output_widget.see(tk.END)
                output_widget.config(state="disabled")
            proc.wait()
            output_widget.config(state="normal")
            output_widget.insert(tk.END, f"\n{'─'*60}\n✅ 完成（退出码 {proc.returncode}）\n")
        except Exception as e:
            output_widget.config(state="normal")
            output_widget.insert(tk.END, f"\n❌ 错误: {e}\n")
        finally:
            output_widget.config(state="disabled")
            output_widget.see(tk.END)
    threading.Thread(target=_run, daemon=True).start()


class FeishuAgentLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("飞书 Agent 控制台")
        self.geometry("800x560")
        self.configure(bg=CLR_BG)
        ico = os.path.join(BASE_DIR, "feishu_agent.ico")
        if os.path.exists(ico):
            try:
                self.iconbitmap(ico)
            except Exception:
                pass
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg=CLR_BLUE, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🤖  飞书 Agent 智能管理中心",
                 bg=CLR_BLUE, fg="white", font=("微软雅黑", 14, "bold")).pack(side="left", padx=20)
        tk.Label(header, text="by Claude AI",
                 bg=CLR_BLUE, fg="#A8C4FF", font=("微软雅黑", 9)).pack(side="right", padx=20)

        body = tk.Frame(self, bg=CLR_BG)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        left = tk.Frame(body, bg=CLR_BG, width=200)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._output = scrolledtext.ScrolledText(
            body, state="disabled", wrap="word",
            bg="#1E1E2E", fg="#CDD6F4", font=("Consolas", 9),
            relief="flat", bd=0,
        )
        self._output.pack(side="right", fill="both", expand=True)

        sections = [
            ("📚 Wiki 整理", [
                ("扫描 & 整理（预览）", [PYTHON, "main.py", "organize", "--dry-run"]),
                ("扫描 & 整理（执行）", [PYTHON, "main.py", "organize"]),
                ("列出 Wiki 空间",     [PYTHON, "main.py", "list-spaces"]),
            ]),
            ("🧹 Wiki 清理", [
                ("预览需清理的节点",   [PYTHON, "cleanup_wiki.py", "--list"]),
                ("移动文档到根目录",   [PYTHON, "cleanup_wiki.py", "--move"]),
                ("移动 + 删除空目录", [PYTHON, "cleanup_wiki.py", "--move", "--delete"]),
            ]),
            ("📅 日历 & 消息", [
                ("查看日历事件",       [PYTHON, "main.py", "manage", "calendar"]),
                ("查看 IM 消息",       [PYTHON, "main.py", "manage", "messages"]),
                ("查看邮件",           [PYTHON, "main.py", "manage", "email"]),
            ]),
            ("🐙 GitHub 导入", [
                ("导入 GitHub 仓库",   [PYTHON, "main.py", "import-github"]),
            ]),
        ]

        for section_name, buttons in sections:
            tk.Label(left, text=section_name, bg=CLR_BG, fg=CLR_GRAY,
                     font=("微软雅黑", 8, "bold"), anchor="w").pack(fill="x", padx=4, pady=(10, 2))
            for label, cmd in buttons:
                btn = tk.Button(
                    left, text=label, bg=CLR_CARD, fg=CLR_TEXT,
                    activebackground=CLR_BLUE, activeforeground="white",
                    relief="flat", font=("微软雅黑", 9),
                    anchor="w", padx=8, pady=5, cursor="hand2",
                    command=lambda c=cmd: run_cmd(c, self._output),
                )
                btn.pack(fill="x", pady=1, padx=2)

        tk.Frame(self, bg=CLR_BORDER, height=1).pack(fill="x")
        foot = tk.Frame(self, bg=CLR_BG, pady=4)
        foot.pack(fill="x")
        tk.Label(foot, text=f"Python: {sys.version.split()[0]}   |   {BASE_DIR}",
                 bg=CLR_BG, fg=CLR_GRAY, font=("微软雅黑", 8)).pack(side="left", padx=12)
        tk.Button(foot, text="清空输出", bg=CLR_BG, fg=CLR_GRAY,
                  relief="flat", font=("微软雅黑", 8), cursor="hand2",
                  command=lambda: (
                      self._output.config(state="normal"),
                      self._output.delete(1.0, tk.END),
                      self._output.config(state="disabled"),
                  )).pack(side="right", padx=12)


if __name__ == "__main__":
    FeishuAgentLauncher().mainloop()
