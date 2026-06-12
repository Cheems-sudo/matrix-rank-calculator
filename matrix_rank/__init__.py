"""
矩阵秩计算器包

该包按职责拆分为：
parsing：数字、分数、科学计数法输入解析
calculator：高斯消元法、行列式法、SVD法核心计算
workflow：用户选择方法后的计算流程与结果复核
gui：tkinter机器人界面
delayed_output：GUI分步延迟输出工具

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from matrix_rank.app import main as gui_main
from matrix_rank.calculator import MatrixRankCalculator, SVDUnavailableError
from matrix_rank.cli import main as cli_main
from matrix_rank.eigen import EigenspaceSummary, EigenvalueSummary
from matrix_rank.parsing import parse_matrix_element
from matrix_rank.workflow import get_eigenvalue_summary

if TYPE_CHECKING:
    from matrix_rank.gui import MatrixRankRobotApp

__all__ = [
    "EigenspaceSummary",
    "EigenvalueSummary",
    "MatrixRankCalculator",
    "MatrixRankRobotApp",
    "SVDUnavailableError",
    "cli_main",
    "get_eigenvalue_summary",
    "gui_main",
    "parse_matrix_element",
]


def __getattr__(name: str) -> Any:
    """按需加载 GUI 类型，使无 tkinter 环境仍可导入核心包。"""
    if name == "MatrixRankRobotApp":
        from matrix_rank.gui import MatrixRankRobotApp

        return MatrixRankRobotApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
