"""输入解析工具"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import sympy as sp


MAX_NUMERIC_INPUT_LENGTH = 256
MAX_ABSOLUTE_DECIMAL_EXPONENT = 10_000


def parse_decimal_or_scientific(raw_value: str) -> sp.Rational:
    """把整数、小数或科学计数法字符串精确转换为 Rational。

    Decimal 可以精确理解 1e12、1e-12、0.5 这类十进制写法；
    再通过 as_integer_ratio 转成分子和分母，避免先变成 float 造成误差。
    """
    stripped_value = raw_value.strip()
    if len(stripped_value) > MAX_NUMERIC_INPUT_LENGTH:
        raise ValueError(
            f"单个数值最多允许 {MAX_NUMERIC_INPUT_LENGTH} 个字符。"
        )

    try:
        decimal_value = Decimal(stripped_value)
    except InvalidOperation as exc:
        raise ValueError("不是合法的十进制数或科学计数法。") from exc

    if not decimal_value.is_finite():
        raise ValueError("矩阵元素不能是 NaN 或无穷大。")

    if decimal_value != 0 and abs(decimal_value.adjusted()) > MAX_ABSOLUTE_DECIMAL_EXPONENT:
        raise ValueError(
            "数值数量级过大；十进制指数的绝对值不能超过 "
            f"{MAX_ABSOLUTE_DECIMAL_EXPONENT}。"
        )

    numerator, denominator = decimal_value.as_integer_ratio()
    return sp.Rational(numerator, denominator)


def parse_matrix_element(raw_value: str) -> sp.Rational:
    """解析单个矩阵元素，支持整数、小数、分数和科学计数法输入。

    支持示例：
    - 整数：2、-3
    - 小数：0.5、-1.25
    - 分数：3/4、-2/5
    - 科学计数法：1e12、1e-12、-3.5e6
    """
    stripped_value = raw_value.strip()
    if not stripped_value:
        raise ValueError("矩阵元素不能为空。")

    if stripped_value.count("/") == 1:
        numerator_text, denominator_text = stripped_value.split("/", 1)
        numerator = parse_decimal_or_scientific(numerator_text.strip())
        denominator = parse_decimal_or_scientific(denominator_text.strip())
        if denominator == 0:
            raise ValueError("分母不能为 0。")
        return sp.Rational(numerator / denominator)

    if "/" in stripped_value:
        raise ValueError("分数只能包含一个 /。")

    return parse_decimal_or_scientific(stripped_value)
