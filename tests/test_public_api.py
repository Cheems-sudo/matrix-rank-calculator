import matrix_rank
from pathlib import Path
import tomllib
from matrix_rank.calculator import MatrixRankCalculator, SVDUnavailableError
from matrix_rank.eigen import EigenspaceSummary, EigenvalueSummary


def test_package_exports_core_public_api():
    assert matrix_rank.__version__ == "1.2.0"
    assert matrix_rank.MatrixRankCalculator is MatrixRankCalculator
    assert matrix_rank.SVDUnavailableError is SVDUnavailableError
    assert matrix_rank.EigenvalueSummary is EigenvalueSummary
    assert matrix_rank.EigenspaceSummary is EigenspaceSummary
    assert callable(matrix_rank.get_eigenvalue_summary)
    assert callable(matrix_rank.cli_main)
    assert callable(matrix_rank.gui_main)


def test_gui_class_remains_available_as_lazy_export():
    from matrix_rank.gui import MatrixRankRobotApp

    assert matrix_rank.MatrixRankRobotApp is MatrixRankRobotApp


def test_public_version_matches_project_metadata():
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    project_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert matrix_rank.__version__ == project_data["project"]["version"]
