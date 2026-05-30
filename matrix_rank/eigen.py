"""Eigenvalue helpers for exact symbolic matrix calculations."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp


NON_SQUARE_EIGENVALUE_MESSAGE = "非方阵没有特征值。"


@dataclass(frozen=True)
class EigenvalueSummary:
    """Exact characteristic polynomial and eigenvalues for a matrix."""

    is_square: bool
    characteristic_polynomial: sp.Expr | None
    eigenvalues: tuple[tuple[sp.Expr, int], ...]
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

    lambda_symbol = sp.Symbol("lambda")
    characteristic_polynomial = sp.expand(matrix.charpoly(lambda_symbol).as_expr())
    eigenvalues = tuple(
        sorted(
            matrix.eigenvals().items(),
            key=lambda item: sp.default_sort_key(item[0]),
        )
    )

    return EigenvalueSummary(
        is_square=True,
        characteristic_polynomial=characteristic_polynomial,
        eigenvalues=eigenvalues,
    )
