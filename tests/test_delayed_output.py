import queue

from matrix_rank.delayed_output import DelayedStepWriter


def test_writer_preserves_blank_lines_inside_explicit_step():
    output_queue: queue.Queue[str | None] = queue.Queue()
    writer = DelayedStepWriter(output_queue)

    writer.write("第一段\n\n仍属于第一步")
    writer.start_step()

    assert output_queue.get_nowait() == "第一段\n\n仍属于第一步"


def test_writer_splits_only_when_start_step_is_called():
    output_queue: queue.Queue[str | None] = queue.Queue()
    writer = DelayedStepWriter(output_queue)

    writer.write("第一步")
    writer.start_step()
    writer.write("第二步")
    writer.flush()

    assert output_queue.get_nowait() == "第一步"
    assert output_queue.get_nowait() == "第二步"
