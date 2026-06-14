"""矩阵秩计算器命令行入口。"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
from collections.abc import Sequence
from typing import Any

import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator, SVDUnavailableError
from matrix_rank.formatting import format_exact_value
from matrix_rank.version import __version__
from matrix_rank.workflow import (
    calculate_rank_with_selected_method,
    get_eigenvalue_summary,
)


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
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "-r",
        "--row",
        action="append",
        dest="rows",
        help='矩阵的一行，可用空格或逗号分隔，例如 --row "1 2 3"。',
    )
    input_group.add_argument(
        "-f",
        "--file",
        type=Path,
        help="从 UTF-8 CSV 或文本文件读取矩阵，每行表示矩阵的一行。",
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
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="output_format",
        help="输出格式，默认 text。",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="把结果写入指定文件；默认输出到终端。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _read_raw_rows(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[str]:
    """根据 CLI 参数从行参数、文件或标准输入读取矩阵行。"""
    if args.rows is not None:
        return list(args.rows)

    if args.file is not None:
        try:
            file_text = args.file.read_text(encoding="utf-8-sig")
        except OSError as exc:
            parser.error(f"无法读取矩阵文件：{exc}")
        return [line for line in file_text.splitlines() if line.strip()]

    if sys.stdin.isatty():
        parser.error("请使用 --row、--file 提供矩阵，或通过标准输入传入每行数据。")
    return [line for line in sys.stdin.read().splitlines() if line.strip()]


def _json_scalar(value: sp.Expr) -> dict[str, str]:
    """把精确 SymPy 标量转换为可脚本处理的 JSON 字段。"""
    return {
        "exact": format_exact_value(value),
        "approximate": str(sp.N(value, 10)),
    }


def build_json_result(
    calculator: MatrixRankCalculator,
    method: str,
) -> dict[str, Any]:
    """构建不依赖人类文本输出的结构化计算结果。"""
    rows, cols = calculator.exact_matrix.shape
    exact_rank = calculator.rank_by_sympy_builtin()
    try:
        svd_rank = calculator.rank_by_svd_without_output()
        svd_error = None
    except SVDUnavailableError as exc:
        svd_rank = None
        svd_error = str(exc)

    is_square = rows == cols
    determinant = (
        sp.simplify(calculator.exact_matrix.det())
        if is_square
        else None
    )
    eigen_summary = get_eigenvalue_summary(calculator)
    eigenspaces_by_value = {
        eigenspace.eigenvalue: eigenspace
        for eigenspace in eigen_summary.eigenspaces
    }
    eigenvalues = []
    for eigenvalue, algebraic_multiplicity in eigen_summary.eigenvalues:
        eigenspace = eigenspaces_by_value[eigenvalue]
        eigenvalues.append(
            {
                **_json_scalar(eigenvalue),
                "algebraic_multiplicity": algebraic_multiplicity,
                "geometric_multiplicity": eigenspace.geometric_multiplicity,
                "basis": [
                    [format_exact_value(value) for value in vector]
                    for vector in eigenspace.eigenvectors
                ],
            }
        )

    return {
        "version": __version__,
        "requested_method": method,
        "exact_algorithm": "sympy_builtin",
        "shape": [rows, cols],
        "matrix": [
            [
                format_exact_value(calculator.exact_matrix[row, col])
                for col in range(cols)
            ]
            for row in range(rows)
        ],
        "rank": {
            "exact": exact_rank,
            "svd": svd_rank,
            "svd_error": svd_error,
        },
        "properties": {
            "is_square": is_square,
            "is_full_rank": exact_rank == min(rows, cols),
            "determinant": (
                format_exact_value(determinant)
                if determinant is not None
                else None
            ),
            "is_invertible": (
                determinant != 0
                if determinant is not None
                else None
            ),
        },
        "eigen": {
            "applicable": eigen_summary.is_square,
            "characteristic_polynomial": (
                format_exact_value(eigen_summary.characteristic_polynomial)
                if eigen_summary.characteristic_polynomial is not None
                else None
            ),
            "values": eigenvalues,
            "message": eigen_summary.message,
        },
    }


def _write_result(content: str, output_path: Path | None) -> None:
    """把结果写到终端或 UTF-8 文件。"""
    if output_path is None:
        print(content, end="" if content.endswith("\n") else "\n")
        return

    output_path.write_text(content, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """运行命令行工具并返回进程退出码。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        raw_rows = _read_raw_rows(args, parser)
        matrix = parse_matrix_rows(raw_rows)
        calculator = MatrixRankCalculator(matrix)
        if args.output_format == "json":
            content = json.dumps(
                build_json_result(calculator, args.method),
                ensure_ascii=False,
                indent=2,
            )
            _write_result(content, args.output)
        elif args.output is not None:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                calculate_rank_with_selected_method(
                    METHOD_CHOICES[args.method],
                    calculator,
                    output_mode=args.mode,
                )
            content = buffer.getvalue()
            _write_result(content, args.output)
        else:
            calculate_rank_with_selected_method(
                METHOD_CHOICES[args.method],
                calculator,
                output_mode=args.mode,
            )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    return 0


if __name__ == "__main__":
    sys.exit(main())
