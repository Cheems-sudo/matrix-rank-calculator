import sympy as sp

from matrix_rank.formatting import (
    format_aligned_matrix,
    format_characteristic_polynomial,
    supports_pretty_math_symbols,
)


def test_format_aligned_matrix_caches_repeated_values():
    calls = 0
    values = [[1, 1], [1, 2]]

    def format_value(value):
        nonlocal calls
        calls += 1
        return str(value)

    result = format_aligned_matrix(
        2,
        2,
        lambda row, col: values[row][col],
        format_value,
    )

    assert result == "[\n  [ 1  1 ]\n  [ 1  2 ]\n]"
    assert calls == 2


def test_pretty_math_symbol_check_is_cached_by_encoding():
    supports_pretty_math_symbols.cache_clear()

    assert supports_pretty_math_symbols("utf-8") is True
    assert supports_pretty_math_symbols("utf-8") is True
    assert supports_pretty_math_symbols.cache_info().hits == 1


def test_characteristic_polynomial_has_unicode_and_ascii_forms():
    lambda_symbol = sp.Symbol("lambda")
    polynomial = lambda_symbol**3 - 2 * lambda_symbol + 1

    assert (
        format_characteristic_polynomial(polynomial, "utf-8")
        == "λ³ − 2λ + 1"
    )
    assert (
        format_characteristic_polynomial(polynomial, "ascii")
        == "lambda^3 - 2*lambda + 1"
    )
