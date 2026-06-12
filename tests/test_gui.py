from matrix_rank.gui import (
    MAX_MATRIX_COLS,
    MAX_MATRIX_ROWS,
    get_dimension_validation_error,
)


def test_dimension_validation_accepts_supported_size():
    assert get_dimension_validation_error(MAX_MATRIX_ROWS, MAX_MATRIX_COLS) is None


def test_dimension_validation_rejects_non_positive_size():
    assert get_dimension_validation_error(0, 3) == "行数和列数都必须大于 0。"


def test_dimension_validation_rejects_size_above_limit():
    error = get_dimension_validation_error(MAX_MATRIX_ROWS + 1, 2)

    assert error is not None
    assert "最多支持" in error
