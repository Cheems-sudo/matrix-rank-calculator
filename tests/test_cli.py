import io
import json

import pytest

from matrix_rank.cli import main, parse_matrix_rows
from matrix_rank.version import __version__


def test_parse_matrix_rows_accepts_spaces_and_commas():
    assert parse_matrix_rows(["1 2", "3,4"]) == [["1", "2"], ["3", "4"]]


def test_parse_matrix_rows_rejects_inconsistent_width():
    with pytest.raises(ValueError, match="元素数量必须一致"):
        parse_matrix_rows(["1 2", "3"])


def test_cli_prints_concise_result_from_rows(capsys):
    exit_code = main(
        [
            "--row",
            "1 2",
            "--row",
            "2 4",
            "--method",
            "gaussian",
            "--mode",
            "concise",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "精确秩 rank = 1" in output


def test_cli_reads_matrix_from_stdin(monkeypatch, capsys):
    stdin = io.StringIO("1,0\n0,1\n")
    monkeypatch.setattr("sys.stdin", stdin)

    exit_code = main(["--mode", "concise"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "精确秩 rank = 2" in output


def test_cli_reads_matrix_from_file(tmp_path, capsys):
    matrix_file = tmp_path / "matrix.csv"
    matrix_file.write_text("1,2\n2,4\n", encoding="utf-8")

    exit_code = main(["--file", str(matrix_file)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "精确秩 rank = 1" in output


def test_cli_writes_result_to_file(tmp_path, capsys):
    output_file = tmp_path / "result.txt"

    exit_code = main(
        [
            "--row",
            "1 0",
            "--row",
            "0 1",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out == ""
    assert "精确秩 rank = 2" in output_file.read_text(encoding="utf-8")


def test_cli_outputs_structured_json(capsys):
    exit_code = main(
        [
            "--row",
            "1 2",
            "--row",
            "2 4",
            "--format",
            "json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["version"] == __version__
    assert result["requested_method"] == "gaussian"
    assert result["exact_algorithm"] == "sympy_builtin"
    assert result["shape"] == [2, 2]
    assert result["rank"]["exact"] == 1
    assert result["properties"]["determinant"] == "0"
    assert isinstance(result["eigen"]["values"], list)


def test_cli_version(capsys):
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])

    assert capsys.readouterr().out.strip() == f"matrix-rank {__version__}"


def test_cli_rejects_rows_and_file_together(tmp_path):
    matrix_file = tmp_path / "matrix.txt"
    matrix_file.write_text("1\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="2"):
        main(["--row", "1", "--file", str(matrix_file)])
