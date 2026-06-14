"""
矩阵秩计算器包

该包按职责拆分为：
parsing：数字、分数、科学计数法输入解析
calculator：高斯消元法、行列式法、SVD 法核心计算
eigen：精确特征多项式、特征值和特征子空间计算
formatting：矩阵和数学表达式格式化
workflow：用户选择方法后的计算流程与结果复核
cli：命令行参数、文件输入和结构化输出
gui：tkinter 图形界面
app：GUI 应用启动逻辑
delayed_output：GUI 分步延迟输出工具
version：项目版本信息

"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from matrix_rank.calculator import MatrixRankCalculator, SVDUnavailableError
from matrix_rank.eigen import EigenspaceSummary, EigenvalueSummary
from matrix_rank.parsing import parse_matrix_element
from matrix_rank.version import __version__
from matrix_rank.workflow import get_eigenvalue_summary

if TYPE_CHECKING:
    from matrix_rank.gui import MatrixRankRobotApp

__all__ = [
    "EigenspaceSummary",
    "EigenvalueSummary",
    "MatrixRankCalculator",
    "MatrixRankRobotApp",
    "SVDUnavailableError",
    "__version__",
    "cli_main",
    "get_eigenvalue_summary",
    "gui_main",
    "parse_matrix_element",
]


def gui_main() -> int:
    """按需加载并启动 GUI 入口。"""
    from matrix_rank.app import main

    return main()


def cli_main(argv: Sequence[str] | None = None) -> int:
    """按需加载并启动命令行入口。"""
    from matrix_rank.cli import main

    return main(argv)


def __getattr__(name: str) -> Any:
    """按需加载 GUI 类型，使无 tkinter 环境仍可导入核心包。"""
    if name == "MatrixRankRobotApp":
        from matrix_rank.gui import MatrixRankRobotApp

        return MatrixRankRobotApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
