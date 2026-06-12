import io

import pytest

from matrix_rank.cli import main, parse_matrix_rows


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
