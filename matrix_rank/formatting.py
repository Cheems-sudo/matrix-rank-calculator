"""计算结果的文本格式化工具。"""

from __future__ import annotations

from collections.abc import Callable
from functools import cache
from typing import TypeVar

import sympy as sp


ValueT = TypeVar("ValueT")


def format_exact_value(value: object) -> str:
    """安全格式化精确值；超长整数改用科学计数法摘要。"""
    try:
        return str(value)
    except ValueError:
        approximate_value = sp.N(value, 6)
        return f"{approximate_value}（精确值过长，使用近似科学计数法显示）"


def format_aligned_matrix(
    rows: int,
    cols: int,
    get_value: Callable[[int, int], ValueT],
    format_value: Callable[[ValueT], str],
) -> str:
    """按列宽对齐矩阵，并在单次格式化中缓存重复标量。"""
    if rows == 0 or cols == 0:
        return "[]"

    cache: dict[object, str] = {}

    def format_cached(value: ValueT) -> str:
        try:
            cached = cache.get(value)
        except TypeError:
            return format_value(value)
        if cached is not None:
            return cached

        formatted = format_value(value)
        try:
            cache[value] = formatted
        except TypeError:
            pass
        return formatted

    formatted_rows = [
        [format_cached(get_value(row_index, col_index)) for col_index in range(cols)]
        for row_index in range(rows)
    ]
    column_widths = [
        max(len(formatted_rows[row_index][col_index]) for row_index in range(rows))
        for col_index in range(cols)
    ]
    aligned_rows = [
        "[ "
        + "  ".join(
            value.rjust(column_widths[col_index])
            for col_index, value in enumerate(row)
        )
        + " ]"
        for row in formatted_rows
    ]
    return "[\n  " + "\n  ".join(aligned_rows) + "\n]"


def format_eigen_expression(value: sp.Expr) -> str:
    """使用常见数学记号格式化特征值相关表达式。"""
    lambda_symbol = sp.Symbol("lambda")
    display_value = value.xreplace({lambda_symbol: sp.Symbol("λ")})
    return format_exact_value(display_value).replace("**", "^")


def _to_superscript(number: int) -> str:
    """把非负整数转换为 Unicode 上标。"""
    translation = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(number).translate(translation)


@cache
def supports_pretty_math_symbols(encoding: str | None) -> bool:
    """判断指定编码能否安全显示 Unicode 数学符号。"""
    if encoding is None:
        return True

    try:
        "λ²³ − ≈".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def format_characteristic_polynomial(
    polynomial: sp.Expr,
    encoding: str | None = "utf-8",
) -> str:
    """把单变量特征多项式格式化为紧凑的数学排版。"""
    lambda_symbol = sp.Symbol("lambda")
    poly = sp.Poly(polynomial, lambda_symbol)
    formatted_terms: list[tuple[bool, str]] = []
    use_pretty_symbols = supports_pretty_math_symbols(encoding)

    for (degree,), coefficient in poly.terms():
        is_negative = coefficient.could_extract_minus_sign()
        absolute_coefficient = -coefficient if is_negative else coefficient

        if degree == 0:
            term = format_exact_value(absolute_coefficient)
        else:
            variable_name = "λ" if use_pretty_symbols else "lambda"
            if degree == 1:
                variable = variable_name
            elif use_pretty_symbols:
                variable = f"{variable_name}{_to_superscript(degree)}"
            else:
                variable = f"{variable_name}^{degree}"
            if absolute_coefficient == 1:
                term = variable
            else:
                separator = "" if use_pretty_symbols else "*"
                term = f"{format_exact_value(absolute_coefficient)}{separator}{variable}"

        formatted_terms.append((is_negative, term))

    if not formatted_terms:
        return "0"

    first_is_negative, first_term = formatted_terms[0]
    minus_sign = "−" if use_pretty_symbols else "-"
    result = f"{minus_sign}{first_term}" if first_is_negative else first_term
    for is_negative, term in formatted_terms[1:]:
        result += (f" {minus_sign} " if is_negative else " + ") + term
    return result


def format_eigenvalue_for_display(
    eigenvalue: sp.Expr,
    encoding: str | None = "utf-8",
) -> tuple[str, bool]:
    """优先显示简洁精确值，复杂根式则显示清晰的数值近似。"""
    exact_text = format_eigen_expression(eigenvalue)
    if len(exact_text) <= 72 and sp.count_ops(eigenvalue) <= 12:
        return exact_text, False

    numeric_value = sp.N(eigenvalue, 8)
    real_part = float(sp.re(numeric_value))
    imaginary_part = float(sp.im(numeric_value))

    if abs(imaginary_part) <= 1e-10:
        return f"{real_part:.8g}", True

    minus_sign = "−" if supports_pretty_math_symbols(encoding) else "-"
    sign = "+" if imaginary_part >= 0 else minus_sign
    return f"{real_part:.8g} {sign} {abs(imaginary_part):.8g}i", True
