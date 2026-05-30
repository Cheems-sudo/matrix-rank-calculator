"""计算流程和结果复核汇总"""

from __future__ import annotations

import sympy as sp

from matrix_rank.calculator import MatrixRankCalculator
from matrix_rank.eigen import EigenvalueSummary, get_eigenvalue_summary as build_eigenvalue_summary


METHOD_NAMES = {
    "1": "高斯消元法",
    "2": "行列式法",
    "3": "SVD 法",
}


def calculate_rank_with_selected_method(
    method_choice: str,
    calculator: MatrixRankCalculator,
    output_mode: str = "detailed",
) -> None:
    """根据输出模式组织矩阵秩计算流程。"""
    if output_mode == "concise":
        print_concise_rank_summary(method_choice, calculator)
        return

    if output_mode != "detailed":
        raise ValueError("output_mode 必须是 detailed 或 concise。")

    print_detailed_rank_process(method_choice, calculator)


def print_detailed_rank_process(method_choice: str, calculator: MatrixRankCalculator) -> None:
    """显示所选方法的计算过程，并在结尾汇总至少两种方法的秩。"""

    rows, cols = calculator.matrix.shape
    max_dimension = max(rows, cols)
    effective_method_choice = method_choice

    if method_choice == "2" and max_dimension > 4:
        print(
            "所选行列式法需要枚举大量子行列式；"
            f"当前 n = max({rows}, {cols}) = {max_dimension} > 4，"
            "为避免大矩阵计算过慢，跳过行列式法详细过程。"
        )
        print("下面改用高斯消元法展示详细计算过程，并在结尾用 SVD 进行复核。")
        effective_method_choice = "1"

    if effective_method_choice == "1":
        rank = calculator.rank_by_gaussian_elimination()
        print(f"高斯消元法计算结果：rank = {rank}")
    elif effective_method_choice == "2":
        rank = calculator.rank_by_determinants()
        print(f"行列式法计算结果：rank = {rank}")
    else:
        rank = calculator.rank_by_svd()
        print(f"SVD 法数值秩计算结果：rank = {rank}")

    print_rank_verification_summary(
        calculator,
        selected_method_choice=effective_method_choice,
        selected_rank=rank,
        original_method_choice=method_choice,
    )


def print_concise_rank_summary(method_choice: str, calculator: MatrixRankCalculator) -> None:
    """只输出关键结论，不展示中间消元、子式枚举或 SVD 分解过程。"""
    if method_choice not in METHOD_NAMES:
        raise ValueError("未知的计算方法。")

    rows, cols = calculator.matrix.shape
    max_dimension = max(rows, cols)
    exact_rank = calculator.rank_by_gaussian_elimination_silent()
    svd_rank = calculator.rank_by_svd_silent()

    print("简洁模式结果")
    print("-" * len("简洁模式结果"))
    print(f"矩阵规模：{rows} × {cols}")
    print(f"所选方法：{METHOD_NAMES[method_choice]}")
    print("")
    print_matrix_properties_summary(calculator, exact_rank=exact_rank)
    print("")
    print_eigenvalue_summary(calculator, output_mode="concise")

    if method_choice == "2" and max_dimension > 4:
        print("")
        print("说明：行列式法在当前矩阵规模下会枚举大量子行列式；简洁模式中已使用高斯消元法给出精确秩。")
    elif method_choice == "3":
        print("")
        print("说明：SVD 是数值秩方法；简洁模式仍会补充精确秩作为最终数学结论。")

    print("")
    print(f"精确秩 rank = {exact_rank}")
    print(f"SVD 数值秩参考 rank = {svd_rank}")
    print("")

    if svd_rank == exact_rank:
        print("SVD 参考结论：数值秩与精确秩一致。")
    else:
        print("SVD 参考结论：数值秩（SVD）与精确秩不一致；以精确秩为准，SVD 仅供参考。")


def get_matrix_properties_summary(
    calculator: MatrixRankCalculator,
    exact_rank: int | None = None,
) -> dict[str, str]:
    """返回矩阵规模、秩、满秩、行列式和可逆性等基础信息。"""
    rows, cols = calculator.matrix.shape
    resolved_exact_rank = (
        calculator.rank_by_gaussian_elimination_silent()
        if exact_rank is None
        else exact_rank
    )
    is_square = rows == cols
    is_full_rank = resolved_exact_rank == min(rows, cols)

    summary = {
        "shape": f"{rows} × {cols}",
        "is_square": "是" if is_square else "否",
        "exact_rank": str(resolved_exact_rank),
        "is_full_rank": "是" if is_full_rank else "否",
        "determinant": "不适用，非方阵没有行列式",
        "is_invertible": "不适用，非方阵没有逆矩阵",
    }

    if is_square:
        determinant = sp.simplify(calculator.exact_matrix.det())
        summary["determinant"] = str(determinant)
        summary["is_invertible"] = "是" if determinant != 0 else "否"

    return summary


def print_matrix_properties_summary(
    calculator: MatrixRankCalculator,
    exact_rank: int | None = None,
) -> None:
    """打印矩阵基础信息总结。"""
    summary = get_matrix_properties_summary(calculator, exact_rank=exact_rank)

    print("矩阵基础信息")
    print("-" * len("矩阵基础信息"))
    print(f"矩阵规模：{summary['shape']}")
    print(f"是否方阵：{summary['is_square']}")
    print(f"精确秩：{summary['exact_rank']}")
    print(f"是否满秩：{summary['is_full_rank']}")
    print(f"行列式：{summary['determinant']}")
    print(f"是否可逆：{summary['is_invertible']}")


