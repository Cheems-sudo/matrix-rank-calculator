"""tkinter 矩阵秩机器人界面"""

from __future__ import annotations

from contextlib import redirect_stdout
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.delayed_output import DelayedStepWriter
from matrix_rank.parsing import parse_matrix_element
from matrix_rank.workflow import calculate_rank_with_selected_method


class MatrixRankRobotApp:
    """使用 tkinter 实现的矩阵秩机器人窗口。"""

    METHOD_NAMES = {
        "1": "高斯消元法",
        "2": "行列式法（适用于小矩阵）",
        "3": "奇异值分解法（SVD）",
    }

    def __init__(self, root: tk.Tk) -> None:
        """初始化机器人窗口和交互状态。"""
        self.root = root
        self.root.title("计算矩阵秩的机器人")
        self.root.geometry("800x600")
        self.root.minsize(760, 560)

        self.method_choice = ""
        self.rows = 0
        self.cols = 0
        self.matrix: list[list[sp.Rational]] = []
        self.current_row_index = 0
        self.output_queue: queue.Queue[str | None] = queue.Queue()
        self.pending_step_messages: list[str] = []
        self.calculation_finished = False
        self.is_displaying_steps = False
        self.step_delay_ms = 700

        self.chat_log = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Microsoft YaHei UI", 11),
            state=tk.DISABLED,
            padx=12,
            pady=12,
        )
        self.chat_log.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8))

        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        self.show_welcome()

    def robot_say(self, message: str) -> None:
        """在聊天窗口中显示机器人消息。"""
        self._append_chat_message("机器人", message)

    def user_say(self, message: str) -> None:
        """在聊天窗口中显示用户消息。"""
        self._append_chat_message("用户", message)

    def _append_chat_message(self, speaker: str, message: str) -> None:
        """把一条聊天消息追加到窗口，并自动滚动到底部。"""
        self.chat_log.configure(state=tk.NORMAL)
        self.chat_log.insert(tk.END, f"{speaker}：{message}\n\n")
        self.chat_log.configure(state=tk.DISABLED)
        self.chat_log.see(tk.END)

    def robot_say_step(self, message: str) -> None:
        """显示一个延迟输出的计算步骤。"""
        self._append_chat_message("机器人", message)

    def clear_controls(self) -> None:
        """清空底部操作区，便于进入下一步交互。"""
        for widget in self.control_frame.winfo_children():
            widget.destroy()

    def show_welcome(self) -> None:
        """显示项目介绍，并让用户选择计算或退出。"""
        self.clear_controls()
        self.robot_say(
            "你好，我是计算矩阵秩的机器人。\n"
            "我可以计算矩阵的秩，并展示详细的中间计算过程。\n"
            "我支持三种方法：高斯消元法、行列式法和奇异值分解法（SVD）。\n"
            "你可以输入整数、小数、分数或科学计数法，例如 2、0.5、3/4、1e12、1e-12；我会尽量用分数显示结果，避免小数。\n"
            "请选择接下来要做什么。"
        )

        tk.Button(self.control_frame, text="计算矩阵秩", command=self.show_method_selection).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )
        tk.Button(self.control_frame, text="退出程序", command=self.exit_app).pack(side=tk.LEFT)

    def show_method_selection(self) -> None:
        """显示计算方法选择按钮。"""
        self.user_say("计算矩阵秩")
        self.clear_controls()
        self.robot_say("请选择一种计算方法。")

        tk.Button(
            self.control_frame,
            text="高斯消元法",
            command=lambda: self.choose_method("1"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            self.control_frame,
            text="行列式法（小矩阵）",
            command=lambda: self.choose_method("2"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            self.control_frame,
            text="SVD 法",
            command=lambda: self.choose_method("3"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(self.control_frame, text="返回主菜单", command=self.show_welcome).pack(side=tk.LEFT)

    def choose_method(self, method_choice: str) -> None:
        """记录用户选择的方法，并开始读取矩阵尺寸。"""
        self.method_choice = method_choice
        self.user_say(self.METHOD_NAMES[method_choice])
        self.show_dimension_input()

    def show_dimension_input(self) -> None:
        """在窗口中读取矩阵行数和列数。"""
        self.clear_controls()
        self.robot_say("请输入矩阵的行数和列数。行数、列数都必须是正整数。")

        tk.Label(self.control_frame, text="行数：").pack(side=tk.LEFT)
        rows_entry = tk.Entry(self.control_frame, width=8)
        rows_entry.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(self.control_frame, text="列数：").pack(side=tk.LEFT)
        cols_entry = tk.Entry(self.control_frame, width=8)
        cols_entry.pack(side=tk.LEFT, padx=(0, 12))

        def submit_dimensions() -> None:
            self.handle_dimension_input(rows_entry.get(), cols_entry.get())

        tk.Button(self.control_frame, text="确认", command=submit_dimensions).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(self.control_frame, text="返回选择方法", command=self.show_method_selection).pack(side=tk.LEFT)
        rows_entry.focus_set()
        self.root.bind("<Return>", lambda _event: submit_dimensions())

    def handle_dimension_input(self, rows_text: str, cols_text: str) -> None:
        """校验并保存矩阵尺寸。"""
        try:
            rows = int(rows_text.strip())
            cols = int(cols_text.strip())
        except ValueError:
            messagebox.showerror("输入错误", "行数和列数必须是正整数，例如 3。")
            return

        if rows <= 0 or cols <= 0:
            messagebox.showerror("输入错误", "行数和列数都必须大于 0。")
            return

        self.rows = rows
        self.cols = cols
        self.matrix = []
        self.current_row_index = 0
        self.user_say(f"矩阵大小：{rows} 行 {cols} 列")
        self.show_row_input()

    def show_row_input(self) -> None:
        """逐行读取矩阵元素。"""
        self.clear_controls()
        row_number = self.current_row_index + 1
        self.robot_say(
            f"请输入第 {row_number} 行，共 {self.cols} 个数字，用空格分隔。\n"
            "支持整数、小数、分数和科学计数法，例如：1、-2、0.5、3/4、1e12、1e-12。"
        )

        row_entry = tk.Entry(self.control_frame, width=70)
        row_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        def submit_row() -> None:
            self.handle_row_input(row_entry.get())

        tk.Button(self.control_frame, text="提交本行", command=submit_row).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(self.control_frame, text="重新开始", command=self.show_method_selection).pack(side=tk.LEFT)
        row_entry.focus_set()
        self.root.bind("<Return>", lambda _event: submit_row())

    def handle_row_input(self, raw_row: str) -> None:
        """校验并保存当前输入行。"""
        parts = raw_row.strip().split()
        row_number = self.current_row_index + 1

        if len(parts) != self.cols:
            messagebox.showerror(
                "输入错误",
                f"第 {row_number} 行需要 {self.cols} 个数字，但你输入了 {len(parts)} 个。",
            )
            return

        try:
            row = [parse_matrix_element(part) for part in parts]
        except ValueError:
            messagebox.showerror("输入错误", "矩阵元素必须是整数、小数、分数或科学计数法，例如 1、-2、0.5、3/4、1e12、1e-12。")
            return

        self.matrix.append(row)
        self.user_say(f"第 {row_number} 行：{'  '.join(str(value) for value in row)}")
        self.current_row_index += 1

        if self.current_row_index < self.rows:
            self.show_row_input()
            return

        self.run_selected_calculation()

    def run_selected_calculation(self) -> None:
        """运行用户选择的计算方法，并把详细过程按 0.7 秒间隔显示在窗口中。"""
        self.clear_controls()
        self.root.unbind("<Return>")
        self.robot_say("矩阵输入完成，我现在开始计算。每个步骤会间隔约 0.7 秒显示，方便你逐步查看。")

        self.output_queue = queue.Queue()
        self.pending_step_messages = []
        self.calculation_finished = False
        self.is_displaying_steps = False

        calculation_thread = threading.Thread(target=self.calculate_in_background, daemon=True)
        calculation_thread.start()
        self.root.after(100, self.poll_calculation_output)

    def calculate_in_background(self) -> None:
        """在后台线程执行计算，避免窗口在计算过程中卡住。"""
        try:
            calculator = MatrixRankCalculator(self.matrix, tol=1e-10)
            writer = DelayedStepWriter(self.output_queue)

            with redirect_stdout(writer):
                calculate_rank_with_selected_method(self.method_choice, calculator)

            writer.flush()
        except Exception as exc:  # noqa: BLE001 - 需要把后台线程错误展示给用户
            self.output_queue.put(f"计算过程中出现错误：{exc}")
        finally:
            self.output_queue.put(None)

    def poll_calculation_output(self) -> None:
        """从后台计算队列读取步骤，并启动延迟显示。"""
        while True:
            try:
                message = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if message is None:
                self.calculation_finished = True
            else:
                self.pending_step_messages.append(message)

        if not self.is_displaying_steps and self.pending_step_messages:
            self.display_next_step_message()

        if not self.calculation_finished or self.pending_step_messages or self.is_displaying_steps:
            self.root.after(100, self.poll_calculation_output)
        else:
            self.show_after_calculation_options()

    def display_next_step_message(self) -> None:
        """每隔 step_delay_ms 显示一个计算步骤。"""
        if not self.pending_step_messages:
            self.is_displaying_steps = False
            return

        self.is_displaying_steps = True
        message = self.pending_step_messages.pop(0)
        self.robot_say_step(message)

        self.root.after(self.step_delay_ms, self.display_next_step_message)

    def show_after_calculation_options(self) -> None:
        """计算结束后，让用户选择继续计算或退出。"""
        self.clear_controls()
        self.robot_say("本次计算完成。你可以继续计算新的矩阵，或退出程序。")
        tk.Button(self.control_frame, text="继续计算", command=self.show_method_selection).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )
        tk.Button(self.control_frame, text="退出程序", command=self.exit_app).pack(side=tk.LEFT)

    def exit_app(self) -> None:
        """退出机器人窗口。"""
        self.user_say("退出程序")
        self.robot_say("感谢使用矩阵秩机器人，再见！")
        self.root.after(500, self.root.destroy)