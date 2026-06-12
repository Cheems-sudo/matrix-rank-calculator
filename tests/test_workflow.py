import pytest

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.workflow import (
    calculate_rank_with_selected_method,
    get_matrix_properties_summary,
)


def test_concise_output_mode_prints_key_summary(capsys):
    calculator = MatrixRankCalculator([[1, 2], [2, 4]])

    calculate_rank_with_selected_method("1", calculator, output_mode="concise")

    output = capsys.readouterr().out
    assert "简洁模式结果" in output
    assert "矩阵规模：2 × 2" in output
    assert "所选方法：高斯消元法" in output
    assert "矩阵基础信息" in output
    assert "特征值信息" in output
    assert "特征多项式：" in output
    assert "精确秩 rank = 1" in output
    assert "SVD 数值秩参考 rank = 1" in output


def test_concise_output_mode_keeps_svd_as_reference(capsys):
    calculator = MatrixRankCalculator([[1, 0], [0, 1]])

    calculate_rank_with_selected_method("3", calculator, output_mode="concise")

    output = capsys.readouterr().out
    assert "所选方法：SVD 法" in output
    assert "SVD 是数值秩方法" in output
    assert "精确秩 rank = 2" in output


def test_detailed_output_mode_remains_default(capsys):
    calculator = MatrixRankCalculator([[1, 0], [0, 1]])

    calculate_rank_with_selected_method("1", calculator)

    output = capsys.readouterr().out
    assert "高斯消元法计算结果：rank = 2" in output
    assert "结果可信度复核" in output
    assert "矩阵基础信息" in output
    assert "特征多项式 det(lambdaI - A)" in output
    assert "解 det(lambdaI - A) = 0 得到特征值" in output
    assert "特征子空间基" in output
    assert "几何重数" in output


def test_rectangular_matrix_prints_no_eigenvalue_message(capsys):
    calculator = MatrixRankCalculator([[1, 2, 3], [4, 5, 6]])

    calculate_rank_with_selected_method("1", calculator, output_mode="concise")

    output = capsys.readouterr().out
    assert "特征值信息" in output
    assert "非方阵没有特征值。" in output


def test_matrix_properties_summary_for_invertible_square_matrix():
    calculator = MatrixRankCalculator([[1, 0], [0, 1]])

    summary = get_matrix_properties_summary(calculator)

    assert summary == {
        "shape": "2 × 2",
        "is_square": "是",
        "exact_rank": "2",
        "is_full_rank": "是",
        "determinant": "1",
        "is_invertible": "是",
    }


def test_matrix_properties_summary_for_singular_square_matrix():
    calculator = MatrixRankCalculator([[1, 2], [2, 4]])

    summary = get_matrix_properties_summary(calculator)

    assert summary == {
        "shape": "2 × 2",
        "is_square": "是",
        "exact_rank": "1",
        "is_full_rank": "否",
        "determinant": "0",
        "is_invertible": "否",
    }


def test_matrix_properties_summary_for_full_rank_rectangular_matrix():
    calculator = MatrixRankCalculator([[1, 0, 0], [0, 1, 0]])

    summary = get_matrix_properties_summary(calculator)

    assert summary == {
        "shape": "2 × 3",
        "is_square": "否",
        "exact_rank": "2",
        "is_full_rank": "是",
        "determinant": "不适用，非方阵没有行列式",
        "is_invertible": "不适用，非方阵没有逆矩阵",
    }


def test_matrix_properties_summary_for_zero_matrix():
    calculator = MatrixRankCalculator([[0, 0], [0, 0]])

    summary = get_matrix_properties_summary(calculator)

    assert summary == {
        "shape": "2 × 2",
        "is_square": "是",
        "exact_rank": "0",
        "is_full_rank": "否",
        "determinant": "0",
        "is_invertible": "否",
    }


@pytest.mark.parametrize("output_mode", ["concise", "detailed"])
def test_unknown_method_is_rejected_in_all_output_modes(output_mode):
    calculator = MatrixRankCalculator([[1]])

    with pytest.raises(ValueError, match="未知的计算方法"):
        calculate_rank_with_selected_method("unknown", calculator, output_mode=output_mode)


def test_concise_output_keeps_exact_result_when_svd_is_unavailable(capsys):
    calculator = MatrixRankCalculator([["1e10000"]])

    calculate_rank_with_selected_method("3", calculator, output_mode="concise")

    output = capsys.readouterr().out
    assert "精确秩 rank = 1" in output
    assert "SVD 数值秩参考不可用" in output
    assert "精确秩结论仍然有效" in output


def test_detailed_svd_falls_back_to_exact_rank_when_svd_is_unavailable(capsys):
    calculator = MatrixRankCalculator([["1e-10000"]])

    calculate_rank_with_selected_method("3", calculator)

    output = capsys.readouterr().out
    assert "SVD 数值计算不可用" in output
    assert "下面改用高斯消元法" in output
    assert "高斯消元法计算结果：rank = 1" in output