def get_eigenvalue_summary(calculator: MatrixRankCalculator) -> EigenvalueSummary:
    """返回矩阵的精确特征值信息；非方阵返回说明信息。"""
    return build_eigenvalue_summary(calculator.exact_matrix)


def print_eigenvalue_summary(
    calculator: MatrixRankCalculator,
    output_mode: str = "detailed",
) -> None:
    """打印特征多项式和特征值信息。"""
    summary = get_eigenvalue_summary(calculator)

    print("特征值信息")
    print("-" * len("特征值信息"))

    if not summary.is_square:
        print(summary.message)
        return

    if output_mode == "detailed":
        print("说明：特征多项式按 det(lambdaI - A) 计算。")
        print(f"特征多项式 det(lambdaI - A)：{summary.characteristic_polynomial}")
        print("解 det(lambdaI - A) = 0 得到特征值：")
    elif output_mode == "concise":
        print(f"特征多项式：{summary.characteristic_polynomial}")
        print("特征值：")
    else:
        raise ValueError("output_mode 必须是 detailed 或 concise。")

    for eigenvalue, algebraic_multiplicity in summary.eigenvalues:
        print(f"- {eigenvalue}，代数重数 {algebraic_multiplicity}")


def print_rank_verification_summary(
    calculator: MatrixRankCalculator,
    selected_method_choice: str,
    selected_rank: int,
    original_method_choice: str | None = None,
) -> None:
    """在详细过程后补充精确秩结论和 SVD 数值秩参考。"""
    method_names = {
        "1": "高斯消元法（精确秩）",
        "2": "行列式法（精确秩）",
        "3": "数值秩（SVD，仅供参考）",
    }
    rows, cols = calculator.matrix.shape
    max_dimension = max(rows, cols)
    exact_results: dict[str, int] = {}
    svd_rank: int | None = None

    print("\n")

    print("结果可信度复核")
    print("-" * len("结果可信度复核"))
    print(f"矩阵规模为 {rows} × {cols}")
    print(f"n = max({rows}, {cols}) = {max_dimension}")
    print("")
    print("说明：高斯消元法和行列式法计算的是精确秩；SVD 计算的是数值秩，只作为工程参考。")
    print("")
    if original_method_choice == "2" and selected_method_choice != "2":
        print(f"用户原本选择行列式法，但 n > 4，\n因此已按规则跳过行列式法并改用高斯消元法展示过程。")
        print("")
    exact_method_choices = ["1"]
    if max_dimension <= 4:
        exact_method_choices.append("2")
        print("因为 n ≤ 4，本次会计算两种精确秩方法（高斯消元法、行列式法）和 SVD 数值秩参考。")
        print("")
    else:
        print("因为 n > 4，为避免子行列式枚举过慢，本次跳过行列式法；精确秩由高斯消元法给出，SVD 仅作数值参考。")
        print("")

    for method_choice in exact_method_choices:
        if method_choice == selected_method_choice:
            exact_results[method_choice] = selected_rank
        elif method_choice == "1":
            exact_results[method_choice] = calculator.rank_by_gaussian_elimination_silent()
        else:
            exact_results[method_choice] = calculator.rank_by_determinants_silent()

    if selected_method_choice == "3":
        svd_rank = selected_rank
    else:
        svd_rank = calculator.rank_by_svd_silent()

    for method_choice in ["1", "2"]:
        method_name = method_names[method_choice]
        if method_choice in exact_results:
            suffix = "（已展示详细过程）" if method_choice == selected_method_choice else "（静默复核，不展示过程）"
            print(f"{method_name}{suffix}：rank = {exact_results[method_choice]}")
            print("")
        elif method_choice == "2":
            print(f"{method_name}：已跳过（n = {max_dimension} > 4，避免大矩阵枚举子行列式）。")
            print("")

    svd_suffix = "（已展示详细过程，但仍仅供参考）" if selected_method_choice == "3" else "（静默复核，不展示过程）"
    print(f"{method_names['3']}{svd_suffix}：rank = {svd_rank}")
    print("")

    exact_rank_values = list(exact_results.values())
    if len(set(exact_rank_values)) == 1:
        exact_rank = exact_rank_values[0]
        print(f"精确秩结论：rank = {exact_rank}。")
        print("")
    else:
        exact_rank = exact_results["1"]
        print("精确秩复核警告：高斯消元法和行列式法结果不一致，请优先检查输入和符号计算过程。")
        print("")
        print(f"当前暂以高斯消元法得到的精确秩 rank = {exact_rank} 作为结论。")
        print("")

    if svd_rank == exact_rank:
        print("SVD 参考结论：数值秩与精确秩一致。")
        print("")
    else:
        print(
            "SVD 参考结论：数值秩（SVD）与精确秩不一致；"
            "以精确秩为准，SVD 仅供参考。"
        )
        print("")
        print("可能原因：矩阵病态、元素尺度差很大，或存在很小但非零的精确值。")
        print("")

    print_matrix_properties_summary(calculator, exact_rank=exact_rank)
    print("")
    print_eigenvalue_summary(calculator, output_mode="detailed")
    print("")
