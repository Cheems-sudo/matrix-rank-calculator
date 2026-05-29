from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.workflow import calculate_rank_with_selected_method


def test_concise_output_mode_prints_key_summary(capsys):
    calculator = MatrixRankCalculator([[1, 2], [2, 4]])

    calculate_rank_with_selected_method("1", calculator, output_mode="concise")

    output = capsys.readouterr().out
    assert "简洁模式结果" in output
    assert "矩阵规模：2 × 2" in output
    assert "所选方法：高斯消元法" in output
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
