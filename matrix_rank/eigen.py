"""Eigenvalue helpers for exact symbolic matrix calculations."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp


NON_SQUARE_EIGENVALUE_MESSAGE = "非方阵没有特征值。"
EIGENVALUE_UNAVAILABLE_MESSAGE = "当前矩阵的精确特征值暂不可计算。"
MAX_EIGENVALUE_ORDER = 6


@dataclass(frozen=True)
class EigenspaceSummary:
    """Exact eigenvectors spanning one eigenspace."""

    eigenvalue: sp.Expr
    algebraic_multiplicity: int
    eigenvectors: tuple[tuple[sp.Expr, ...], ...]

    @property
    def geometric_multiplicity(self) -> int:
        """Return the dimension of the eigenspace."""
        return len(self.eigenvectors)


@dataclass(frozen=True)
class EigenvalueSummary:
    """Exact characteristic polynomial and eigenvalues for a matrix."""

    is_square: bool
    characteristic_polynomial: sp.Expr | None
    eigenvalues: tuple[tuple[sp.Expr, int], ...]
    eigenspaces: tuple[EigenspaceSummary, ...] = ()
    message: str | None = None


def get_eigenvalue_summary(matrix: sp.MatrixBase) -> EigenvalueSummary:
    """Return exact eigenvalue information for a square matrix."""
    rows, cols = matrix.shape
    if rows != cols:
        return EigenvalueSummary(
            is_square=False,
            characteristic_polynomial=None,
            eigenvalues=(),
            message=NON_SQUARE_EIGENVALUE_MESSAGE,
        )

    if rows > MAX_EIGENVALUE_ORDER:
        return EigenvalueSummary(
            is_square=True,
            characteristic_polynomial=None,
            eigenvalues=(),
            message=(
                f"为避免符号计算耗时过长，当前仅计算不超过 "
                f"{MAX_EIGENVALUE_ORDER} 阶方阵的精确特征值。"
            ),
        )

    try:
        lambda_symbol = sp.Symbol("lambda")
        characteristic_polynomial = sp.expand(matrix.charpoly(lambda_symbol).as_expr())
        eigenvector_data = sorted(
            matrix.eigenvects(),
            key=lambda item: sp.default_sort_key(item[0]),
        )
        eigenspaces = tuple(
            EigenspaceSummary(
                eigenvalue=eigenvalue,
                algebraic_multiplicity=algebraic_multiplicity,
                eigenvectors=tuple(
                    tuple(vector[row_index, 0] for row_index in range(vector.rows))
                    for vector in basis
                ),
            )
            for eigenvalue, algebraic_multiplicity, basis in eigenvector_data
        )
        eigenvalues = tuple(
            (eigenspace.eigenvalue, eigenspace.algebraic_multiplicity)
            for eigenspace in eigenspaces
        )
    except Exception:  # noqa: BLE001 - 符号算法可能因表达式规模或内部限制失败
        return EigenvalueSummary(
            is_square=True,
            characteristic_polynomial=None,
            eigenvalues=(),
            message=EIGENVALUE_UNAVAILABLE_MESSAGE,
        )

    return EigenvalueSummary(
        is_square=True,
        characteristic_polynomial=characteristic_polynomial,
        eigenvalues=eigenvalues,
        eigenspaces=eigenspaces,
    )
