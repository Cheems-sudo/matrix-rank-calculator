import numpy as np
import pytest
import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator, SVDUnavailableError


def test_zero_matrix_rank_is_zero():
    calculator = MatrixRankCalculator([[0, 0, 0], [0, 0, 0]])

    assert calculator.rank_by_sympy_builtin() == 0


@pytest.mark.parametrize("size", [1, 2, 4])
def test_identity_matrix_rank_is_n(size):
    calculator = MatrixRankCalculator(sp.eye(size).tolist())

    assert calculator.rank_by_sympy_builtin() == size


def test_row_dependent_matrix_rank_is_correct():
    matrix = [
        [1, 2, 3],
        [2, 4, 6],
        [1, 1, 1],
    ]
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_sympy_builtin() == 2


def test_rectangular_matrix_rank_is_correct():
    matrix = [
        [1, 2, 3, 4],
        [2, 4, 6, 8],
        [0, 1, 0, 1],
    ]
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_sympy_builtin() == 2


def test_fraction_matrix_rank_is_correct():
    matrix = [
        ["1/2", "1/3"],
        ["2/3", "4/9"],
    ]
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_sympy_builtin() == 1


@pytest.mark.parametrize("matrix", [[], [[]]])
def test_calculator_rejects_empty_matrix_shapes(matrix):
    with pytest.raises(ValueError, match="不能为空|至少包含一个元素"):
        MatrixRankCalculator(matrix)


def test_calculator_rejects_ragged_matrix():
    with pytest.raises(ValueError, match="元素数量必须一致"):
        MatrixRankCalculator([[1, 2], [3]])


def test_calculator_rejects_string_as_matrix_row():
    with pytest.raises(ValueError, match="不能是字符串"):
        MatrixRankCalculator(["12", "34"])


def test_calculator_reports_sympy_matrix_construction_failure(monkeypatch):
    def fail_matrix(_rows):
        raise ValueError("internal construction failure")

    monkeypatch.setattr(sp, "Matrix", fail_matrix)

    with pytest.raises(ValueError, match="无法构建 SymPy 矩阵"):
        MatrixRankCalculator([[1]])


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

    assert calculator.rank_by_sympy_builtin() == expected_rank


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

    assert calculator.rank_by_svd_without_output() == expected_rank


def test_svd_numeric_rank_matches_numpy_for_full_rank_matrix():
    matrix = np.array([[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])
    calculator = MatrixRankCalculator(matrix)

    assert calculator.rank_by_svd_without_output() == np.linalg.matrix_rank(matrix)


@pytest.mark.parametrize("value", ["1e10000", "1e-10000"])
def test_svd_rejects_values_outside_float_range_but_exact_rank_remains_available(value):
    calculator = MatrixRankCalculator([[value]])

    assert calculator.rank_by_sympy_builtin() == 1
    with pytest.raises(SVDUnavailableError, match="无法进行 SVD"):
        calculator.rank_by_svd_without_output()


def test_svd_convergence_failure_uses_unavailable_error(monkeypatch):
    calculator = MatrixRankCalculator([[1]])

    def fail_svd(*args, **kwargs):
        raise np.linalg.LinAlgError("did not converge")

    monkeypatch.setattr(np.linalg, "svd", fail_svd)

    with pytest.raises(SVDUnavailableError, match="未收敛"):
        calculator.rank_by_svd_without_output()


def test_legacy_silent_rank_method_warns_and_uses_sympy():
    calculator = MatrixRankCalculator([[1, 2], [2, 4]])

    with pytest.warns(DeprecationWarning, match="rank_by_sympy_builtin"):
        rank = calculator.rank_by_gaussian_elimination_silent()

    assert rank == 1
