import pytest
import sympy as sp

from matrix_rank.gui import (
    DEFAULT_STEP_DELAY_MS,
    MAX_MATRIX_COLS,
    MAX_MATRIX_ROWS,
    MatrixGridParseError,
    STEP_SPEED_DELAYS,
    WELCOME_MESSAGE,
    get_dimension_validation_error,
    get_step_delay_ms,
    parse_matrix_grid_values,
)


def test_dimension_validation_accepts_supported_size():
    assert get_dimension_validation_error(MAX_MATRIX_ROWS, MAX_MATRIX_COLS) is None


def test_dimension_validation_rejects_non_positive_size():
    assert get_dimension_validation_error(0, 3) == "行数和列数都必须大于 0。"


def test_dimension_validation_rejects_size_above_limit():
    error = get_dimension_validation_error(MAX_MATRIX_ROWS + 1, 2)

    assert error is not None
    assert "最多支持" in error


def test_welcome_message_describes_current_matrix_analysis_features():
    assert "矩阵分析助手" in WELCOME_MESSAGE
    assert "特征多项式" in WELCOME_MESSAGE
    assert "特征值" in WELCOME_MESSAGE
    assert "详细模式" in WELCOME_MESSAGE
    assert "简洁模式" in WELCOME_MESSAGE


def test_parse_matrix_grid_values_parses_supported_formats():
    parsed = parse_matrix_grid_values([["1", "1/2"], ["3e-2", "-4"]])

    assert parsed == [
        [sp.Rational(1), sp.Rational(1, 2)],
        [sp.Rational(3, 100), sp.Rational(-4)],
    ]


def test_parse_matrix_grid_values_reports_error_cell():
    with pytest.raises(MatrixGridParseError) as error:
        parse_matrix_grid_values([["1", "2"], ["3", "not-a-number"]])

    assert error.value.row_index == 1
    assert error.value.col_index == 1


def test_parse_matrix_grid_values_rejects_ragged_grid():
    with pytest.raises(ValueError, match="元素数量必须一致"):
        parse_matrix_grid_values([["1", "2"], ["3"]])


def test_parse_matrix_grid_values_reports_empty_row():
    with pytest.raises(ValueError, match="第 1 行不能为空"):
        parse_matrix_grid_values([[]])


def test_parse_matrix_grid_values_reports_later_empty_row():
    with pytest.raises(ValueError, match="第 2 行不能为空"):
        parse_matrix_grid_values([["1"], []])


def test_default_step_delay_is_non_negative():
    assert DEFAULT_STEP_DELAY_MS >= 0


def test_step_speed_options_have_distinct_delays():
    assert get_step_delay_ms("快速") < get_step_delay_ms("正常")
    assert get_step_delay_ms("正常") < get_step_delay_ms("慢速")
    assert set(STEP_SPEED_DELAYS) == {"快速", "正常", "慢速"}


def test_unknown_step_speed_is_rejected():
    with pytest.raises(ValueError, match="未知"):
        get_step_delay_ms("极速")
