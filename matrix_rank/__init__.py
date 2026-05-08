"""
矩阵秩计算器包

该包按职责拆分为：
parsing：数字、分数、科学计数法输入解析
calculator：高斯消元法、行列式法、SVD法核心计算
workflow：用户选择方法后的计算流程与结果复核
gui：tkinter机器人界面
delayed_output：GUI分步延迟输出工具

"""

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.gui import MatrixRankRobotApp
from matrix_rank.parsing import parse_matrix_element

__all__ = ["MatrixRankCalculator", "MatrixRankRobotApp", "parse_matrix_element"]
