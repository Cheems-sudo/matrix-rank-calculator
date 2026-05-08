"""应用入口"""

from __future__ import annotations

import tkinter as tk

from matrix_rank.gui import MatrixRankRobotApp


def main() -> None:
    """启动tkinter窗口，让机器人引导用户完成计算。"""
    root = tk.Tk()
    MatrixRankRobotApp(root)
    root.mainloop()
