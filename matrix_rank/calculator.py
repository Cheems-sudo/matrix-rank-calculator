"""矩阵秩计算核心算法"""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations
from typing import Any, Literal, overload

import numpy as np
import sympy as sp

from matrix_rank.delayed_output import start_output_step
from matrix_rank.parsing import parse_matrix_element


class SVDUnavailableError(ValueError):
    """Raised when the exact matrix cannot be represented safely for SVD."""


def format_exact_value(value: object) -> str:
    """安全格式化精确值；超长整数改用科学计数法摘要。"""
    try:
        return str(value)
    except ValueError:
        approximate_value = sp.N(value, 6)
        return f"{approximate_value}（精确值过长，使用近似科学计数法显示）"


class MatrixRankCalculator:
    """提供多种矩阵秩计算方法，并打印详细计算过程。"""

    def __init__(self, matrix: Iterable[Iterable[object]], tol: float = 1e-10) -> None:
        """初始化待计算矩阵。

        Args:
            matrix: 二维可迭代对象，表示输入矩阵。支持整数、小数、分数和科学计数法形式的元素。
            tol: 数值计算中的零判定阈值。绝对值小于等于该阈值的数会被视为 0。
        """
        self.tol = tol
        self.exact_matrix = self._build_exact_matrix(matrix)
        self.matrix = self._build_numeric_matrix()

        if self.matrix.ndim != 2:
            raise ValueError("输入必须是二维矩阵。")

    def _build_exact_matrix(self, matrix: Iterable[Iterable[object]]) -> sp.Matrix:
        """把输入矩阵转换为 sympy 精确矩阵，避免后续计算和显示出现小数。"""
        try:
            return sp.Matrix([[parse_matrix_element(str(value)) for value in row] for row in matrix])
        except TypeError as exc:
            raise ValueError("输入必须是二维矩阵。") from exc
        except ValueError as exc:
            raise ValueError("矩阵元素必须是整数、小数、分数或科学计数法形式的数字。") from exc

    def _build_numeric_matrix(self) -> np.ndarray:
        """构建供 SVD 使用的浮点矩阵，无法表示的元素记为非有限值。"""
        rows, cols = self.exact_matrix.shape
        numeric_matrix = np.empty((rows, cols), dtype=float)

        for row_index in range(rows):
            for col_index in range(cols):
                exact_value = self.exact_matrix[row_index, col_index]
                try:
                    numeric_value = float(exact_value)
                except (OverflowError, TypeError, ValueError):
                    numeric_value = np.nan

                if exact_value != 0 and numeric_value == 0.0:
                    numeric_value = np.nan

                numeric_matrix[row_index, col_index] = numeric_value

        return numeric_matrix

    def _ensure_svd_available(self) -> None:
        """确保矩阵可以用有限浮点数执行 SVD。"""
        if not np.all(np.isfinite(self.matrix)):
            raise SVDUnavailableError(
                "矩阵包含超出浮点数表示范围的元素，无法进行 SVD 数值计算。"
            )

    @overload
    def _compute_svd(self, *, compute_uv: Literal[False]) -> np.ndarray: ...

    @overload
    def _compute_svd(
        self,
        *,
        compute_uv: Literal[True],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]: ...

    def _compute_svd(
        self,
        *,
        compute_uv: bool,
    ) -> np.ndarray | tuple[np.ndarray, np.ndarray, np.ndarray]:
        """执行 SVD，并把 NumPy 收敛错误转换为可降级异常。"""
        self._ensure_svd_available()
        try:
            if compute_uv:
                u, singular_values, vt = np.linalg.svd(
                    self.matrix,
                    full_matrices=True,
                )
                return u, singular_values, vt

            return np.linalg.svd(
                self.matrix,
                full_matrices=True,
                compute_uv=False,
            )
        except np.linalg.LinAlgError as exc:
            raise SVDUnavailableError("SVD 数值分解未收敛。") from exc

    def _format_scalar(self, value: object) -> str:
        """把矩阵中的单个元素格式化成紧凑、易对齐的字符串。

        numpy 的默认打印在元素较多或小数较长时容易显得拥挤；这里会把
        小数近似为分数或根式等精确表达，保证输出中不出现小数。
        """
        if isinstance(value, (float, np.floating, sp.Float)):
            numeric_value = float(value)
            if abs(numeric_value) <= self.tol:
                return "0"
            return str(sp.nsimplify(numeric_value, tolerance=self.tol))

        if isinstance(value, (int, np.integer)):
            return str(value)

        simplified_value = sp.simplify(value)
        return format_exact_value(simplified_value)

    def _format_matrix(self, matrix: np.ndarray | sp.Matrix) -> str:
        """把矩阵格式化为行列分明的文本表格。

        输出时会逐列计算最大宽度，并让同一列中的元素右对齐。这样无论是
        numpy 矩阵还是 sympy 矩阵，都不会挤在一起，行和列的边界更清晰。
        """
        if isinstance(matrix, sp.MatrixBase):
            rows, cols = matrix.shape
            formatted_rows = [
                [self._format_scalar(matrix[row_index, col_index]) for col_index in range(cols)]
                for row_index in range(rows)
            ]
        else:
            array = np.asarray(matrix)
            rows, cols = array.shape
            formatted_rows = [
                [self._format_scalar(array[row_index, col_index]) for col_index in range(cols)]
                for row_index in range(rows)
            ]

        if not formatted_rows:
            return "[]"

        column_widths = [
            max(len(formatted_rows[row_index][col_index]) for row_index in range(rows))
            for col_index in range(cols)
        ]
        aligned_rows = []

        for row in formatted_rows:
            aligned_values = [
                value.rjust(column_widths[col_index]) for col_index, value in enumerate(row)
            ]
            aligned_rows.append("[ " + "  ".join(aligned_values) + " ]")

        return "[\n  " + "\n  ".join(aligned_rows) + "\n]"

    def _format_numeric_scalar(
        self,
        value: float | np.floating[Any],
        precision: int = 6,
        zero_tol: float | None = None,
    ) -> str:
        """格式化 SVD 等数值算法产生的近似值，避免伪装成精确分数。

        SVD 的 U、Sigma、V^T 通常包含无理数或数值近似值。如果强行用
        nsimplify 转成分数/根式，可能会得到很长且不可靠的表达式。这里明确
        使用“≈”和固定有效数字表示近似值，既美观，也不会误导用户以为它是
        精确结果。
        """
        numeric_value = float(value)
        effective_zero_tol = self.tol if zero_tol is None else zero_tol
        if abs(numeric_value) <= effective_zero_tol:
            return "0"

        formatted_value = f"{numeric_value:.{precision}g}"
        return f"≈{formatted_value}"

    def _format_numeric_matrix(
        self,
        matrix: np.ndarray,
        precision: int = 6,
        zero_tol: float | None = None,
    ) -> str:
        """把数值矩阵格式化为行列对齐的近似值表格。"""
        array = np.asarray(matrix, dtype=float)
        rows, cols = array.shape
        formatted_rows = [
            [
                self._format_numeric_scalar(
                    array[row_index, col_index],
                    precision,
                    zero_tol,
                )
                for col_index in range(cols)
            ]
            for row_index in range(rows)
        ]

        if not formatted_rows:
            return "[]"

        column_widths = [
            max(len(formatted_rows[row_index][col_index]) for row_index in range(rows))
            for col_index in range(cols)
        ]
        aligned_rows = []

        for row in formatted_rows:
            aligned_values = [
                value.rjust(column_widths[col_index]) for col_index, value in enumerate(row)
            ]
            aligned_rows.append("[ " + "  ".join(aligned_values) + " ]")

        return "[\n  " + "\n  ".join(aligned_rows) + "\n]"

    def _print_numeric_matrix(
        self,
        matrix: np.ndarray,
        title: str,
        precision: int = 6,
        zero_tol: float | None = None,
    ) -> None:
        """打印 SVD 等数值矩阵，明确标注为近似值并保持行列对齐。"""
        start_output_step()
        print(f"\n{title}（数值近似）")
        print("-" * (len(title) + len("（数值近似）")))
        print(self._format_numeric_matrix(matrix, precision, zero_tol))

    def _default_svd_relative_tolerance(self) -> float:
        """返回 NumPy/MATLAB 常用的 SVD 相对阈值系数。

        固定绝对阈值（例如 1e-10）会把 1e-12 这类“很小但确实非零”的
        奇异值直接判为 0。工程数值秩更常用与矩阵规模和机器精度相关的
        自适应阈值：max(m, n) * eps。最终阈值再乘以最大奇异值形成相对判定。
        """
        rows, cols = self.matrix.shape
        return max(rows, cols) * np.finfo(self.matrix.dtype).eps

    def _calculate_svd_threshold(
        self,
        singular_values: np.ndarray,
        relative_tol: float | None,
        absolute_tol: float,
    ) -> tuple[float, float]:
        """根据奇异值、相对阈值和绝对阈值计算 SVD 判秩阈值。"""
        if absolute_tol < 0:
            raise ValueError("absolute_tol 不能为负数。")

        resolved_relative_tol = (
            self._default_svd_relative_tolerance() if relative_tol is None else relative_tol
        )
        if resolved_relative_tol < 0:
            raise ValueError("relative_tol 不能为负数。")

        max_singular_value = float(np.max(singular_values)) if singular_values.size else 0.0
        threshold = max(absolute_tol, resolved_relative_tol * max_singular_value)
        return threshold, resolved_relative_tol

    def _print_matrix(self, matrix: np.ndarray | sp.Matrix, title: str) -> None:
        """统一打印矩阵状态，方便每一步都带说明，并保持行列对齐。"""
        start_output_step()
        print(f"\n{title}")
        print("-" * len(title))
        print(self._format_matrix(matrix))

    def rank_by_gaussian_elimination(self) -> int:
        """使用高斯消元法计算秩，并打印每次行变换后的矩阵。

        思路：
        - 从左到右扫描每一列，寻找当前列中绝对值最大的非零元素作为主元。
        - 如有必要，交换当前行和主元所在行。
        - 将主元行归一化，使主元变为 1。
        - 消去主元下方同列元素，得到行阶梯形矩阵。
        - 非零行的数量就是矩阵的秩。
        """
        a = self.exact_matrix.copy()
        rows, cols = a.shape
        pivot_row = 0

        self._print_matrix(a, "高斯消元法：初始矩阵")

        for col in range(cols):
            print(f"\n开始处理第 {col + 1} 列，当前主元目标行是第 {pivot_row + 1} 行。")

            # 在当前列、当前主元目标行及其下方寻找绝对值最大的精确主元。
            candidate_rows = range(pivot_row, rows)
            max_row = max(candidate_rows, key=lambda row: abs(a[row, col])) if pivot_row < rows else pivot_row
            max_value = abs(a[max_row, col]) if pivot_row < rows else 0

            if max_value == 0:
                print(f"第 {col + 1} 列在可选行中没有非零主元，跳过该列。")
                continue

            # 如果最大主元不在当前目标行，先交换两行。
            if max_row != pivot_row:
                a.row_swap(pivot_row, max_row)
                self._print_matrix(
                    a,
                    f"交换第 {pivot_row + 1} 行和第 {max_row + 1} 行，使较大元素成为主元",
                )

            # 把主元行归一化，使主元等于 1，便于观察后续消元。
            pivot_value = a[pivot_row, col]
            print(f"选定主元 a[{pivot_row + 1}, {col + 1}] = {self._format_scalar(pivot_value)}。")
            for col_index in range(cols):
                a[pivot_row, col_index] = sp.simplify(a[pivot_row, col_index] / pivot_value)
            self._print_matrix(a, f"第 {pivot_row + 1} 行除以主元 {self._format_scalar(pivot_value)}，主元归一化")

            # 消去主元下方所有行在当前列中的元素。
            for row in range(pivot_row + 1, rows):
                factor = a[row, col]
                if factor == 0:
                    print(f"第 {row + 1} 行在第 {col + 1} 列已经为 0，无需消元。")
                    continue

                for col_index in range(cols):
                    a[row, col_index] = sp.simplify(a[row, col_index] - factor * a[pivot_row, col_index])
                self._print_matrix(
                    a,
                    f"R{row + 1} <- R{row + 1} - ({self._format_scalar(factor)}) * R{pivot_row + 1}，消去第 {col + 1} 列元素",
                )

            pivot_row += 1
            if pivot_row == rows:
                print("所有行都已经成为主元行，消元结束。")
                break

        rank = sum(any(a[row, col] != 0 for col in range(cols)) for row in range(rows))
        self._print_matrix(a, "高斯消元法：最终行阶梯形矩阵")
        print(f"非零行数量为 {rank}，因此矩阵的秩为 {rank}。")
        return rank

    def rank_by_gaussian_elimination_silent(self) -> int:
        """静默计算精确秩，用于在结果汇总中复核高斯消元法结果。"""
        return int(self.exact_matrix.rank())

    def rank_by_determinants_silent(self, max_order: int | None = None) -> int:
        """静默使用子行列式法计算秩，适合小矩阵复核。"""
        sym_matrix = self.exact_matrix.copy()
        rows, cols = sym_matrix.shape
        highest_order = min(rows, cols) if max_order is None else min(max_order, rows, cols)

        for order in range(highest_order, 0, -1):
            for row_indices in combinations(range(rows), order):
                for col_indices in combinations(range(cols), order):
                    sub_matrix = sym_matrix.extract(row_indices, col_indices)
                    determinant = sp.simplify(sub_matrix.det())
                    if determinant != 0:
                        return order

        return 0

    def rank_by_svd_silent(
        self,
        relative_tol: float | None = None,
        absolute_tol: float = 0.0,
    ) -> int:
        """静默使用 SVD 和自适应阈值计算数值秩。"""
        singular_values = self._compute_svd(compute_uv=False)
        threshold, _resolved_relative_tol = self._calculate_svd_threshold(
            singular_values,
            relative_tol,
            absolute_tol,
        )
        return int(np.sum(singular_values > threshold))

    def rank_by_determinants(self, max_order: int | None = None) -> int:
        """使用子行列式法计算秩，并打印每个子矩阵及其行列式。

        重要说明：
        - 矩阵的秩等于非零子行列式的最高阶数。
        - 枚举子行列式的组合数量可能很大，因此该方法主要适用于小矩阵。
        - 本方法使用 sympy 进行符号/精确计算，使每个行列式结果更可靠、更易展示。

        Args:
            max_order: 允许枚举的最高阶数；默认枚举到 min(行数, 列数)。
        """
        sym_matrix = self.exact_matrix.copy()
        rows, cols = sym_matrix.shape
        highest_order = min(rows, cols) if max_order is None else min(max_order, rows, cols)

        self._print_matrix(sym_matrix, "行列式法：初始矩阵")
        print("矩阵的秩等于所有非零子行列式中的最高阶数。")

        # 从高阶到低阶检查，一旦发现非零子行列式即可确定秩。
        for order in range(highest_order, 0, -1):
            print(f"\n开始检查所有 {order} 阶子行列式。")
            for row_indices in combinations(range(rows), order):
                for col_indices in combinations(range(cols), order):
                    sub_matrix = sym_matrix.extract(row_indices, col_indices)
                    determinant = sp.simplify(sub_matrix.det())

                    print(f"选择行 {[i + 1 for i in row_indices]}、列 {[j + 1 for j in col_indices]} 得到子矩阵：")
                    self._print_matrix(sub_matrix, "当前子矩阵")
                    print(f"该子矩阵的行列式 = {determinant}")

                    if determinant != 0:
                        print(f"发现非零 {order} 阶子行列式，因此矩阵的秩为 {order}。")
                        return order

            print(f"所有 {order} 阶子行列式均为 0，继续检查更低阶。")

        print("所有元素均为 0，因此矩阵的秩为 0。")
        return 0

    def rank_by_svd(
        self,
        relative_tol: float | None = None,
        absolute_tol: float = 0.0,
    ) -> int:
        """使用奇异值分解 SVD 计算数值秩，并打印分解结果和判定过程。

        思路：
        - 对矩阵 A 做分解 A = U * S * V^T。
        - S 中的奇异值反映矩阵在线性空间各方向上的伸缩程度。
        - 不再使用固定 tol = 1e-10 判秩；默认采用
          threshold = max(absolute_tol, max(m, n) * eps * 最大奇异值)。
        - 如果工程数据含噪声，可以传入更大的 relative_tol 或 absolute_tol；
          如果日常作业需要尽可能保留很小但非零的奇异值，可以保持默认值。
        """
        self._print_matrix(self.exact_matrix, "SVD 法：初始矩阵")

        u, singular_values, vt = self._compute_svd(compute_uv=True)
        sigma = np.zeros_like(self.matrix, dtype=float)
        np.fill_diagonal(sigma, singular_values)
        threshold, resolved_relative_tol = self._calculate_svd_threshold(
            singular_values,
            relative_tol,
            absolute_tol,
        )

        print("SVD 是数值分解方法；\n下面的 U、Sigma、V^T 和奇异值均用 ≈ 标注为近似值，避免把近似数误写成复杂分数或根式。")
        print("")
        print(
            "当前阈值 = max(absolute_tol, relative_tol * 最大奇异值)；\n"
            f"relative_tol {self._format_numeric_scalar(resolved_relative_tol, zero_tol=0.0)}，\n"
            f"absolute_tol {self._format_numeric_scalar(absolute_tol, zero_tol=0.0)}，\n"
            f"最终阈值 {self._format_numeric_scalar(threshold, zero_tol=0.0)}。"
        )
        self._print_numeric_matrix(u, "SVD 法：左奇异向量矩阵 U", zero_tol=threshold)
        self._print_numeric_matrix(sigma, "SVD 法：奇异值矩阵 Sigma", zero_tol=threshold)
        self._print_numeric_matrix(vt, "SVD 法：右奇异向量转置矩阵 V^T", zero_tol=threshold)

        print("\n逐个检查奇异值是否大于自适应阈值：")
        rank = 0
        threshold_text = self._format_numeric_scalar(threshold, zero_tol=0.0)
        for index, value in enumerate(singular_values, start=1):
            is_nonzero = value > threshold
            status = "计入秩" if is_nonzero else "视为数值 0，不计入秩"
            print(
                f"第 {index} 个奇异值 "
                f"{self._format_numeric_scalar(value, zero_tol=threshold)}，"
                f"自适应阈值 {threshold_text}，{status}。"
            )
            rank += int(is_nonzero)

        print(f"大于自适应阈值的奇异值数量为 {rank}，因此矩阵的数值秩为 {rank}。")
        return rank
