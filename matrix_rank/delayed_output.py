"""延迟输出工具，用于GUI逐步展示计算过程"""

from __future__ import annotations

import queue


class DelayedStepWriter:
    """把 print 输出按步骤切分后送入队列，供 tkinter 延迟显示。"""

    def __init__(self, output_queue: queue.Queue[str | None]) -> None:
        """初始化输出队列和临时缓冲区。"""
        self.output_queue = output_queue
        self.buffer = ""

    def write(self, text: str) -> int:
        """接收 stdout 文本，并在遇到空行时认为一个计算步骤结束。"""
        self.buffer += text

        while "\n\n" in self.buffer:
            step_text, self.buffer = self.buffer.split("\n\n", 1)
            if step_text.strip():
                self.output_queue.put(step_text.strip())

        return len(text)

    def flush(self) -> None:
        """把剩余缓冲内容作为最后一个步骤送入队列。"""
        if self.buffer.strip():
            self.output_queue.put(self.buffer.strip())
            self.buffer = ""
