import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.eigen import NON_SQUARE_EIGENVALUE_MESSAGE
from matrix_rank.workflow import get_eigenvalue_summary


def test_diagonal_matrix_eigenvalues_are_exact():
    calculator = MatrixRankCalculator([[1, 0], [0, 2]])

    summary = get_eigenvalue_summary(calculator)

    assert summary.is_square is True
    assert summary.characteristic_polynomial == sp.Symbol("lambda") ** 2 - 3 * sp.Symbol("lambda") + 2
    assert dict(summary.eigenvalues) == {sp.Integer(1): 1, sp.Integer(2): 1}


def test_identity_matrix_eigenvalue_has_algebraic_multiplicity_two():
    calculator = MatrixRankCalculator([[1, 0], [0, 1]])

    summary = get_eigenvalue_summary(calculator)

    assert summary.is_square is True
    assert dict(summary.eigenvalues) == {sp.Integer(1): 2}


def test_defective_matrix_reports_repeated_root_without_eigenvectors():
    calculator = MatrixRankCalculator([[1, 1], [0, 1]])

    summary = get_eigenvalue_summary(calculator)

    assert summary.is_square is True
    assert dict(summary.eigenvalues) == {sp.Integer(1): 2}


def test_rectangular_matrix_does_not_calculate_eigenvalues():
    calculator = MatrixRankCalculator([[1, 2, 3], [4, 5, 6]])

    summary = get_eigenvalue_summary(calculator)

    assert summary.is_square is False
    assert summary.characteristic_polynomial is None
    assert summary.eigenvalues == ()
    assert summary.message == NON_SQUARE_EIGENVALUE_MESSAGE
