"""应用入口"""

from __future__ import annotations

import sys


def main() -> int:
    """启动 tkinter 窗口；图形环境不可用时返回非零状态码。"""
    try:
        import tkinter as tk

        from matrix_rank.gui import MatrixRankRobotApp
    except ImportError:
        print(
            "无法启动图形界面：当前 Python 环境未安装 tkinter。"
            "请安装 tkinter，或改用 matrix-rank 命令行工具。",
            file=sys.stderr,
        )
        return 1

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(
            "无法启动图形界面：未检测到可用的桌面显示环境。"
            "请在图形桌面中运行，或改用 matrix-rank 命令行工具。"
            f"\n详细信息：{exc}",
            file=sys.stderr,
        )
        return 1

    MatrixRankRobotApp(root)
    root.mainloop()
    return 0
