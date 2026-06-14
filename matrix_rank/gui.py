"""tkinter 矩阵秩机器人界面"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import redirect_stdout
from functools import partial
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.delayed_output import DelayedStepWriter
from matrix_rank.parsing import parse_matrix_element
from matrix_rank.workflow import calculate_rank_with_selected_method


MAX_MATRIX_ROWS = 10
MAX_MATRIX_COLS = 10
DEFAULT_STEP_DELAY_MS = 700
STEP_SPEED_DELAYS = {
    "快速": 200,
    "正常": DEFAULT_STEP_DELAY_MS,
    "慢速": 1400,
}
WELCOME_MESSAGE = (
    "你好，我是矩阵分析助手。\n"
    "我可以计算矩阵的秩，并根据矩阵类型补充基础性质和特征信息。\n"
    "秩的计算支持高斯消元法、行列式法和奇异值分解法（SVD）；"
    "详细模式会展示中间计算过程，简洁模式只显示主要结论。\n"
    "对于方阵，我还会给出行列式、可逆性、特征多项式、特征值、"
    "代数重数、几何重数和特征子空间基。\n"
    "矩阵元素支持整数、小数、分数和科学计数法，例如 "
    "2、0.5、3/4、1e12、1e-12。\n"
    "请选择接下来要做什么。"
)


class MatrixGridParseError(ValueError):
    """矩阵表格解析错误，并记录出错单元格位置。"""

    def __init__(self, row_index: int, col_index: int, message: str) -> None:
        super().__init__(message)
        self.row_index = row_index
        self.col_index = col_index


def parse_matrix_grid_values(
    raw_rows: Sequence[Sequence[str]],
) -> list[list[sp.Rational]]:
    """解析矩阵表格中的文本值，并在错误中保留行列位置。"""
    parsed_matrix: list[list[sp.Rational]] = []
    expected_columns: int | None = None

    for row_index, raw_row in enumerate(raw_rows):
        if not raw_row:
            raise ValueError(f"矩阵第 {row_index + 1} 行不能为空。")

        if expected_columns is None:
            expected_columns = len(raw_row)
        elif len(raw_row) != expected_columns:
            raise ValueError("矩阵每一行的元素数量必须一致。")

        parsed_row = []
        for col_index, raw_value in enumerate(raw_row):
            try:
                parsed_row.append(parse_matrix_element(raw_value))
            except ValueError as exc:
                raise MatrixGridParseError(
                    row_index,
                    col_index,
                    str(exc),
                ) from exc
        parsed_matrix.append(parsed_row)

    if not parsed_matrix:
        raise ValueError("矩阵不能为空。")
    return parsed_matrix


def get_dimension_validation_error(rows: int, cols: int) -> str | None:
    """返回矩阵尺寸校验错误；合法时返回 None。"""
    if rows <= 0 or cols <= 0:
        return "行数和列数都必须大于 0。"
    if rows > MAX_MATRIX_ROWS or cols > MAX_MATRIX_COLS:
        return (
            f"当前版本最多支持 {MAX_MATRIX_ROWS} 行、{MAX_MATRIX_COLS} 列。"
            "较大的矩阵可能导致详细计算或特征值计算耗时过长。"
        )
    return None


def get_step_delay_ms(speed_name: str) -> int:
    """返回步骤播放速度对应的延迟毫秒数。"""
    try:
        return STEP_SPEED_DELAYS[speed_name]
    except KeyError as exc:
        raise ValueError("未知的步骤播放速度。") from exc


class MatrixRankRobotApp:
    """使用 tkinter 实现的矩阵秩机器人窗口。"""

    METHOD_NAMES = {
        "1": "高斯消元法",
        "2": "行列式法（适用于小矩阵）",
        "3": "奇异值分解法（SVD）",
    }
    OUTPUT_MODE_NAMES = {
        "detailed": "详细模式",
        "concise": "简洁模式",
    }

    def __init__(
        self,
        root: tk.Tk,
        step_delay_ms: int = DEFAULT_STEP_DELAY_MS,
    ) -> None:
        """初始化机器人窗口和交互状态。"""
        if step_delay_ms < 0:
            raise ValueError("step_delay_ms 不能为负数。")

        self.root = root
        self.root.title("矩阵分析助手")
        self.root.geometry("800x600")
        self.root.minsize(760, 560)

        self.method_choice = ""
        self.output_mode = "detailed"
        self.rows = 0
        self.cols = 0
        self.matrix: list[list[sp.Rational]] = []
        self.matrix_entries: list[list[tk.Entry]] = []
        self.output_queue: queue.Queue[str | None] = queue.Queue()
        self.pending_step_messages: list[str] = []
        self.calculation_finished = False
        self.is_displaying_steps = False
        self.step_delay_ms = step_delay_ms

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
        self.root.unbind("<Return>")
        for widget in self.control_frame.winfo_children():
            widget.destroy()

    def show_welcome(self) -> None:
        """显示项目介绍，并让用户选择计算或退出。"""
        self.clear_controls()
        self.robot_say(WELCOME_MESSAGE)

        tk.Button(self.control_frame, text="开始计算", command=self.show_method_selection).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )
        tk.Button(self.control_frame, text="退出程序", command=self.exit_app).pack(side=tk.LEFT)

    def show_method_selection(self) -> None:
        """显示计算方法选择按钮。"""
        self.user_say("开始计算")
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
        """记录用户选择的方法，并继续选择输出模式。"""
        self.method_choice = method_choice
        self.user_say(self.METHOD_NAMES[method_choice])
        self.show_output_mode_selection()

    def show_output_mode_selection(self) -> None:
        """让用户选择输出模式。"""
        self.clear_controls()
        self.robot_say(
            "请选择输出模式。\n"
            "建议使用详细模式，适合查看完整计算过程；如果只想快速看结论，可以选择简洁模式。"
        )

        tk.Button(
            self.control_frame,
            text="详细模式（推荐）",
            command=self.show_step_speed_selection,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            self.control_frame,
            text="简洁模式",
            command=lambda: self.choose_output_mode("concise"),
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(self.control_frame, text="返回选择方法", command=self.show_method_selection).pack(side=tk.LEFT)

    def set_step_speed(self, speed_name: str) -> None:
        """更新详细模式每一步的显示间隔。"""
        self.step_delay_ms = get_step_delay_ms(speed_name)

    def show_step_speed_selection(self) -> None:
        """仅为详细模式显示步骤播放速度选项。"""
        self.user_say(self.OUTPUT_MODE_NAMES["detailed"])
        self.clear_controls()
        self.robot_say("请选择详细计算步骤的播放速度。")

        for speed_name in STEP_SPEED_DELAYS:
            tk.Button(
                self.control_frame,
                text=speed_name,
                command=partial(self.choose_detailed_speed, speed_name),
            ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            self.control_frame,
            text="返回输出模式",
            command=self.show_output_mode_selection,
        ).pack(side=tk.LEFT)

    def choose_detailed_speed(self, speed_name: str) -> None:
        """记录详细模式播放速度，并继续输入矩阵尺寸。"""
        self.set_step_speed(speed_name)
        self.user_say(f"步骤速度：{speed_name}")
        self.output_mode = "detailed"
        self.show_dimension_input()

    def choose_output_mode(self, output_mode: str) -> None:
        """记录输出模式，并开始读取矩阵尺寸。"""
        self.output_mode = output_mode
        self.user_say(self.OUTPUT_MODE_NAMES[output_mode])
        self.show_dimension_input()

    def show_dimension_input(self) -> None:
        """在窗口中读取矩阵行数和列数。"""
        self.clear_controls()
        self.robot_say(
            "请输入矩阵的行数和列数。行数、列数都必须是正整数，"
            f"且当前版本最多支持 {MAX_MATRIX_ROWS} 行、{MAX_MATRIX_COLS} 列。"
        )

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

        validation_error = get_dimension_validation_error(rows, cols)
        if validation_error is not None:
            messagebox.showerror("输入错误", validation_error)
            return

        self.rows = rows
        self.cols = cols
        self.matrix = []
        self.matrix_entries = []
        self.user_say(f"矩阵大小：{rows} 行 {cols} 列")
        self.show_matrix_grid_input()

    def show_matrix_grid_input(self) -> None:
        """生成矩阵表格，让用户一次性输入所有元素。"""
        self.clear_controls()
        self.robot_say(
            f"请在下面的 {self.rows} 行 {self.cols} 列表格中输入矩阵元素。\n"
            "支持整数、小数、分数和科学计数法，例如：1、-2、0.5、3/4、1e12、1e-12。"
        )

        scroll_container = self._create_scrollable_matrix_container()
        scroll_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        button_frame = tk.Frame(self.control_frame)
        button_frame.pack(side=tk.RIGHT, anchor=tk.N)

        tk.Button(button_frame, text="开始计算", command=self.handle_matrix_grid_submit).pack(
            anchor=tk.W,
            pady=(0, 8),
        )
        tk.Button(button_frame, text="重新选择方法", command=self.show_method_selection).pack(anchor=tk.W)

        if self.matrix_entries and self.matrix_entries[0]:
            self.matrix_entries[0][0].focus_set()
        self.root.bind("<Return>", lambda _event: self.handle_matrix_grid_submit())

    def _create_scrollable_matrix_container(self) -> tk.Frame:
        """创建双向可滚动的矩阵输入容器，避免大矩阵挤出操作按钮。"""
        container = tk.Frame(self.control_frame)
        canvas = tk.Canvas(container, width=560, height=220, highlightthickness=0)
        vertical_scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        horizontal_scrollbar = tk.Scrollbar(container, orient=tk.HORIZONTAL, command=canvas.xview)
        grid_frame = tk.Frame(canvas)

        canvas.create_window((0, 0), window=grid_frame, anchor=tk.NW)
        canvas.configure(
            xscrollcommand=horizontal_scrollbar.set,
            yscrollcommand=vertical_scrollbar.set,
        )

        grid_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox(tk.ALL)),
        )

        canvas.grid(row=0, column=0, sticky=tk.NSEW)
        vertical_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        horizontal_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._bind_mousewheel(canvas, grid_frame)
        self._create_matrix_grid(grid_frame)
        return container

    def _bind_mousewheel(self, canvas: tk.Canvas, scrollable_widget: tk.Widget) -> None:
        """给矩阵输入区域绑定鼠标滚轮。"""
        def on_mousewheel(event: tk.Event) -> None:
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_mousewheel(_event: tk.Event) -> None:
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel(_event: tk.Event) -> None:
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)
        scrollable_widget.bind("<Enter>", bind_mousewheel)
        scrollable_widget.bind("<Leave>", unbind_mousewheel)

    def _create_matrix_grid(self, grid_frame: tk.Frame) -> None:
        """根据矩阵尺寸创建 Entry 表格。"""
        self.matrix_entries = []

        for row_index in range(self.rows):
            tk.Label(grid_frame, text=f"第 {row_index + 1} 行").grid(
                row=row_index,
                column=0,
                padx=(0, 6),
                pady=3,
                sticky=tk.E,
            )

            entry_row = []
            for col_index in range(self.cols):
                entry = tk.Entry(grid_frame, width=10, justify=tk.CENTER)
                entry.grid(row=row_index, column=col_index + 1, padx=3, pady=3)
                entry_row.append(entry)
            self.matrix_entries.append(entry_row)

    def handle_matrix_grid_submit(self) -> None:
        """读取表格中的所有元素，校验通过后启动计算。"""
        parsed_matrix = self._parse_matrix_grid()
        if parsed_matrix is None:
            return

        self.matrix = parsed_matrix
        self.user_say("矩阵输入完成：\n" + self._format_matrix_input_summary(parsed_matrix))
        self.run_selected_calculation()

    def _parse_matrix_grid(self) -> list[list[sp.Rational]] | None:
        """解析整个矩阵表格；发现错误时提示具体行列位置。"""
        raw_rows = [
            [entry.get() for entry in entry_row]
            for entry_row in self.matrix_entries
        ]

        try:
            return parse_matrix_grid_values(raw_rows)
        except MatrixGridParseError as exc:
            messagebox.showerror(
                "输入错误",
                f"第 {exc.row_index + 1} 行第 {exc.col_index + 1} 列输入错误：{exc}",
            )
            self.matrix_entries[exc.row_index][exc.col_index].focus_set()
            return None
        except ValueError as exc:
            messagebox.showerror("输入错误", str(exc))
            return None

    def _format_matrix_input_summary(self, matrix: list[list[sp.Rational]]) -> str:
        """把用户输入的矩阵整理成简洁的聊天记录。"""
        return "\n".join("  ".join(str(value) for value in row) for row in matrix)

    def run_selected_calculation(self) -> None:
        """运行用户选择的计算方法，并把详细过程按 0.7 秒间隔显示在窗口中。"""
        self.clear_controls()
        self.root.unbind("<Return>")
        if self.output_mode == "concise":
            self.robot_say("矩阵输入完成，我现在使用简洁模式计算，只展示关键结论。")
        else:
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
                calculate_rank_with_selected_method(
                    self.method_choice,
                    calculator,
                    output_mode=self.output_mode,
                )

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
