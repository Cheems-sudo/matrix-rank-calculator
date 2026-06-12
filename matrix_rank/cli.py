"""矩阵秩计算器命令行入口。"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.workflow import calculate_rank_with_selected_method


METHOD_CHOICES = {
    "gaussian": "1",
    "determinant": "2",
    "svd": "3",
}


def parse_matrix_rows(raw_rows: Sequence[str]) -> list[list[str]]:
    """解析由空格或逗号分隔的矩阵行，并校验各行长度。"""
    matrix: list[list[str]] = []

    for raw_row in raw_rows:
        values = [value for value in re.split(r"[\s,]+", raw_row.strip()) if value]
        if not values:
            raise ValueError("矩阵行不能为空。")
        matrix.append(values)

    if not matrix:
        raise ValueError("请至少提供一行矩阵数据。")

    column_count = len(matrix[0])
    if any(len(row) != column_count for row in matrix):
        raise ValueError("矩阵每一行的元素数量必须一致。")

    return matrix


def build_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="matrix-rank",
        description="计算矩阵的精确秩、数值秩和方阵特征信息。",
    )
    parser.add_argument(
        "-r",
        "--row",
        action="append",
        dest="rows",
        help='矩阵的一行，可用空格或逗号分隔，例如 --row "1 2 3"。',
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=tuple(METHOD_CHOICES),
        default="gaussian",
        help="详细模式使用的计算方法，默认 gaussian。",
    )
    parser.add_argument(
        "--mode",
        choices=("concise", "detailed"),
        default="concise",
        help="输出模式，默认 concise。",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """运行命令行工具并返回进程退出码。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    raw_rows = args.rows
    if raw_rows is None:
        if sys.stdin.isatty():
            parser.error("请使用 --row 提供矩阵，或通过标准输入传入每行数据。")
        raw_rows = [line for line in sys.stdin.read().splitlines() if line.strip()]

    try:
        matrix = parse_matrix_rows(raw_rows)
        calculator = MatrixRankCalculator(matrix)
        calculate_rank_with_selected_method(
            METHOD_CHOICES[args.method],
            calculator,
            output_mode=args.mode,
        )
    except ValueError as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":
    sys.exit(main())
