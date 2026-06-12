"""延迟输出工具，用于GUI逐步展示计算过程"""

from __future__ import annotations

import queue
import sys


def start_output_step() -> None:
    """Start a new GUI output step when stdout supports the step protocol."""
    start_step = getattr(sys.stdout, "start_step", None)
    if callable(start_step):
        start_step()


class DelayedStepWriter:
    """把 print 输出按步骤切分后送入队列，供 tkinter 延迟显示。"""

    def __init__(self, output_queue: queue.Queue[str | None]) -> None:
        """初始化输出队列和临时缓冲区。"""
        self.output_queue = output_queue
        self.buffer = ""

    def write(self, text: str) -> int:
        """接收 stdout 文本；步骤边界由 start_step 显式控制。"""
        self.buffer += text
        return len(text)

    def start_step(self) -> None:
        """结束当前步骤并开始下一个步骤。"""
        self.flush()

    def flush(self) -> None:
        """把剩余缓冲内容作为最后一个步骤送入队列。"""
        if self.buffer.strip():
            self.output_queue.put(self.buffer.strip())
            self.buffer = ""
