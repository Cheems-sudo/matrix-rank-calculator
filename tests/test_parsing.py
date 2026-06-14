import pytest
import sympy as sp

from matrix_rank.parsing import (
    MAX_ABSOLUTE_DECIMAL_EXPONENT,
    MAX_NUMERIC_INPUT_LENGTH,
    parse_matrix_element,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("3", sp.Rational(3)),
        ("0.125", sp.Rational(1, 8)),
        ("-7", sp.Rational(-7)),
        ("-2/5", sp.Rational(-2, 5)),
        ("1.2e3", sp.Rational(1200)),
        ("-3.5e-2", sp.Rational(-7, 200)),
    ],
)
def test_parse_matrix_element_supported_number_formats(raw_value, expected):
    assert parse_matrix_element(raw_value) == expected


def test_parse_matrix_element_rejects_zero_denominator():
    with pytest.raises(ValueError):
        parse_matrix_element("1/0")


@pytest.mark.parametrize("raw_value", ["NaN", "Infinity", "-Infinity"])
def test_parse_matrix_element_rejects_non_finite_values(raw_value):
    with pytest.raises(ValueError, match="NaN 或无穷大"):
        parse_matrix_element(raw_value)


def test_parse_matrix_element_rejects_excessively_long_literal():
    raw_value = "1" * (MAX_NUMERIC_INPUT_LENGTH + 1)

    with pytest.raises(ValueError, match="最多允许"):
        parse_matrix_element(raw_value)


def test_parse_matrix_element_rejects_excessive_decimal_exponent():
    raw_value = f"1e{MAX_ABSOLUTE_DECIMAL_EXPONENT + 1}"

    with pytest.raises(ValueError, match="指数的绝对值不能超过"):
        parse_matrix_element(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        f"1e{MAX_ABSOLUTE_DECIMAL_EXPONENT}",
        f"1e-{MAX_ABSOLUTE_DECIMAL_EXPONENT}",
    ],
)
def test_parse_matrix_element_accepts_supported_exponent_boundary(raw_value):
    assert parse_matrix_element(raw_value) != 0
