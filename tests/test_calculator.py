import numpy as np
import pytest
import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator, SVDUnavailableError


def test_zero_matrix_rank_is_zero():
    calculator = MatrixRankCalculator([[0, 0, 0], [0, 0, 0]])

    assert calculator.rank_by_gaussian_elimination_silent() == 0


@pytest.mark.parametrize("size", [1, 2, 4])
def test_identity_matrix_rank_is_n(size):
    calculator = MatrixRankCalculator(sp.eye(size).tolist())

    assert calculator.rank_by_gaussian_elimination_silent() == size


def test_row_dependent_matrix_rank_is_correct():
    matrix = [
        [1, 2, 3],
        [2, 4, 6],
        [1, 1, 1],
    ]
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_gaussian_elimination_silent() == 2


def test_rectangular_matrix_rank_is_correct():
    matrix = [
        [1, 2, 3, 4],
        [2, 4, 6, 8],
        [0, 1, 0, 1],
    ]
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_gaussian_elimination_silent() == 2


def test_fraction_matrix_rank_is_correct():
    matrix = [
        ["1/2", "1/3"],
        ["2/3", "4/9"],
    ]
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_gaussian_elimination_silent() == 1


@pytest.mark.parametrize(
    "matrix",
    [
        [[0, 0], [0, 0]],
        [[1, 2], [3, 4]],
        [[1, 2, 3], [2, 4, 6], [3, 6, 9]],
        [["1/2", "0", "3/4"], ["1", "2", "5/2"]],
    ],
)
def test_gaussian_silent_rank_matches_sympy(matrix):
    calculator = MatrixRankCalculator(matrix)
    expected_rank = sp.Matrix(
        [[sp.Rational(str(value)) for value in row] for row in matrix]
    ).rank()

    assert calculator.rank_by_gaussian_elimination_silent() == expected_rank


@pytest.mark.parametrize(
    ("matrix", "expected_rank"),
    [
        ([[0, 0], [0, 0]], 0),
        ([[1, 0], [0, 1]], 2),
        ([[1, 2], [2, 4]], 1),
        ([[1, 2, 3], [4, 5, 6]], 2),
    ],
)
def test_svd_numeric_rank_for_common_matrices(matrix, expected_rank):
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_svd_silent() == expected_rank


def test_svd_numeric_rank_matches_numpy_for_full_rank_matrix():
    matrix = np.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_svd_silent() == np.linalg.matrix_rank(matrix)


@pytest.mark.parametrize("value", ["1e10000", "1e-10000"])
def test_svd_rejects_values_outside_float_range_but_exact_rank_remains_available(value):
    calculator = MatrixRankCalculator([[value]])

    assert calculator.rank_by_gaussian_elimination_silent() == 1
    with pytest.raises(SVDUnavailableError, match="无法进行 SVD"):
        calculator.rank_by_svd_silent()


def test_svd_convergence_failure_uses_unavailable_error(monkeypatch):
    calculator = MatrixRankCalculator([[1]])

    def fail_svd(*args, **kwargs):
        raise np.linalg.LinAlgError("did not converge")

    monkeypatch.setattr(np.linalg, "svd", fail_svd)

    with pytest.raises(SVDUnavailableError, match="未收敛"):
        calculator.rank_by_svd_silent()
