import pytest
import sympy as sp

from matrix_rank.parsing import parse_matrix_element


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
